const fs = require('fs');
const path = require('path');

const dataDir = 'src/data';
const collections = ['regionen', 'unterkuenfte', 'camping', 'gastro', 'orte', 'sehenswuerdigkeiten', 'magazin', 'erlebnisse', 'events'];

const allTags = {};
const slugMap = {}; // slug -> [{collection, name}]
const untagged = [];

for (const coll of collections) {
  const dir = path.join(dataDir, coll);
  if (!fs.existsSync(dir)) continue;
  for (const item of fs.readdirSync(dir, {withFileTypes: true})) {
    if (!item.isDirectory()) continue;
    const jsonPath = path.join(dir, item.name, 'index.json');
    if (!fs.existsSync(jsonPath)) continue;
    try {
      const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
      if (data.status === 'archived') continue;
      const slug = data.slug || item.name;
      if (!slugMap[slug]) slugMap[slug] = [];
      slugMap[slug].push({collection: coll, name: data.name || data.titel});
      
      if (data.tags && Array.isArray(data.tags) && data.tags.length > 0) {
        for (const tag of data.tags) {
          if (!allTags[tag]) allTags[tag] = [];
          allTags[tag].push({collection: coll, slug, name: data.name || data.titel});
        }
      } else {
        untagged.push({collection: coll, slug, name: data.name || data.titel});
      }
    } catch(e) {
      console.error(`Error reading ${jsonPath}: ${e.message}`);
    }
  }
}

console.log('=== TAG ANALYSIS ===\n');

// Tags sorted by usage count
const sortedTags = Object.entries(allTags).sort((a, b) => b[1].length - a[1].length);
console.log('Tags used in entries:');
for (const [tag, entries] of sortedTags) {
  const collections = [...new Set(entries.map(e => e.collection))];
  console.log(`  "${tag}" (${entries.length} entries, ${collections.join(', ')})`);
}

console.log(`\nTotal unique tags: ${sortedTags.length}`);
console.log(`Total entries with tags: ${Object.values(allTags).flat().length} tag-assignments`);

// Check which tags might reference existing pages (tags that are also slugs)
console.log('\n=== TAGS THAT MATCH EXISTING SLUGS ===');
const allSlugs = Object.keys(slugMap);
for (const [tag, _] of sortedTags) {
  const tagLower = tag.toLowerCase().replace(/[^a-z0-9-]/g, '');
  const matches = allSlugs.filter(s => s.toLowerCase() === tagLower || s.toLowerCase().includes(tagLower));
  if (matches.length > 0) {
    console.log(`  "${tag}" → slug matches: ${matches.join(', ')}`);
  }
}

// Check entries that might correspond to tags but don't have them
console.log('\n=== ORPHAN TAGS (tags that match no existing slug) ===');
for (const [tag, _] of sortedTags) {
  const tagLower = tag.toLowerCase().replace(/[^a-z0-9-]/g, '');
  const matches = allSlugs.filter(s => s.toLowerCase() === tagLower || s.toLowerCase().includes(tagLower) || tagLower.includes(s));
  if (matches.length === 0) {
    console.log(`  "${tag}" — no matching page slug found`);
  }
}

console.log(`\n=== ENTRIES WITHOUT TAGS (${untagged.length}) ===`);
for (const e of untagged.slice(0, 20)) {
  console.log(`  ${e.collection}/${e.slug} — ${e.name}`);
}
if (untagged.length > 20) console.log(`  ... and ${untagged.length - 20} more`);

console.log(`\nTotal entries in slugMap: ${allSlugs.length}`);
