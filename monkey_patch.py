import sys, urllib.request, json

main_mod = sys.modules.get('__main__')
if main_mod and hasattr(main_mod, 'AntigravityHandler'):
    handler_cls = main_mod.AntigravityHandler
    
    orig_do_GET = handler_cls.do_GET
    orig_do_POST = handler_cls.do_POST

    def custom_do_GET(self):
        if self.path.startswith('/api/sms/'):
            try:
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
        orig_do_GET(self)

    def custom_do_POST(self):
        if self.path.startswith('/api/sms/') or self.path.startswith('/queue-sms'):
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            try:
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
        orig_do_POST(self)

    handler_cls.do_GET = custom_do_GET
    handler_cls.do_POST = custom_do_POST
    print("MONKEY_PATCH_SUCCESSFUL")
else:
    print("MAIN_MOD_NOT_FOUND")
