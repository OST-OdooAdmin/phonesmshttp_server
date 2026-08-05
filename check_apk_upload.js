const http = require('http');

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

sendCmd('base64 -d /tmp/apk_b64.txt > /root/app-debug.apk && ls -lh /root/app-debug.apk', (res1) => {
    console.log('APK File Status:', res1);
    sendCmd('pkill -f "python3 -m http.server 8088" ; cd /root && nohup python3 -m http.server 8088 > /dev/null 2>&1 &', (res2) => {
        console.log('Web Server Status:', res2);
    });
});
