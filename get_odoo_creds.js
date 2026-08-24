const { Client } = require('ssh2');

const authMethods = [
    { port: 22222, password: 'Dreamer1!' },
    { port: 22222, password: '5ptr-2hdv-kaji' },
    { port: 22, password: 'Dreamer1!' },
    { port: 22, password: '5ptr-2hdv-kaji' }
];

function tryNext(idx) {
    if (idx >= authMethods.length) {
        console.log("All attempts failed.");
        return;
    }
    const m = authMethods[idx];
    const conn = new Client();
    conn.on('ready', () => {
        console.log(`SSH Success on port ${m.port}!`);
        const cmd = `
            echo "--- DATABASES ---"
            docker exec odoo19-web psql -U odoo -l 2>/dev/null || psql -U odoo -l
            echo "--- RES_USERS IN DEFAULT DB ---"
            docker exec odoo19-web psql -U odoo -d postgres -c "SELECT id, login, password FROM res_users;" 2>/dev/null || psql -U odoo -d postgres -c "SELECT id, login FROM res_users;"
        `;
        conn.exec(cmd, (err, stream) => {
            if (err) {
                console.error(err);
                conn.end();
                return;
            }
            stream.on('data', data => console.log(data.toString()));
            stream.on('close', () => conn.end());
        });
    }).on('error', err => {
        console.log(`Failed port ${m.port}:`, err.message);
        tryNext(idx + 1);
    }).connect({
        host: '175.142.51.75',
        port: m.port,
        username: 'root',
        password: m.password
    });
}

tryNext(0);
