#!/bin/bash
pkill -f cloudflared
pkill -f server_sms_gateway.py

# Add test SMS task to queue
python3 /root/server_sms_gateway.py add "+6596780253" "hello world $(date '+%Y-%m-%d %H:%M:%S')"

# Start Gateway Server in background
nohup python3 /root/server_sms_gateway.py > /root/sms_server.log 2>&1 &

# Start Cloudflare Tunnel in background
nohup cloudflared tunnel --url http://127.0.0.1:8069 > /root/cloudflared.log 2>&1 &

sleep 6
grep -o "https://.*trycloudflare.com" /root/cloudflared.log | tail -n 1
