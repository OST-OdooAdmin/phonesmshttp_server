#!/usr/bin/env python3
"""
Dynamic Public IP Monitor & Auto-Notifier
Checks public IP address hourly. When IP changes, records update and
publishes live IP to GitHub / Google Drive webhook for 100% free tracking.
"""

import urllib.request
import os
import json
import time
import datetime

IP_FILE = "/root/current_ip.txt"
LOG_FILE = "/var/log/ip_changes.log"

def get_public_ip():
    try:
        url = "https://api.ipify.org"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.read().decode('utf-8').strip()
    except Exception as e:
        print(f"Error fetching public IP: {e}")
        return None

def check_and_notify_ip():
    new_ip = get_public_ip()
    if not new_ip:
        return

    old_ip = ""
    if os.path.exists(IP_FILE):
        with open(IP_FILE, "r") as f:
            old_ip = f.read().strip()

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if new_ip != old_ip:
        log_entry = f"[{now_str}] 🌐 PUBLIC IP CHANGED: Old={old_ip} -> New={new_ip}\n"
        print(log_entry.strip())
        
        with open(IP_FILE, "w") as f:
            f.write(new_ip)
            
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)

        # 100% Free Auto-Push to GitHub / Google Drive tracking file
        try:
            os.system(f"cd /root && git add current_ip.txt && git commit -m 'Auto-Update Server Public IP: {new_ip} ({now_str})' && git push origin main 2>/dev/null || true")
        except Exception as e:
            print(f"Git push IP error: {e}")
    else:
        print(f"[{now_str}] Public IP unchanged: {new_ip}")

if __name__ == '__main__':
    check_and_notify_ip()
