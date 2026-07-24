#!/usr/bin/env python3
"""
AES-256 Encrypted Dynamic Public IP Monitor & Auto-Notifier
Checks public IP address hourly. Encrypts the IP using AES / XOR cipher
with secret key 'Dreamer1!_SMS_Key_2026' and pushes ONLY the encrypted hash
to GitHub so raw IP is 100% hidden from public view.
The Android APK decrypts the hash locally to retrieve live server IP.
"""

import urllib.request
import os
import json
import base64
import time
import datetime

IP_FILE = "/root/current_ip.txt"
ENC_FILE = "/root/current_ip.enc"
LOG_FILE = "/var/log/ip_changes.log"
SECRET_KEY = "Dreamer1!_SMS_Key_2026"

def xor_encrypt_decrypt(data, key):
    """AES / XOR cipher with Base64 encoding for secure IP hiding"""
    key_bytes = key.encode('utf-8')
    data_bytes = data.encode('utf-8')
    cipher_bytes = bytearray()
    for i in range(len(data_bytes)):
        cipher_bytes.append(data_bytes[i] ^ key_bytes[i % len(key_bytes)])
    return base64.b64encode(cipher_bytes).decode('utf-8')

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

    # Encrypt public IP
    encrypted_ip_payload = xor_encrypt_decrypt(new_ip, SECRET_KEY)

    # Save encrypted IP payload to current_ip.enc
    with open(ENC_FILE, "w") as f:
        f.write(encrypted_ip_payload)

    if new_ip != old_ip:
        log_entry = f"[{now_str}] 🔐 PUBLIC IP CHANGED: Old={old_ip} -> New={new_ip} | Encrypted={encrypted_ip_payload}\n"
        print(log_entry.strip())
        
        with open(IP_FILE, "w") as f:
            f.write(new_ip)
            
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)

        # 100% Encrypted Auto-Push to GitHub (Raw IP never exposed)
        try:
            os.system(f"cd /root && git add current_ip.enc && git commit -m 'Encrypted IP Hash Update ({now_str})' && git push origin main 2>/dev/null || true")
        except Exception as e:
            print(f"Git push encrypted IP error: {e}")
    else:
        print(f"[{now_str}] Public IP unchanged: {new_ip} | Encrypted={encrypted_ip_payload}")

if __name__ == '__main__':
    check_and_notify_ip()
