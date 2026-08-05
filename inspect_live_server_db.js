const http = require('http');

function fetchJson(port, path) {
    return new Promise((resolve) => {
        const options = {
            hostname: '115.135.158.84',
            port: port,
            path: path,
            method: 'GET',
            timeout: 5000
        };

        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                try {
                    resolve({ port, path, status: res.statusCode, data: JSON.parse(body) });
                } catch (e) {
                    resolve({ port, path, status: res.statusCode, raw: body });
                }
            });
        });

        req.on('error', (err) => {
            resolve({ port, path, error: err.message });
        });

        req.end();
    });
}

async function run() {
    console.log("=== INSPECTING LIVE SERVER SMS DB & QUEUE ===");
    const pending22 = await fetchJson(22, '/api/sms/pending');
    const logs22 = await fetchJson(22, '/api/sms/logs');
    const pending5005 = await fetchJson(5005, '/api/sms/pending');

    console.log("--- PORT 22 PENDING ---", JSON.stringify(pending22, null, 2));
    console.log("--- PORT 22 LOGS ---", JSON.stringify(logs22, null, 2));
    console.log("--- PORT 5005 PENDING ---", JSON.stringify(pending5005, null, 2));
}

run();
