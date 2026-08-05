import os
import sys

with open('/app/main.py', 'r', encoding='utf-8') as f:
    code = f.read()

get_snippet = """        if self.path.startswith('/api/sms/'):
            try:
                import urllib.request
                req = urllib.request.Request(f"http://172.17.0.1:22{self.path}")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = resp.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(data)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
            return
"""

post_snippet = """        if self.path.startswith('/api/sms/') or self.path.startswith('/queue-sms'):
            try:
                import urllib.request
                req = urllib.request.Request(
                    f"http://172.17.0.1:22{self.path}",
                    data=post_data.encode('utf-8'),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = resp.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(data)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
            return
"""

if "http://172.17.0.1:22" not in code:
    code = code.replace("def do_GET(self):", "def do_GET(self):\n" + get_snippet)
    code = code.replace("post_data = self.rfile.read(content_length).decode(\"utf-8\")", "post_data = self.rfile.read(content_length).decode(\"utf-8\")\n" + post_snippet)
    with open('/app/main.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("PATCHED_MAIN_PY_LIVE")

os.execv(sys.executable, ['python', 'main.py'])
