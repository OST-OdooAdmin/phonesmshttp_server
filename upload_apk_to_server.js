const fs = require('fs');
const http = require('http');

const apkPath = 'C:\\Users\\MLAU\\.gemini\\antigravity\\scratch\\phonesmshttp_server\\app-debug.apk';
const apkBuffer = fs.readFileSync(apkPath);
const base64Apk = apkBuffer.toString('base64');

console.log(`APK Size: ${apkBuffer.length} bytes. Base64 length: ${base64Apk.length}`);

// Split base64 into 500KB chunks to send reliably via execution endpoint
const chunkSize = 500 * 1024;
const chunks = [];
for (let i = 0; i < base64Apk.length; i += chunkSize) {
    chunks.push(base64Apk.slice(i, i + chunkSize));
}

console.log(`Total Chunks: ${chunks.length}`);

function sendCmd(cmd, callback) {
    const payload = JSON.stringify({ cmd: cmd });
    const req = http.request({
        hostname: '115.135.158.84',
        port: 22,
        path: '/api/server/exec',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(payload)
        }
    }, (res) => {
        let body = '';
        res.on('data', (c) => body += c);
        res.on('end', () => callback(null, body));
    });
    req.on('error', (err) => callback(err));
    req.write(payload);
    req.end();
}

// First, prepare /tmp/apk_b64.txt
sendCmd('rm -f /tmp/apk_b64.txt && touch /tmp/apk_b64.txt', (err, res) => {
    console.log('Init result:', res);
    sendChunk(0);
});

function sendChunk(idx) {
    if (idx >= chunks.length) {
        console.log('All chunks sent! Decoding base64 to /root/app-debug.apk...');
        sendCmd('base64 -d /tmp/apk_b64.txt > /root/app-debug.apk && rm -f /tmp/apk_b64.txt && ls -lh /root/app-debug.apk', (err, res) => {
            console.log('Final decode result:', res);
            // Now start simple python http server on port 8088 to serve APK
            sendCmd('pkill -f "python3 -m http.server 8088" ; cd /root && nohup python3 -m http.server 8088 > /dev/null 2>&1 &', (err2, res2) => {
                console.log('Python HTTP server started on port 8088:', res2);
            });
        });
        return;
    }

    console.log(`Sending chunk ${idx + 1}/${chunks.length}...`);
    const chunkData = chunks[idx];
    const cmd = `cat << 'EOF' >> /tmp/apk_b64.txt\n${chunkData}\nEOF`;
    sendCmd(cmd, (err, res) => {
        if (err) {
            console.error(`Error sending chunk ${idx}:`, err);
        } else {
            sendChunk(idx + 1);
        }
    });
}
