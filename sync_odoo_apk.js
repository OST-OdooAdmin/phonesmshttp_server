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

const syncCmd = `
docker exec -u 0 odoo18-web mkdir -p /var/lib/odoo/custom_addons/phone_sms_gateway/controllers &&
docker cp /root/app-debug.apk odoo18-web:/var/lib/odoo/custom_addons/phone_sms_gateway/app-debug.apk &&
docker restart odoo18-web
`;

sendCmd(syncCmd, (res) => {
    console.log('Sync Odoo APK result:', res);
});
