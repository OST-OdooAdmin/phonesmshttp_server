import socket

for host in ['192.168.0.106', '115.135.158.84']:
    for port in [22222, 22, 5005, 8069]:
        s = socket.socket()
        s.settimeout(3)
        try:
            s.connect((host, port))
            banner = s.recv(1024).decode('utf-8', errors='ignore') if port in [22, 22222] else 'HTTP'
            print(f"OPEN: {host}:{port} -> {banner.strip()[:40]}")
        except Exception as e:
            print(f"CLOSED/TIMEOUT: {host}:{port} ({e})")
        finally:
            s.close()
