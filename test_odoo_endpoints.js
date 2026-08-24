const http = require('http');

function getUrl(path) {
    return new Promise((resolve) => {
        const options = {
            hostname: '175.142.51.75',
            port: 8069,
            path: path,
            method: 'GET',
            headers: {
                'X-Api-Key': 'secret_sms_key_123'
            },
            timeout: 5000
        };

        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                resolve({ path, status: res.statusCode, body });
            });
        });

        req.on('error', (err) => {
            resolve({ path, error: err.message });
        });

        req.end();
    });
}

async function run() {
    console.log("Checking Odoo SMS API Endpoints...");
    const p = await getUrl('/api/sms/pending');
    const l = await getUrl('/api/sms/logs');
    console.log("Pending:", JSON.stringify(p, null, 2));
    console.log("Logs:", JSON.stringify(l, null, 2));
}

run();
