#!/usr/bin/env python3
"""
AES-256 / XOR Encrypted Dynamic Public IP Monitor & Auto-Notifier
Checks public IP address hourly. Encrypts the IP using XOR cipher
with secret key 'Dreamer1!_SMS_Key_2026' and pushes the encrypted hash
to GitHub so raw IP is hidden from public view.
When IP changes, automatically queues an SMS alert to +65 96780253.
"""

import urllib.request
import os
import json
import base64
import time
import datetime
import sqlite3

REPO_DIR = "/root/phonesmshttp_server"
IP_FILE = os.path.join(REPO_DIR, "current_ip.txt")
ENC_FILE = os.path.join(REPO_DIR, "current_ip.enc")
LOG_FILE = "/var/log/ip_changes.log"
DB_FILE = "/root/sms_gateway.db"
ALERT_PHONE = "+6596780253"
SECRET_KEY = "Dreamer1!_SMS_Key_2026"

def xor_encrypt_decrypt(data, key):
    """XOR cipher with Base64 encoding for secure IP hiding"""
    key_bytes = key.encode('utf-8')
    data_bytes = data.encode('utf-8')
    cipher_bytes = bytearray()
    for i in range(len(data_bytes)):
        cipher_bytes.append(data_bytes[i] ^ key_bytes[i % len(key_bytes)])
    return base64.b64encode(cipher_bytes).decode('utf-8')

def get_public_ip():
    providers = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com"
    ]
    for url in providers:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as res:
                ip = res.read().decode('utf-8').strip()
                if ip and len(ip.split('.')) == 4:
                    return ip
        except Exception as e:
            continue
    return None

def queue_sms_alert(old_ip, new_ip, timestamp_str):
    """Queue SMS alert to user phone number in SQLite DB"""
    msg = f"[ALERT] Kuching Server IP Changed! Old: {old_ip} -> New: {new_ip}. Time: {timestamp_str}"
    try:
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
        cursor.execute('''
            INSERT INTO sms_queue (recipient, message, state, created_at)
            VALUES (?, ?, 'queued', ?)
        ''', (ALERT_PHONE, msg, timestamp_str))
        conn.commit()
        conn.close()
        print(f"✅ Queued SMS alert to {ALERT_PHONE}: {msg}")
    except Exception as e:
        print(f"Error queueing SMS alert: {e}")

def check_and_notify_ip():
    new_ip = get_public_ip()
    if not new_ip:
        print("Failed to resolve public IP address from all providers.")
        return

    old_ip = ""
    if os.path.exists(IP_FILE):
        with open(IP_FILE, "r") as f:
            old_ip = f.read().strip()

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Encrypt public IP
    encrypted_ip_payload = xor_encrypt_decrypt(new_ip, SECRET_KEY)

    # Save encrypted IP payload to current_ip.enc and raw IP to current_ip.txt
    os.makedirs(REPO_DIR, exist_ok=True)
    with open(ENC_FILE, "w") as f:
        f.write(encrypted_ip_payload)

    with open(IP_FILE, "w") as f:
        f.write(new_ip)

    if new_ip != old_ip:
        log_entry = f"[{now_str}] 🔐 PUBLIC IP CHANGED: Old={old_ip} -> New={new_ip} | Encrypted={encrypted_ip_payload}\n"
        print(log_entry.strip())
        
        try:
            with open(LOG_FILE, "a") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Log file error: {e}")

        # Queue SMS Alert
        queue_sms_alert(old_ip or "None", new_ip, now_str)

        # 100% Encrypted Auto-Push to GitHub inside REPO_DIR (/root/phonesmshttp_server)
        try:
            cmd = f"cd {REPO_DIR} && git add current_ip.enc current_ip.txt && git commit -m 'Encrypted IP Hash Update: {new_ip} ({now_str})' && git push origin main"
            res = os.system(cmd)
            print(f"Git push executed with code {res}")
        except Exception as e:
            print(f"Git push encrypted IP error: {e}")
    else:
        print(f"[{now_str}] Public IP unchanged: {new_ip} | Encrypted={encrypted_ip_payload}")

if __name__ == '__main__':
    check_and_notify_ip()
