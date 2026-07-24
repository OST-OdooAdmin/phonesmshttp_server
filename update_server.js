const fs = require('fs');
const http = require('http');

const code = fs.readFileSync('server_sms_gateway.py', 'utf8');
const payload = JSON.stringify({ code: code });

const req = http.request({
    hostname: '115.135.158.84',
    port: 2222,
    path: '/api/server/update-code',
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
    }
}, (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => console.log('SERVER UPDATE RESULT:', data));
});

req.on('error', e => console.error('ERROR:', e.message));
req.write(payload);
req.end();
