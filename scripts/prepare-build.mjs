/**
 * prepare-build.mjs
 * Stasht DE-Root-Seiten (src/pages/*) für Single-Lang-Builds von Nicht-DE-Sprachen,
 * damit die [...locale]-Routen die Root-Pfade übernehmen können.
 *
 * Usage:
 *   BUILD_LANGS=cs node scripts/prepare-build.mjs           → stash DE pages
 *   node scripts/prepare-build.mjs --restore                → restore DE pages
 *
 * KEEP: [...locale]/, 404.astro, 500.astro (bleiben in allen Builds)
 */
import fs from 'fs';
import path from 'path';

const PAGES = 'src/pages';
const STASH = '.stash-de-pages';
const KEEP = new Set(['[...locale]', '404.astro', '500.astro']);

const restore = process.argv.includes('--restore');
const buildLangs = (process.env.BUILD_LANGS || '').split(',').map(s => s.trim()).filter(Boolean);
const isSingleNonDe = buildLangs.length === 1 && buildLangs[0] !== 'de';

if (restore) {
  if (!fs.existsSync(STASH)) {
    console.log('prepare-build: nothing to restore');
    process.exit(0);
  }
  let n = 0;
  for (const entry of fs.readdirSync(STASH)) {
    fs.renameSync(path.join(STASH, entry), path.join(PAGES, entry));
    n++;
  }
  fs.rmdirSync(STASH);
  console.log(`prepare-build: restored ${n} entries from stash`);
  process.exit(0);
}

if (!isSingleNonDe) {
  console.log(`prepare-build: no stash needed (BUILD_LANGS=${buildLangs.join(',') || 'multi/dev'})`);
  process.exit(0);
}

if (fs.existsSync(STASH)) {
  console.error('prepare-build: ERROR — stash dir already exists. Run with --restore first.');
  process.exit(1);
}

fs.mkdirSync(STASH, { recursive: true });
let n = 0;
for (const entry of fs.readdirSync(PAGES)) {
  if (KEEP.has(entry)) continue;
  fs.renameSync(path.join(PAGES, entry), path.join(STASH, entry));
  n++;
}
console.log(`prepare-build: stashed ${n} DE root entries (BUILD_LANGS=${buildLangs[0]})`);
