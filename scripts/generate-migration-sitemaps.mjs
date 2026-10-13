/**
 * generate-migration-sitemaps.mjs
 * Generiert Migration-Sitemaps für die Landing-Domain (tiroltourismus.com).
 *
 * Zweck: Google soll die ALTEN URLs schnell recrawlen und die 301-Redirects
 * zu den Sprach-Subdomains erkennen (GSC-freundliche Migration).
 *
 * Output:
 *   landing/public/sitemap-migration-0.xml  (erste 10k alte URLs)
 *   landing/public/sitemap-migration-1.xml  (Rest)
 *
 * Die Dateien bleiben abrufbar, werden aber nicht beworben.
 * Dieses Script schreibt sitemap-index.xml nicht neu und trägt die
 * Migration-Dateien nicht wieder in den Index ein.
 * Sprach-Subdomains zeigen auf ihre eigene Astro-sitemap-index.xml.
 *
 * Die hreflang-Links werden entfernt — die alten URLs sind reine Redirects,
 * die neuen hreflang-Beziehungen leben in den Subdomain-Sitemaps.
 */
import fs from 'fs';
import path from 'path';

const SRC = ['migration-data/old-sitemap-0.xml', 'migration-data/old-sitemap-1.xml'];
const OUT_DIR = 'landing/public';
const CHUNK = 10000;

// Alle alten URLs einsammeln
const urls = [];
for (const f of SRC) {
  if (!fs.existsSync(f)) {
    console.error(`ERROR: ${f} not found`);
    process.exit(1);
  }
  const content = fs.readFileSync(f, 'utf-8');
  for (const m of content.matchAll(/<loc>([^<]+)<\/loc>/g)) {
    urls.push(m[1]);
  }
}

// Dedupe + sort
const unique = [...new Set(urls)].sort();
console.log(`Migration URLs: ${urls.length} total, ${unique.length} unique`);

// Chunks schreiben
const chunks = [];
for (let i = 0; i < unique.length; i += CHUNK) {
  const slice = unique.slice(i, i + CHUNK);
  const idx = chunks.length;
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${slice.map(u => `  <url><loc>${u}</loc></url>`).join('\n')}
</urlset>
`;
  const out = path.join(OUT_DIR, `sitemap-migration-${idx}.xml`);
  fs.writeFileSync(out, xml);
  chunks.push(`sitemap-migration-${idx}.xml`);
  console.log(`  ${out}: ${slice.length} URLs`);
}

console.log(`Migration XML written (${chunks.length} files). Not added to sitemap-index.xml.`);
console.log('DONE');
