const http = require('http');

function checkEndpoint(port, path) {
    return new Promise((resolve) => {
        const options = {
            hostname: '115.135.158.84',
            port: port,
            path: path,
            method: 'GET',
            timeout: 4000
        };

        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                resolve({ port, path, status: res.statusCode, body });
            });
        });

        req.on('error', (err) => {
            resolve({ port, path, error: err.message });
        });

        req.on('timeout', () => {
            req.destroy();
            resolve({ port, path, error: 'Timeout' });
        });

        req.end();
    });
}

async function run() {
    console.log("Checking Queue Endpoints...");
    const results = await Promise.all([
        checkEndpoint(22, '/api/sms/pending'),
        checkEndpoint(22, '/api/sms/logs'),
        checkEndpoint(5005, '/api/sms/pending'),
        checkEndpoint(8069, '/api/sms/pending')
    ]);
    console.log(JSON.stringify(results, null, 2));
}

run();
