const http = require('http');
const fs = require('fs');

let cmd = process.argv.slice(2).join(' ');
if (!cmd && fs.existsSync('cmd.txt')) {
    cmd = fs.readFileSync('cmd.txt', 'utf8').trim();
}
if (!cmd) {
    cmd = 'id && uname -a';
}

function exec(command) {
    const payload = JSON.stringify({ command });
    const options = {
        hostname: '175.142.51.75',
        port: 5005,
        path: '/execute',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(payload)
        },
        timeout: 10000
    };

    const req = http.request(options, (res) => {
        let body = '';
        res.on('data', (chunk) => body += chunk);
        res.on('end', () => {
            console.log(`STATUS: ${res.statusCode}`);
            try {
                const parsed = JSON.parse(body);
                console.log("--- STDOUT ---");
                console.log(parsed.stdout || '(empty)');
                console.log("--- STDERR ---");
                console.log(parsed.stderr || '(empty)');
            } catch (e) {
                console.log("RAW BODY:\n" + body);
            }
        });
    });

    req.on('error', (err) => {
        console.error("HTTP ERROR:", err.message);
    });

    req.write(payload);
    req.end();
}

exec(cmd);
