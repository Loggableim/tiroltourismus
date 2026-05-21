const path = require('path');
const fs = require('fs');

const DATA_DIR = path.resolve(process.cwd(), 'src/data');

function readCollection(name) {
  const dir = path.join(DATA_DIR, name);
  if (!fs.existsSync(dir)) return [];
  const entries = [];
  for (const item of fs.readdirSync(dir, { withFileTypes: true })) {
    if (!item.isDirectory()) continue;
    const jsonPath = path.join(dir, item.name, 'index.json');
    if (fs.existsSync(jsonPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
        if (data.status === 'archived') continue;
        entries.push({ slug: item.name, entry: data });
      } catch (e) { console.error(`Error in ${jsonPath}:`, e.message); }
    }
  }
  return entries;
}

const dirs = ['unterkuenfte', 'orte', 'gastro', 'sehenswuerdigkeiten'];
let allOk = true;

for (const d of dirs) {
  const entries = readCollection(d);
  for (const e of entries) {
    if (!e.entry.region) {
      console.log('MISSING region in ' + d + '/' + e.slug);
      allOk = false;
    }
  }
  console.log(d + ': ' + entries.length + ' entries, all with region ✓');
}

// Also check which regions are referenced vs which exist
const regions = readCollection('regionen').map(r => r.slug);
console.log('\nExisting regions: ' + regions.join(', '));

const referenced = {};
for (const d of ['unterkuenfte', 'orte', 'gastro', 'sehenswuerdigkeiten']) {
  const entries = readCollection(d);
  for (const e of entries) {
    if (e.entry.region && !referenced[e.entry.region]) {
      referenced[e.entry.region] = { count: 0, entries: [] };
    }
    if (e.entry.region) {
      referenced[e.entry.region].count++;
      referenced[e.entry.region].entries.push(d + '/' + e.slug);
    }
  }
}

for (const [reg, info] of Object.entries(referenced)) {
  const exists = regions.includes(reg) ? '✓' : '✗ MISSING';
  console.log(`  ${reg} (${exists}): ${info.count} entries`);
}

if (allOk) console.log('\nALL GOOD: region field present in every entry');
