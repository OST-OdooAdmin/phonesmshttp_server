const http = require('http');

function sendCmd(port, path, bodyObj) {
    const payload = JSON.stringify(bodyObj);
    const options = {
        hostname: '115.135.158.84',
        port: port,
        path: path,
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(payload)
        }
    };

    const req = http.request(options, (res) => {
        let body = '';
        res.on('data', (chunk) => body += chunk);
        res.on('end', () => {
            console.log(`Port ${port} Response:`, body);
        });
    });

    req.on('error', (err) => {
        console.error(`Port ${port} Request Error:`, err.message);
    });

    req.write(payload);
    req.end();
}

const addSmsCmd = `python3 /root/server_sms_gateway.py add "+6596780253" "fill test msg"`;

sendCmd(5005, '/execute', { command: addSmsCmd });
sendCmd(22, '/api/server/exec', { cmd: addSmsCmd });
