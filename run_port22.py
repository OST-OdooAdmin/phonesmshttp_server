import subprocess

with open("/etc/ssh/sshd_config", "r") as f:
    text = f.read()

text = text.replace("Port 22\n", "#Port 22\n")
if "Port 22222" not in text:
    text += "\nPort 22222\n"

with open("/etc/ssh/sshd_config", "w") as f:
    f.write(text)

subprocess.run(["systemctl", "stop", "sslh"])
subprocess.run(["systemctl", "disable", "sslh"])
subprocess.run(["systemctl", "restart", "sshd"])

with open("/root/server_sms_gateway.py", "r") as f:
    code = f.read()

code = code.replace("run_server(8069)", "run_server(22)")
with open("/root/server_sms_gateway.py", "w") as f:
    f.write(code)

subprocess.run(["systemctl", "restart", "sms-gateway"])
print("PORT_22_LIVE")
