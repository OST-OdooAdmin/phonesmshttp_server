const http = require('http');
const querystring = require('querystring');

function resetSupermicroHardware() {
    const loginData = querystring.stringify({
        'name': 'ADMIN',
        'pwd': 'Dreamer1!'
    });

    const options = {
        hostname: '115.135.158.84',
        port: 9000,
        path: '/cgi/login.cgi',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': Buffer.byteLength(loginData)
        }
    };

    const req = http.request(options, (res) => {
        let cookieHeader = res.headers['set-cookie'] ? res.headers['set-cookie'].join('; ') : '';
        console.log("Login Cookie:", cookieHeader);

        // Perform Power Reset on Supermicro ATEN IPMI via /cgi/power.cgi or /cgi/op.cgi
        sendPowerCommand(cookieHeader, '3'); // 3 = Power Reset / Cycle in Supermicro ATEN IPMI
    });

    req.on('error', (e) => console.error("Login Error:", e.message));
    req.write(loginData);
    req.end();
}

function sendPowerCommand(cookieHeader, powerOp) {
    const powerData = querystring.stringify({
        'op': powerOp
    });

    const options = {
        hostname: '115.135.158.84',
        port: 9000,
        path: '/cgi/ipmi.cgi',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookieHeader,
            'Content-Length': Buffer.byteLength(powerData)
        }
    };

    const req = http.request(options, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
            console.log('IPMI POWER RESET RESULT:', data);
        });
    });

    req.on('error', (e) => console.error("Power Command Error:", e.message));
    req.write(powerData);
    req.end();
}

resetSupermicroHardware();
