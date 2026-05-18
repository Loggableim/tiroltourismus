const fs = require('fs');
const p = 'src/data/magazin/tiroler-kueche-traditionelle-gerichte--spezialitaeten/index.json';
const content = fs.readFileSync(p, 'utf-8');
try {
  JSON.parse(content);
  console.log('OK — valid JSON');
} catch(e) {
  console.log('JSON Error:', e.message);
  console.log('Position:', e.pos);
  // Show context around the error
  const pos = e.pos || 0;
  const start = Math.max(0, pos - 100);
  const end = Math.min(content.length, pos + 100);
  console.log('Context:\n' + content.substring(start, end));
  console.log('---');
  // Save a backup and attempt repair
  const backup = p.replace('.json', '.json.bak');
  fs.writeFileSync(backup, content);
  console.log('Backup saved to:', backup);
}
