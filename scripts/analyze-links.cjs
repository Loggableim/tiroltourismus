const fs = require('fs');
const path = require('path');

const dataDir = 'src/data';
const collections = ['regionen', 'unterkuenfte', 'camping', 'gastro', 'orte', 'sehenswuerdigkeiten', 'magazin', 'erlebnisse', 'events'];

function countLinks(text) {
  if (!text) return 0;
  const linkMatches = text.match(/<a\s+href=/gi);
  const mdLinkMatches = text.match(/\[([^\]]+)\]\(([^)]+)\)/g);
  return (linkMatches ? linkMatches.length : 0) + (mdLinkMatches ? mdLinkMatches.length : 0);
}

function countInternalLinks(text, collection) {
  if (!text) return 0;
  const internalPattern = /href=["']\/(?:regionen|unterkuenfte|camping|gastro|orte|sehenswuerdigkeiten|magazin|erlebnisse|events|bezirke)/gi;
  const mdInternalPattern = /\]\(\/(?:regionen|unterkuenfte|camping|gastro|orte|sehenswuerdigkeiten|magazin|erlebnisse|events|bezirke)/gi;
  const html = (text.match(internalPattern) || []).length;
  const md = (text.match(mdInternalPattern) || []).length;
  return html + md;
}

const stats = {};
for (const coll of collections) {
  const dir = path.join(dataDir, coll);
  if (!fs.existsSync(dir)) continue;
  
  let total = 0;
  let withContent = 0;
  let withLinks = 0;
  let withInternalLinks = 0;
  let totalInternalLinks = 0;
  
  for (const item of fs.readdirSync(dir, {withFileTypes: true})) {
    if (!item.isDirectory()) continue;
    const jsonPath = path.join(dir, item.name, 'index.json');
    if (!fs.existsSync(jsonPath)) continue;
    try {
      const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
      if (data.status === 'archived') continue;
      total++;
      
      // Check content fields
      const contentFields = [data.inhalt, data.beschreibung, data.kurzbeschreibung].filter(Boolean);
      const hasContent = contentFields.length > 0;
      if (hasContent) withContent++;
      
      const linkCount = contentFields.reduce((sum, f) => sum + countLinks(f), 0);
      const internalLinkCount = contentFields.reduce((sum, f) => sum + countInternalLinks(f, coll), 0);
      
      if (linkCount > 0) withLinks++;
      if (internalLinkCount > 0) withInternalLinks++;
      totalInternalLinks += internalLinkCount;
    } catch(e) {}
  }
  
  stats[coll] = { total, withContent, withLinks, withInternalLinks, totalInternalLinks };
}

console.log('COLLECTION | TOTAL | WITH CONTENT | HAS ANY LINKS | HAS INTERNAL LINKS | TOTAL INTERNAL');
console.log('-' .repeat(100));
for (const [coll, s] of Object.entries(stats)) {
  console.log(
    coll.padEnd(16), '|',
    String(s.total).padStart(5), '|',
    String(s.withContent).padStart(12), '|',
    String(s.withLinks).padStart(13), '|',
    String(s.withInternalLinks).padStart(18), '|',
    String(s.totalInternalLinks).padStart(14)
  );
}

// Show some entries without internal links
console.log('\n\n=== ENTRIES WITHOUT INTERNAL LINKS (sample from each collection) ===');
for (const coll of collections) {
  const dir = path.join(dataDir, coll);
  if (!fs.existsSync(dir)) continue;
  
  let shown = 0;
  for (const item of fs.readdirSync(dir, {withFileTypes: true})) {
    if (shown >= 3) break;
    if (!item.isDirectory()) continue;
    const jsonPath = path.join(dir, item.name, 'index.json');
    if (!fs.existsSync(jsonPath)) continue;
    try {
      const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
      if (data.status === 'archived') continue;
      
      const contentFields = [data.inhalt, data.beschreibung, data.kurzbeschreibung].filter(Boolean);
      const internalLinkCount = contentFields.reduce((sum, f) => sum + countInternalLinks(f, coll), 0);
      
      if (internalLinkCount === 0 && contentFields.length > 0) {
        const name = data.name || data.titel || item.name;
        const contentPreview = (data.beschreibung || data.inhalt || '').replace(/<[^>]*>/g, '').substring(0, 80);
        console.log(`  ${coll}/${item.name} — "${name}"`);
        console.log(`    Content: "${contentPreview}..."`);
        shown++;
      }
    } catch(e) {}
  }
}
