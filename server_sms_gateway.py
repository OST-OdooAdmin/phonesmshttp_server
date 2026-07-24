#!/usr/bin/env python3
import json
import sqlite3
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
import os
import subprocess

DB_FILE = "/root/sms_gateway.db"
LOG_FILE = "/var/log/sms_gateway_activity.log"
DEFAULT_RECIPIENT = "+6596780253"

def log_activity(text):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{now_str}] {text}\n"
    print(entry.strip())
    try:
        with open(LOG_FILE, "a") as f:
            f.write(entry)
    except Exception as e:
        print(f"Log write error: {e}")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sms_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT NOT NULL,
            message TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'queued',
            detail TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    purge_old_logs()

def purge_old_logs():
    """Purge records older than 3 months (90 days)"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM sms_queue WHERE datetime(created_at) < datetime('now', '-90 days')
        ''')
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        if deleted_count > 0:
            log_activity(f"🧹 Purged {deleted_count} log records older than 90 days (3 months).")
    except Exception as e:
        log_activity(f"Error purging old logs: {e}")

def add_sms_task(recipient, message):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO sms_queue (recipient, message, state, created_at)
        VALUES (?, ?, 'queued', ?)
    ''', (recipient, message, now_str))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    log_activity(f"✅ QUEUED TASK #{task_id} -> {recipient}: '{message}'")
    purge_old_logs()
    return task_id

def log_phone_dispatch(recipient, message, status="sent", detail=""):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_state = 'sent' if status == 'sent' or status == 'SUCCESS' else 'failed'
    cursor.execute('''
        INSERT INTO sms_queue (recipient, message, state, detail, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (recipient, message, new_state, detail, now_str))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    log_activity(f"📱 PHONE DIRECT DISPATCH Task #{task_id} -> {recipient}: '{message}' [{new_state.upper()}] ({detail})")
    purge_old_logs()
    return task_id

def trigger_server_startup_message():
    """Triggered on server boot / service start: queues default startup test message"""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    startup_msg = f"[SERVER STARTUP TRIGGER] Gateway Online at {now_str}"
    task_id = add_sms_task(DEFAULT_RECIPIENT, startup_msg)
    log_activity(f"🚀 SERVER STARTUP AUTO-TRIGGER -> Queued task #{task_id} for {DEFAULT_RECIPIENT}")

def get_pending_tasks():
    """Returns ONLY unpicked queued tasks (Once & Only Once pickup policy)"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, recipient, message FROM sms_queue WHERE state = 'queued' LIMIT 20
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    tasks = []
    for r in rows:
        tasks.append({
            "id": r[0],
            "to": r[1],
            "message": r[2]
        })
    if tasks:
        log_activity(f"📡 Delivered {len(tasks)} pending tasks to polling phone app.")
    return tasks

