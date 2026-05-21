import fs from 'fs';
import path from 'path';

const filePath = 'src/lib/content.js';
const content = fs.readFileSync(filePath, 'utf-8');

// Simple check: count imports, exports, function blocks
const imports = (content.match(/^import /gm) || []).length;
const exports = (content.match(/^export /gm) || []).length;
const functions = (content.match(/^export (async )?function /gm) || []).length;

console.log(`File: ${filePath}`);
console.log(`Size: ${content.length} bytes`);
console.log(`Imports: ${imports}`);
console.log(`Exports: ${exports}`);
console.log(`Exported functions: ${functions}`);
console.log('');

// Check for autoLinkContent
if (content.includes('autoLinkContent')) {
  console.log('✓ autoLinkContent function defined');
} else {
  console.log('✗ autoLinkContent function MISSING');
}

// Check for invalidateEntityCache
if (content.includes('invalidateEntityCache')) {
  console.log('✓ invalidateEntityCache function defined');
} else {
  console.log('✗ invalidateEntityCache function MISSING');
}

// Verify findNearby function ends correctly
const fnIdx = content.indexOf('export function findNearby');
const endIdx = content.indexOf('\n}', fnIdx);
if (endIdx > 0) {
  const fnBody = content.substring(fnIdx, endIdx + 2);
  if (fnBody.includes('results.sort') && fnBody.includes('results.slice')) {
    console.log('✓ findNearby function has correct variable names');
  } else {
    console.log('✗ findNearby function may have incorrect variables!');
    console.log(fnBody.substring(fnBody.length - 100));
  }
}

// Check key slug templates for autoLinkContent usage
const templates = [
  'src/pages/sehenswuerdigkeiten/[slug].astro',
  'src/pages/gastro/[slug].astro',
  'src/pages/erlebnisse/[slug].astro',
  'src/pages/regionen/[slug].astro',
  'src/pages/unterkuenfte/[slug].astro',
  'src/pages/camping/[slug].astro',
  'src/pages/events/[slug].astro',
  'src/pages/[locale]/regionen/[slug].astro',
];

console.log('\n=== Template autoLinkContent Check ===');
for (const tpl of templates) {
  if (!fs.existsSync(tpl)) { console.log(`  ${tpl}: FILE NOT FOUND`); continue; }
  const tplContent = fs.readFileSync(tpl, 'utf-8');
  const hasImport = tplContent.includes('autoLinkContent');
  const hasUsage = tplContent.includes('autoLinkContent(');
  console.log(`  ${tpl}: import=${hasImport}, used=${hasUsage}`);
}

// Check slug templates for findByTag usage (Weitere Beiträge)
console.log('\n=== Template findByTag / Weitere Beiträge Check ===');
const allTemplates = [
  'src/pages/orte/[slug].astro',
  'src/pages/sehenswuerdigkeiten/[slug].astro',
  'src/pages/gastro/[slug].astro',
  'src/pages/erlebnisse/[slug].astro',
  'src/pages/unterkuenfte/[slug].astro',
  'src/pages/camping/[slug].astro',
  'src/pages/regionen/[slug].astro',
  'src/pages/events/[slug].astro',
  'src/pages/magazin/[slug].astro',
];
for (const tpl of allTemplates) {
  if (!fs.existsSync(tpl)) { console.log(`  ${tpl}: FILE NOT FOUND`); continue; }
  const tplContent = fs.readFileSync(tpl, 'utf-8');
  const hasRelated = tplContent.includes('relatedByTag') || tplContent.includes('relatedSection') || tplContent.includes('findRelated(');
  const hasImport = tplContent.includes('findByTag') || tplContent.includes('findRelated');
  console.log(`  ${tpl}: import=${hasImport}, has_related_section=${hasRelated}`);
}
