const http = require('http');
const net = require('net');

const hosts = ['175.142.51.75', '115.135.158.84'];
const ports = [22, 5005, 8069, 8080, 22222, 80];

function checkPort(host, port) {
    return new Promise((resolve) => {
        const socket = new net.Socket();
        socket.setTimeout(2500);
        socket.on('connect', () => {
            socket.destroy();
            resolve({ host, port, status: 'OPEN' });
        });
        socket.on('timeout', () => {
            socket.destroy();
            resolve({ host, port, status: 'TIMEOUT' });
        });
        socket.on('error', (err) => {
            socket.destroy();
            resolve({ host, port, status: 'CLOSED: ' + err.code });
        });
        socket.connect(port, host);
    });
}

async function run() {
    console.log("Probing remote servers...");
    for (const host of hosts) {
        for (const port of ports) {
            const res = await checkPort(host, port);
            console.log(`[${res.host}:${res.port}] -> ${res.status}`);
        }
    }
}

run();
