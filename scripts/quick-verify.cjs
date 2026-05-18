const fs = require('fs');

// 1. Check content.js
const content = fs.readFileSync('src/lib/content.js', 'utf-8');
console.log('=== content.js verification ===');
console.log('Has autoLinkContent:', content.includes('autoLinkContent'));
console.log('Has invalidateEntityCache:', content.includes('invalidateEntityCache'));
console.log('Has findNearby with results.sort:', content.includes('results.sort'));
console.log('File size:', content.length, 'bytes');

// 2. Check all slug templates
const tpls = [
  'src/pages/orte/[slug].astro',
  'src/pages/sehenswuerdigkeiten/[slug].astro',
  'src/pages/gastro/[slug].astro',
  'src/pages/erlebnisse/[slug].astro',
  'src/pages/unterkuenfte/[slug].astro',
  'src/pages/camping/[slug].astro',
  'src/pages/regionen/[slug].astro',
  'src/pages/events/[slug].astro',
  'src/pages/magazin/[slug].astro',
  'src/pages/[locale]/regionen/[slug].astro',
];
console.log('\n=== Slug templates ===');
let allOk = true;
for (const tpl of tpls) {
  if (!fs.existsSync(tpl)) { console.log('MISSING:', tpl); allOk = false; continue; }
  const c = fs.readFileSync(tpl, 'utf-8');
  const hasFindByTag = c.includes('findByTag');
  const hasFindRelated = c.includes('findRelated');
  const hasAutoLink = c.includes('autoLinkContent');
  const hasRelatedSection = c.includes('relatedByTag') || c.includes('relatedSection') || c.includes('related-grid');
  const label = tpl.split('/').slice(-2).join('/').replace(']', '').replace('[', '');
  const status = (hasFindByTag || hasFindRelated) && (hasRelatedSection) ? 'OK' : 'MISSING';
  if (status === 'MISSING') allOk = false;
  console.log(`  ${label.padEnd(25)} findByTag=${hasFindByTag ? '✓' : ' '} autoLink=${hasAutoLink ? '✓' : ' '} relatedSection=${hasRelatedSection ? '✓' : ' '} → ${status}`);
}
console.log('\nAll checks:', allOk ? '✅ PASSED' : '❌ FAILED');
