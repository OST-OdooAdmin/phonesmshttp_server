const { execSync } = require('child_process');

const adb = '"C:\\Users\\MLAU\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe"';

try {
  const output = execSync(`${adb} shell pm dump com.antigravity.smshttpgateway`, { encoding: 'utf-8' });
  const lines = output.split('\n').filter(l => l.includes('Activity') || l.includes('MAIN') || l.includes('LAUNCHER') || l.includes('com.antigravity'));
  console.log('--- FOUND STAGE 1 ACTIVITIES ---');
  console.log(lines.slice(0, 20).join('\n'));
} catch (err) {
  console.error('Error dumping package:', err.message);
}
