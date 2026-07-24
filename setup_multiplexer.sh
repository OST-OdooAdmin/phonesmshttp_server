#!/bin/bash
# 1. Update sshd_config to listen on internal port 22222
if ! grep -q "^Port 22222" /etc/ssh/sshd_config; then
    echo "Port 22222" >> /etc/ssh/sshd_config
fi
# Remove port 22 from sshd_config if present so port 22 is free for multiplexer
sed -i 's/^Port 22$/#Port 22/' /etc/ssh/sshd_config
systemctl restart sshd

# 2. Kill old multiplexer
pkill -f multiplexer.py

# 3. Start multiplexer on port 22 in background
nohup python3 /root/multiplexer.py > /root/multiplexer.log 2>&1 &
