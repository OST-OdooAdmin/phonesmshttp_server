const fs = require('fs');

const SECRET_KEY = "Dreamer1!_SMS_Key_2026";

function decrypt(encryptedBase64) {
    try {
        const cipherBytes = Buffer.from(encryptedBase64.trim(), 'base64');
        const keyBytes = Buffer.from(SECRET_KEY, 'utf-8');
        const plainBytes = Buffer.alloc(cipherBytes.length);
        for (let i = 0; i < cipherBytes.length; i++) {
            plainBytes[i] = cipherBytes[i] ^ keyBytes[i % keyBytes.length];
        }
        return plainBytes.toString('utf-8').trim();
    } catch (e) {
        return "ERROR: " + e.message;
    }
}

if (fs.existsSync('current_ip.enc')) {
    const enc = fs.readFileSync('current_ip.enc', 'utf-8');
    console.log("DECRYPTED_IP:", decrypt(enc));
} else {
    console.log("NO_ENC_FILE");
}
