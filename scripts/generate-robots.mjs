/**
 * generate-robots.mjs
 * Generiert die korrekte robots.txt für den aktuellen Build.
 *
 * Single-Lang-Build (BUILD_LANGS=cs): Sitemap zeigt auf cs.tiroltourismus.com
 * Multi-Lang/Dev: Sitemap zeigt auf tiroltourismus.com (Landing)
 */
import fs from 'fs';
import path from 'path';

const buildLangs = (process.env.BUILD_LANGS || '').split(',').map(s => s.trim()).filter(Boolean);
const isSingleLang = buildLangs.length === 1;

const LANG_DOMAINS = {
  de: 'https://de.tiroltourismus.com',
  en: 'https://en.tiroltourismus.com',
  fr: 'https://fr.tiroltourismus.com',
  cs: 'https://cs.tiroltourismus.com',
  nl: 'https://nl.tiroltourismus.com',
  it: 'https://it.tiroltourismus.com',
  es: 'https://es.tiroltourismus.com',
  zh: 'https://cn.tiroltourismus.com',
};

const domain = isSingleLang ? (LANG_DOMAINS[buildLangs[0]] || 'https://tiroltourismus.com') : 'https://tiroltourismus.com';

const content = `# robots.txt for ${domain.replace('https://', '')}
User-agent: *
Allow: /

Sitemap: ${domain}/sitemap-index.xml
`;

fs.writeFileSync(path.join('public', 'robots.txt'), content);
console.log(`robots.txt → ${domain}/sitemap-index.xml`);
