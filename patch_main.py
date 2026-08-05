import os

with open('/app/main.py', 'r', encoding='utf-8') as f:
    code = f.read()

snippet = """        with open('/tmp/debug_path.txt', 'a') as f_debug:
            f_debug.write(f"DO_GET PATH: {self.path}\\n")
        if '/api/sms/' in self.path:
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

code = code.replace("def do_GET(self):", "def do_GET(self):\n" + snippet)

with open('/app/main.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("DEBUG_PATCH_APPLIED")
