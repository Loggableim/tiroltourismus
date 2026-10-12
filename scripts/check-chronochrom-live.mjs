/**
 * Live Chronochrom contrast on each language subdomain (not path-prefixed hub).
 * Fetches each host's /assets/js/tirol.js, evaluates CHRONOCHROM_CORE at key hours,
 * asserts --text vs --bg >= 4.5:1. Per-locale HomepageArt palettes are not modified.
 */
import { chromium } from '/workspace/tirol/review/shots/node_modules/playwright/index.js';

const MIN = 4.5;
const HOURS = [2, 5.5, 7.5, 10, 13, 16.5, 17.5, 18.5, 21.5];
const SITES = [
  { lang: 'de', origin: 'https://de.tiroltourismus.com', path: '/sehenswuerdigkeiten/schloss-ambras/' },
  { lang: 'en', origin: 'https://en.tiroltourismus.com', path: '/sehenswuerdigkeiten/schloss-ambras/' },
  { lang: 'fr', origin: 'https://fr.tiroltourismus.com', path: '/sehenswuerdigkeiten/schloss-ambras/' },
  { lang: 'cs', origin: 'https://cs.tiroltourismus.com', path: '/sehenswuerdigkeiten/schloss-ambras/' },
  { lang: 'nl', origin: 'https://nl.tiroltourismus.com', path: '/sehenswuerdigkeiten/schloss-ambras/' },
  { lang: 'it', origin: 'https://it.tiroltourismus.com', path: '/sehenswuerdigkeiten/schloss-ambras/' },
  { lang: 'es', origin: 'https://es.tiroltourismus.com', path: '/sehenswuerdigkeiten/schloss-ambras/' },
  { lang: 'zh', origin: 'https://cn.tiroltourismus.com', path: '/sehenswuerdigkeiten/schloss-ambras/' },
];

function hexToRgb(hex) {
  hex = String(hex || '').trim();
  if (!hex.startsWith('#')) return null;
  if (hex.length === 4) hex = '#' + [...hex.slice(1)].map((c) => c + c).join('');
  const n = parseInt(hex.slice(1), 16);
  if (Number.isNaN(n)) return null;
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function relLum([r, g, b]) {
  const f = (c) => {
    c /= 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}
function contrast(a, b) {
  const ra = hexToRgb(a);
  const rb = hexToRgb(b);
  if (!ra || !rb) return 0;
  const L1 = relLum(ra);
  const L2 = relLum(rb);
  return (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
}

const browser = await chromium.launch({
  headless: true,
  executablePath: '/usr/bin/google-chrome',
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});

let failed = 0;
const rows = [];

for (const site of SITES) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();
  const url = site.origin + site.path;
  try {
    const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    if (!resp || resp.status() >= 400) {
      await page.goto(site.origin + '/', { waitUntil: 'domcontentloaded', timeout: 45000 });
    }
    await page.waitForTimeout(600);
  } catch (e) {
    console.error(`FAIL ${site.lang}: navigate ${e.message}`);
    failed++;
    await context.close();
    continue;
  }

  for (const hour of HOURS) {
    const sample = await page.evaluate(async (h) => {
      const src = await (await fetch('/assets/js/tirol.js', { cache: 'no-store' })).text();
      const start = src.indexOf('/* CHRONOCHROM_CORE_START');
      const end = src.indexOf('/* CHRONOCHROM_CORE_END');
      if (start < 0 || end < 0) {
        return { error: 'CORE markers missing (deploy without clamp?)', bytes: src.length };
      }
      const core = src.slice(start, end);
      let colors;
      try {
        colors = new Function(core + `\nreturn computeInterpolatedColors(${JSON.stringify(h)});`)();
      } catch (err) {
        return { error: String(err), bytes: src.length };
      }
      document.documentElement.dataset.tod = colors.dominant;
      document.documentElement.style.setProperty('--bg', colors.bg);
      document.documentElement.style.setProperty('--text', colors.text);
      return {
        tod: colors.dominant,
        bg: colors.bg,
        text: colors.text,
        bytes: src.length,
        hasClamp: src.includes('clampChronochromTextContrast'),
      };
    }, hour);

    if (sample.error) {
      console.error(`FAIL ${site.lang} h=${hour}: ${sample.error} (js ${sample.bytes}b)`);
      failed++;
      rows.push({ lang: site.lang, hour, ok: false, ratio: 0 });
      continue;
    }
    const ratio = contrast(sample.bg, sample.text);
    const ok = ratio >= MIN && sample.hasClamp;
    if (!ok) failed++;
    rows.push({
      lang: site.lang,
      hour,
      tod: sample.tod,
      bg: sample.bg,
      text: sample.text,
      ratio,
      ok,
      bytes: sample.bytes,
    });
    console.log(
      `${ok ? 'pass' : 'FAIL'} ${site.lang.padEnd(2)} h=${String(hour).padStart(4)} tod=${String(sample.tod).padEnd(10)} ${ratio.toFixed(2)}:1  ${sample.bg}/${sample.text} clamp=${sample.hasClamp}`
    );
  }
  await context.close();
}

await browser.close();
const worst = rows.filter((r) => r.ratio).sort((a, b) => a.ratio - b.ratio).slice(0, 10);
console.log('\nWorst:');
for (const r of worst) console.log(`  ${r.lang} h=${r.hour} ${r.ratio.toFixed(2)}:1 ${r.bg}/${r.text}`);
console.log(failed ? `\n${failed} failure(s).` : `\nAll live subdomain samples passed (>= ${MIN}:1).`);
process.exit(failed ? 1 : 0);
