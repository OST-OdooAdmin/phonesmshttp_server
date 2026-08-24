const http = require('http');
const fs = require('fs');

function sendCmd(port, path, bodyObj) {
    return new Promise((resolve) => {
        const payload = JSON.stringify(bodyObj);
        const options = {
            hostname: '175.142.51.75',
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
    const res22 = await sendCmd(22, '/api/server/exec', { cmd: "docker exec odoo19-web psql -U odoo -d postgres -c 'SELECT id, login FROM res_users;' 2>/dev/null || psql -U odoo -d postgres -c 'SELECT id, login FROM res_users;' 2>/dev/null" });
    
    const res22_db = await sendCmd(22, '/api/server/exec', { cmd: "docker exec odoo19-web psql -U odoo -d DreamHRsolution -c 'SELECT id, login FROM res_users;' 2>/dev/null || psql -U odoo -d DreamHRsolution -c 'SELECT id, login FROM res_users;' 2>/dev/null" });

    const output = `--- RES_USERS (POSTGRES DB) ---\n${JSON.stringify(res22, null, 2)}\n\n--- RES_USERS (DreamHRsolution DB) ---\n${JSON.stringify(res22_db, null, 2)}\n`;
    
    fs.writeFileSync('exec_results.utf8.txt', output, 'utf8');
    console.log("Done writing results!");
}

run();
