const http = require('http');

function sendCmd(port, path, bodyObj) {
    return new Promise((resolve) => {
        const payload = JSON.stringify(bodyObj);
        const options = {
            hostname: '115.135.158.84',
            port: port,
            path: path,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(payload)
            },
            timeout: 5000
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

        req.write(payload);
        req.end();
    });
}

async function run() {
    const diagCmd = `
echo "=== DOCKER CONTAINERS ==="
docker ps

echo "=== ODOO LOGS (LAST 50) ==="
docker logs --tail 50 odoo19-web

echo "=== QUERY POSTGRES sms_outbound_queue ==="
docker exec odoo19-web psql -U odoo -d postgres -c "SELECT id, recipient, state, create_date FROM sms_outbound_queue ORDER BY id DESC LIMIT 10;" 2>&1

echo "=== QUERY POSTGRES phone_sms_message ==="
docker exec odoo19-web psql -U odoo -d postgres -c "SELECT id, recipient_number, state, create_date FROM phone_sms_message ORDER BY id DESC LIMIT 10;" 2>&1

echo "=== GATEWAY LOG FILE ==="
tail -n 30 /var/log/sms_gateway_activity.log 2>&1
`;

    console.log("Running diagnostics on host...");
    const res5005 = await sendCmd(5005, '/execute', { command: diagCmd });
    console.log("5005 Response:", JSON.stringify(res5005, null, 2));

    const res22 = await sendCmd(22, '/api/server/exec', { cmd: diagCmd });
    console.log("22 Response:", JSON.stringify(res22, null, 2));
}

run();
