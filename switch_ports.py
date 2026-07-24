import subprocess

with open("/etc/ssh/sshd_config", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip().startswith("Port"):
        continue
    new_lines.append(line)
new_lines.append("Port 22222\n")

with open("/etc/ssh/sshd_config", "w") as f:
    f.writelines(new_lines)

subprocess.run(["systemctl", "restart", "sshd"])

sslh_conf = """RUN=yes
DAEMON=/usr/sbin/sslh
DAEMON_OPTS="--user sslh --listen 0.0.0.0:22 --ssh 127.0.0.1:22222 --http 127.0.0.1:8069 --pidfile /var/run/sslh/sslh.pid"
"""
with open("/etc/default/sslh", "w") as f:
    f.write(sslh_conf)

subprocess.run(["systemctl", "restart", "sslh"])
print("SWITCH_SUCCESS")