def get_all_server_logs():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT recipient, message, state, detail, created_at FROM sms_queue ORDER BY id DESC LIMIT 200
    ''')
    rows = cursor.fetchall()
    conn.close()

    logs = []
    for r in rows:
        status_str = "SUCCESS" if r[2] == 'sent' else ("FAILED: " + r[3] if r[2] == 'failed' else "QUEUED")
        words = len(r[1].split()) if r[1] else 0
        logs.append({
            "recipient": r[0],
            "message": r[1],
            "status": status_str,
            "timestamp": r[4],
            "wordCount": words
        })
    return logs

def update_task_status(task_id, status, detail=""):
    """Marks task as 'sent' so it is NEVER picked up again by the phone"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    new_state = 'sent' if status == 'sent' else 'failed'
    cursor.execute('''
        UPDATE sms_queue SET state = ?, detail = ? WHERE id = ?
    ''', (new_state, detail, task_id))
    conn.commit()
    conn.close()
    log_activity(f"📋 DISPATCH RECEIPT Task #{task_id} -> State: {new_state} ({detail})")

class SmsGatewayRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/api/sms/pending'):
            tasks = get_pending_tasks()
            self._set_headers(200)
            self.wfile.write(json.dumps({"pending": tasks}).encode('utf-8'))
        elif self.path.startswith('/api/sms/logs'):
            logs = get_all_server_logs()
            self._set_headers(200)
            self.wfile.write(json.dumps({"logs": logs}).encode('utf-8'))
        elif self.path.startswith('/api/sms/trigger-startup'):
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            msg = f"[SERVER STARTUP TRIGGER] Gateway Online at {now_str}"
            task_id = add_sms_task(DEFAULT_RECIPIENT, msg)
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "status": "queued",
                "task_id": task_id,
                "recipient": DEFAULT_RECIPIENT,
                "message": msg
            }).encode('utf-8'))
        elif self.path == '/' or self.path == '/status':
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT id, recipient, message, state, detail, created_at FROM sms_queue ORDER BY id DESC LIMIT 100")
            rows = cursor.fetchall()
            conn.close()

            html = "<html><head><title>SMS Gateway Server Log Dashboard (3 Months Retention)</title></head><body style='font-family:sans-serif;background:#121212;color:#fff;padding:20px;'>"
            html += "<h1>📱 SMS Gateway Server Log Dashboard</h1>"
            html += f"<h3>Server Date & Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h3>"
            html += "<p style='color:#aaa;'>Common Log File: <code>/var/log/sms_gateway_activity.log</code> (Automatic 3-month retention window)</p>"
            html += "<table border='1' cellpadding='8' style='border-collapse:collapse;width:100%;'>"
            html += "<tr style='background:#333;'><th>ID</th><th>Recipient</th><th>Message</th><th>State</th><th>Detail</th><th>Created At</th></tr>"
            for r in rows:
                color = "#4CAF50" if r[3] == 'sent' else ("#F44336" if r[3] == 'failed' else "#FF9800")
                html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td style='color:{color};font-weight:bold;'>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td></tr>"
            html += "</table></body></html>"
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body_data = self.rfile.read(content_length).decode('utf-8')
        try:
            payload = json.loads(body_data) if body_data else {}
        except Exception:
            payload = {}

        if self.path.startswith('/api/sms/status'):
            task_id = payload.get('task_id')
            status = payload.get('status')
            detail = payload.get('detail', '')
            if task_id:
                update_task_status(task_id, status, detail)
                self._set_headers(200)
                self.wfile.write(json.dumps({"result": "ok"}).encode('utf-8'))
            else:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing task_id"}).encode('utf-8'))
        elif self.path.startswith('/api/sms/log-dispatch'):
            recipient = payload.get('to') or payload.get('recipient')
            message = payload.get('message')
            status = payload.get('status', 'sent')
            detail = payload.get('detail', 'Sent via Phone App')
            if recipient and message:
                task_id = log_phone_dispatch(recipient, message, status, detail)
                self._set_headers(200)
                self.wfile.write(json.dumps({"result": "ok", "task_id": task_id}).encode('utf-8'))
            else:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing 'to' or 'message'"}).encode('utf-8'))
        elif self.path.startswith('/queue-sms'):
            recipient = payload.get('to')
            message = payload.get('message')
            if recipient and message:
                task_id = add_sms_task(recipient, message)
                self._set_headers(200)
                self.wfile.write(json.dumps({"status": "queued", "task_id": task_id}).encode('utf-8'))
            else:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing 'to' or 'message'"}).encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))

def run_server(port=22):
    init_db()
    trigger_server_startup_message()
    server_address = ('', port)
    httpd = HTTPServer(server_address, SmsGatewayRequestHandler)
    log_activity(f"🚀 SMS Gateway Server listening on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log_activity("Stopping server...")
        httpd.server_close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "add":
        init_db()
        recipient = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_RECIPIENT
        message = sys.argv[3] if len(sys.argv) > 3 else f"hello world {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        add_sms_task(recipient, message)
    else:
        run_server(22)
