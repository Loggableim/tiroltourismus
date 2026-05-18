const fs = require('fs');
const p = 'src/data/magazin/tiroler-kueche-traditionelle-gerichte--spezialitaeten/index.json';
const content = fs.readFileSync(p, 'utf-8');
const pos = 3366;

console.log('Total length:', content.length);
console.log('Character at position', pos, ':', JSON.stringify(content[pos]));
console.log('Character at position', pos-1, ':', JSON.stringify(content[pos-1]));
console.log('Character at position', pos-2, ':', JSON.stringify(content[pos-2]));
console.log('Character at position', pos+1, ':', JSON.stringify(content[pos+1]));
console.log('Character at position', pos+2, ':', JSON.stringify(content[pos+2]));
console.log('');
console.log('Context (-50 to +50):');
console.log(content.substring(Math.max(0,pos-50), Math.min(content.length,pos+50)));
console.log('');
console.log('Context (-200 to +200):');
console.log(content.substring(Math.max(0,pos-200), Math.min(content.length,pos+200)));
