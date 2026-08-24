const { Client } = require('ssh2');

const host = '175.142.51.75';

const authMethods = [
    { name: 'Password Dreamer1! (Port 22222)', port: 22222, password: 'Dreamer1!' },
    { name: 'Password 5ptr-2hdv-kaji (Port 22222)', port: 22222, password: '5ptr-2hdv-kaji' },
    { name: 'Password Dreamer1! (Port 22)', port: 22, password: 'Dreamer1!' },
    { name: 'Password 5ptr-2hdv-kaji (Port 22)', port: 22, password: '5ptr-2hdv-kaji' }
];

function tryMethod(idx) {
    if (idx >= authMethods.length) {
        console.log("ALL AUTH METHODS ATTEMPTED.");
        return;
    }
    const method = authMethods[idx];
    console.log(`\nAttempting [${method.name}]...`);

    const conn = new Client();
    conn.on('ready', () => {
        console.log(`\n✅ SSH SUCCESS: [${method.name}]!`);
        const cmd = 'systemctl status sms-gateway; echo "--- DISPATCH QUEUE ---"; sqlite3 /root/sms_gateway.db "SELECT * FROM sms_queue ORDER BY id DESC LIMIT 10;"; echo "--- RECENT LOGS ---"; tail -n 20 /var/log/sms_gateway_activity.log; echo "--- NETWORK LISTENERS ---"; netstat -tulpn';
        conn.exec(cmd, (err, stream) => {
            if (err) {
                console.error("Exec error:", err);
                conn.end();
                return;
            }
            stream.on('close', (code, signal) => {
                console.log(`\nCommand completed with code ${code}`);
                conn.end();
            }).on('data', (data) => {
                console.log(data.toString());
            }).stderr.on('data', (data) => {
                console.error('STDERR:', data.toString());
            });
        });
    }).on('error', (err) => {
        console.log(`❌ Failed [${method.name}]: ${err.message}`);
        tryMethod(idx + 1);
    }).connect({
        host: host,
        port: method.port,
        username: 'root',
        password: method.password,
        readyTimeout: 10000
    });
}

tryMethod(0);
