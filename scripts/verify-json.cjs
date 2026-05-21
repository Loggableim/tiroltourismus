const fs = require('fs');
try {
  const data = JSON.parse(fs.readFileSync('src/data/magazin/tiroler-kueche-traditionelle-gerichte--spezialitaeten/index.json', 'utf-8'));
  console.log('VALID JSON');
  console.log('Title:', data.titel);
  console.log('Tags:', data.tags.join(', '));
} catch(e) {
  console.log('ERROR:', e.message);
}
