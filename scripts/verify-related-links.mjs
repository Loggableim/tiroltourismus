/**
 * Verify related-links-card hrefs in dist HTML exist on disk.
 * Usage: node scripts/verify-related-links.mjs [distDir] [maxPages]
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const distDir = path.resolve(process.argv[2] || path.join(__dirname, '..', 'dist'));
const maxPages = Number(process.argv[3] || 3);

function hrefToFsPath(href) {
  let p = href.trim();
  if (p.startsWith('http://') || p.startsWith('https://')) {
    try {
      p = new URL(p).pathname;
    } catch {
      return null;
    }
  }
  if (!p.startsWith('/')) return null;
  p = p.replace(/\/+$/, '');
  const rel = p.slice(1);
  return path.join(distDir, rel, 'index.html');
}

function walkHtml(dir, out = []) {
  if (!fs.existsSync(dir)) return out;
  for (const name of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, name.name);
    if (name.isDirectory()) walkHtml(full, out);
    else if (name.name.endsWith('.html')) out.push(full);
  }
  return out;
}

const cardRe = /class="related-links-card"[^>]*href="([^"]+)"/g;
const sectionRe = /class="related-links\b/;

const htmlFiles = walkHtml(distDir);
const withRelated = htmlFiles.filter((f) => sectionRe.test(fs.readFileSync(f, 'utf8')));

if (withRelated.length === 0) {
  console.error('No HTML files with class="related-links" under', distDir);
  process.exit(1);
}

const picked = withRelated.slice(0, maxPages);
let failed = false;

for (const file of picked) {
  const html = fs.readFileSync(file, 'utf8');
  const hrefs = [...html.matchAll(cardRe)].map((m) => m[1]);
  const relPage = path.relative(distDir, file);
  console.log('\n===', relPage, `(${hrefs.length} card hrefs) ===`);
  for (const href of hrefs.slice(0, 5)) {
    const target = hrefToFsPath(href);
    if (!target) {
      console.log('  SKIP external or non-path:', href);
      continue;
    }
    const ok = fs.existsSync(target);
    console.log(`  ${ok ? 'OK' : 'MISSING'} ${href} -> ${path.relative(distDir, target)}`);
    if (!ok) failed = true;
  }
}

if (failed) process.exit(1);
console.log('\nVerified', picked.length, 'pages (sample hrefs).');
