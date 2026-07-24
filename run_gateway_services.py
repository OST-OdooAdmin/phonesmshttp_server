#!/usr/bin/env python3
import subprocess
import time
import re

print("Starting SMS Gateway Server...")
gateway_proc = subprocess.Popen(["python3", "/root/server_sms_gateway.py"])

print("Starting Cloudflare Tunnel...")
tunnel_proc = subprocess.Popen(
    ["cloudflared", "tunnel", "--url", "http://127.0.0.1:8069"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

url = None
for line in iter(tunnel_proc.stdout.readline, ''):
    print(line, end='')
    match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
    if match:
        url = match.group(0)
        with open("/root/tunnel_url.txt", "w") as f:
            f.write(url)
        print(f"\n==========================================")
        print(f"🎉 CLOUDFLARE PUBLIC TUNNEL URL: {url}")
        print(f"==========================================\n")
        break

gateway_proc.wait()
