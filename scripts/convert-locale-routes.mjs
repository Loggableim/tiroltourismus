/**
 * convert-locale-routes.mjs
 * Konvertiert src/pages/[locale]/ → src/pages/[...locale]/ für Root-Serving.
 *
 * Änderungen pro Datei:
 * 1. getStaticPaths → localeParams() (Single-Lang: [undefined] für Root, [] für DE)
 * 2. const { locale } = Astro.params → const locale = Astro.params.locale || DEFAULT_LOCALE
 * 3. [slug]-Loops: for (const loc of locales) { const locale = loc || DEFAULT_LOCALE; ... params: { locale: loc, slug } }
 * 4. Imports: localeParams + DEFAULT_LOCALE ergänzen
 */
import fs from 'fs';
import path from 'path';

const DIR = 'src/pages/[...locale]';
if (!fs.existsSync(DIR)) {
  console.error('ERROR: ' + DIR + ' not found — run git mv first');
  process.exit(1);
}

const files = [];
function walk(d) {
  for (const e of fs.readdirSync(d)) {
    const p = path.join(d, e);
    if (fs.statSync(p).isDirectory()) walk(p);
    else if (p.endsWith('.astro')) files.push(p);
  }
}
walk(DIR);

let changed = 0;
const report = [];

for (const f of files) {
  let c = fs.readFileSync(f, 'utf-8');
  const before = c;
  const notes = [];

  // ── 1. getStaticPaths patterns ──
  // Pattern B/D: LANGUAGES_READY.filter((x) => x !== 'de').map((locale) => ({ params: { locale } }))
  if (/return LANGUAGES_READY\.filter\(\((?:locale|l|c)\) => (?:locale|l|c) !== 'de'\)\.map\(\((?:locale|l)\) => \(\{ params: \{ locale \} \}\)\);/.test(c)) {
    c = c.replace(
      /return LANGUAGES_READY\.filter\(\((?:locale|l|c)\) => (?:locale|l|c) !== 'de'\)\.map\(\((?:locale|l)\) => \(\{ params: \{ locale \} \}\)\);/g,
      'return localeParams().map(locale => ({ params: { locale } }));'
    );
    notes.push('pattern-B');
  }
  // Pattern A: LANGUAGES_READY.map(locale => ({ params: { locale } }))
  if (/return LANGUAGES_READY\.map\(locale => \(\{ params: \{ locale \} \}\)\);/.test(c)) {
    c = c.replace(
      /return LANGUAGES_READY\.map\(locale => \(\{ params: \{ locale \} \}\)\);/g,
      'return localeParams().map(locale => ({ params: { locale } }));'
    );
    notes.push('pattern-A');
  }
  // Pattern C: const locales = LANGUAGES_READY.filter((l) => l !== 'de');
  if (/const locales = LANGUAGES_READY\.filter\(\(l\) => l !== 'de'\);/.test(c)) {
    c = c.replace(
      /const locales = LANGUAGES_READY\.filter\(\(l\) => l !== 'de'\);/g,
      'const locales = localeParams();'
    );
    // Loop variable rename + data-locale resolution
    c = c.replace(
      /for \(const locale of locales\) \{/g,
      'for (const loc of locales) {\n    const locale = loc || DEFAULT_LOCALE;'
    );
    // params: { locale, slug → params: { locale: loc, slug
    c = c.replace(/params: \{ locale, slug:/g, 'params: { locale: loc, slug:');
    notes.push('pattern-C');
  }

  // ── 2. locale extraction ──
  if (/const \{ locale \} = Astro\.params;/.test(c)) {
    c = c.replace(
      /const \{ locale \} = Astro\.params;/g,
      'const locale = Astro.params.locale || DEFAULT_LOCALE;'
    );
    notes.push('locale-extract');
  }

  // ── 3. Imports ──
  c = c.replace(
    /import \{([^}]*)\} from '((?:\.\.\/)+lib\/languages\.js)';/,
    (m, names, p) => {
      const set = new Set(names.split(',').map(s => s.trim()).filter(Boolean));
      set.add('localeParams');
      set.add('DEFAULT_LOCALE');
      return `import { ${[...set].join(', ')} } from '${p}';`;
    }
  );

  if (c !== before) {
    fs.writeFileSync(f, c);
    changed++;
    report.push(`${f}  [${notes.join(', ')}]`);
  } else {
    report.push(`${f}  [NO CHANGE — CHECK MANUALLY]`);
  }
}

console.log(report.join('\n'));
console.log(`\n${changed}/${files.length} files changed`);
