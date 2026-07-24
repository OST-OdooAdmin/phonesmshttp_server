#!/bin/bash
# 1. Add internal Port 22222 for SSH
if ! grep -q "^Port 22222" /etc/ssh/sshd_config; then
    echo "Port 22222" >> /etc/ssh/sshd_config
fi
systemctl restart sshd

# 2. Configure sslh multiplexer on port 22
cat << 'EOF' > /etc/default/sslh
RUN=yes
DAEMON=/usr/sbin/sslh
DAEMON_OPTS="--user sslh --listen 0.0.0.0:22 --ssh 127.0.0.1:22222 --http 127.0.0.1:8069 --pidfile /var/run/sslh/sslh.pid"
EOF

systemctl restart sslh
