const http = require('http');

const patchScript = `
import re

with open('/root/server_sms_gateway.py', 'r') as f:
    code = f.read()

download_route = '''
        elif self.path.startswith('/download/app-debug.apk') or self.path.startswith('/app-debug.apk'):
            try:
                with open('/root/app-debug.apk', 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/vnd.android.package-archive')
                self.send_header('Content-Disposition', 'attachment; filename="app-debug.apk"')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(str(e).encode())
            return
'''

if '/download/app-debug.apk' not in code:
    code = code.replace("def do_GET(self):", "def do_GET(self):\n" + download_route)
    with open('/root/server_sms_gateway.py', 'w') as f:
        f.write(code)
    print("Patched server_sms_gateway.py with download route!")
else:
    print("Download route already exists in server_sms_gateway.py")
`;

function sendCmd(cmd, cb) {
    const payload = JSON.stringify({ cmd: cmd });
    const req = http.request({
        hostname: '115.135.158.84',
        port: 22,
        path: '/api/server/exec',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(payload)
        }
    }, (res) => {
        let body = '';
        res.on('data', (c) => body += c);
        res.on('end', () => cb(body));
    });
    req.write(payload);
    req.end();
}

const escapedPy = patchScript.replace(/'/g, "'\"'\"'");
sendCmd(`python3 -c '${escapedPy}' && pkill -f "python3 /root/server_sms_gateway.py" ; cd /root && nohup python3 /root/server_sms_gateway.py > /var/log/sms_gateway_activity.log 2>&1 &`, (res) => {
    console.log('Result:', res);
});
