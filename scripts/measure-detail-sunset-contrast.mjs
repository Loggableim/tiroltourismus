/**
 * Live Schloss Ambras detail page: force Chronochrom sunset (h=18.5), measure
 * WCAG contrast on hero/info selectors, screenshot + JSON report.
 */
import { writeFileSync, mkdirSync, readFileSync } from 'fs';
import pkg from '/workspace/tirol/review/shots/node_modules/playwright/index.js';

const { chromium } = pkg;

const MIN_RATIO = 4.5;
const SUNSET_HOUR = 18.5;
const PATH = '/sehenswuerdigkeiten/schloss-ambras/';
const OUT_DIR = '/workspace/tirol/review/shots';

const SITES = [
  { lang: 'de', origin: 'https://de.tiroltourismus.com' },
  { lang: 'en', origin: 'https://en.tiroltourismus.com' },
  { lang: 'fr', origin: 'https://fr.tiroltourismus.com' },
  { lang: 'cs', origin: 'https://cs.tiroltourismus.com' },
  { lang: 'nl', origin: 'https://nl.tiroltourismus.com' },
  { lang: 'it', origin: 'https://it.tiroltourismus.com' },
  { lang: 'es', origin: 'https://es.tiroltourismus.com' },
  { lang: 'zh', origin: 'https://cn.tiroltourismus.com' },
];

const SCREENSHOT_LANGS = new Set(['de', 'fr', 'zh']);

const SELECTORS = [
  { id: 'hero-loc', selector: '.sec-custom-hero-loc', bgHint: 'hero' },
  { id: 'hero-sub', selector: '.sec-custom-hero-sub', bgHint: 'hero' },
  { id: 'hero-cat', selector: '.sec-custom-hero-cat', bgHint: 'hero' },
  { id: 'info-label', selector: '.sec-custom-info-label', bgHint: 'info-item' },
];

const langFilter = process.argv
  .find((a) => a.startsWith('--langs='))
  ?.split('=')[1]
  ?.split(',')
  .map((s) => s.trim())
  .filter(Boolean);

const jsArg = process.argv.find((a) => a.startsWith('--js='));
const localJsPath = jsArg ? jsArg.slice('--js='.length) : null;
let injectedTirolSrc = null;
if (localJsPath) {
  injectedTirolSrc = readFileSync(localJsPath, 'utf8');
}

const sitesToRun = langFilter ? SITES.filter((s) => langFilter.includes(s.lang)) : SITES;

mkdirSync(OUT_DIR, { recursive: true });

const browser = await chromium.launch({
  headless: true,
  executablePath: '/usr/bin/google-chrome',
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});

const report = {
  generatedAt: new Date().toISOString(),
  sunsetHour: SUNSET_HOUR,
  minRatio: MIN_RATIO,
  jsSource: localJsPath || 'live:/assets/js/tirol.js',
  langs: {},
};

for (const site of sitesToRun) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  const url = site.origin + PATH;
  const langEntry = { url, sunset: null, elements: [], error: null };

  try {
    const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    if (!resp || resp.status() >= 400) {
      await page.goto(site.origin + '/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    }
    await page.waitForSelector('.sec-custom-hero', { timeout: 30000 }).catch(() => {});
    await page.waitForTimeout(800);

    const sunsetMeta = await page.evaluate(
      async ({ hour, tirolSrc }) => {
      const src =
        tirolSrc != null
          ? tirolSrc
          : await (await fetch('/assets/js/tirol.js', { cache: 'no-store' })).text();
      const start = src.indexOf('/* CHRONOCHROM_CORE_START');
      const end = src.indexOf('/* CHRONOCHROM_CORE_END');
      if (start < 0 || end < 0) {
        return { error: 'CHRONOCHROM_CORE markers missing', bytes: src.length };
      }
      const core = src.slice(start, end);
      let colors;
      try {
        if (typeof window.computeInterpolatedColors === 'function') {
          colors = window.computeInterpolatedColors(hour);
        } else {
          colors = new Function(core + `\nreturn computeInterpolatedColors(${JSON.stringify(hour)});`)();
        }
      } catch (err) {
        return { error: String(err), bytes: src.length };
      }

      const root = document.documentElement;
      root.dataset.tod = colors.dominant || 'sunset';
      const map = {
        '--bg': colors.bg,
        '--bg2': colors.bg2,
        '--text': colors.text,
        '--text2': colors.text2,
        '--text3': colors.text3,
        '--pink': colors.pink,
        '--pink-dark': colors.pinkDark,
        '--pink-glow': colors.pinkGlow,
        '--gold': colors.gold,
        '--gold-light': colors.goldLight,
        '--gold-glow': colors.goldGlow,
        '--gold-soft': colors.goldSoft,
        '--glass': colors.glass,
        '--glass-border': colors.glassBorder,
        '--surface': colors.surface,
        '--surface-hover': colors.surfaceHover,
        '--yellow': colors.yellow,
        '--blue': colors.blue,
        '--tirol-pink': colors.pink,
        '--tirol-pink-dark': colors.pinkDark,
        '--tirol-pink-glow': colors.pinkGlow,
        '--pop-yellow': colors.yellow,
        '--ikea-blue': colors.blue,
        '--purple': colors.purple || '#8B5CF6',
        '--pop-purple': colors.purple || '#8B5CF6',
      };
      for (const key of Object.keys(map)) {
        if (map[key] != null) root.style.setProperty(key, map[key]);
      }
      root.classList.add('chrono-active');

      return {
        bytes: src.length,
        hasClamp: src.includes('clampChronochromTextContrast'),
        text2Min: (src.match(/CHRONO_TEXT2_MIN\s*=\s*([\d.]+)/) || [])[1],
        text3Min: (src.match(/CHRONO_TEXT3_MIN\s*=\s*([\d.]+)/) || [])[1],
        dominant: colors.dominant,
        bg: colors.bg,
        text2: colors.text2,
        text3: colors.text3,
        purple: colors.purple,
      };
    },
      { hour: SUNSET_HOUR, tirolSrc: injectedTirolSrc }
    );

    if (sunsetMeta.error) {
      langEntry.error = sunsetMeta.error;
      report.langs[site.lang] = langEntry;
      console.error(`FAIL ${site.lang}: ${sunsetMeta.error}`);
      await context.close();
      continue;
    }
    langEntry.sunset = sunsetMeta;

    const measurements = await page.evaluate(
      ({ selectors, minRatio }) => {
        function parseCssColor(str) {
          str = String(str || '').trim();
          if (!str || str === 'transparent') return null;
          let m = str.match(/^#([0-9a-f]{3,8})$/i);
          if (m) {
            let h = m[1];
            if (h.length === 3) h = [...h].map((c) => c + c).join('');
            const n = parseInt(h.slice(0, 6), 16);
            return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255, a: 1 };
          }
          m = str.match(/rgba?\(([^)]+)\)/);
          if (m) {
            const parts = m[1].split(',').map((p) => p.trim());
            const r = +parts[0];
            const g = +parts[1];
            const b = +parts[2];
            const a = parts.length > 3 ? +parts[3] : 1;
            return { r, g, b, a: Number.isFinite(a) ? a : 1 };
          }
          return null;
        }

        function relLum(r, g, b) {
          const lin = (c) => {
            c /= 255;
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
          };
          return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
        }

        function contrastRgb(fg, bg) {
          const comp =
            fg.a >= 1
              ? fg
              : {
                  r: fg.r * fg.a + bg.r * (1 - fg.a),
                  g: fg.g * fg.a + bg.g * (1 - fg.a),
                  b: fg.b * fg.a + bg.b * (1 - fg.a),
                  a: 1,
                };
          const L1 = relLum(comp.r, comp.g, comp.b);
          const L2 = relLum(bg.r, bg.g, bg.b);
          return (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
        }

        function colorToCss(c) {
          if (!c) return 'n/a';
          if (c.a >= 1) return `rgb(${Math.round(c.r)},${Math.round(c.g)},${Math.round(c.b)})`;
          return `rgba(${Math.round(c.r)},${Math.round(c.g)},${Math.round(c.b)},${c.a.toFixed(3)})`;
        }

        function heroEffectiveBg() {
          const hero = document.querySelector('.sec-custom-hero');
          if (hero && hero.classList.contains('sec-custom-hero-has-img')) {
            return { r: 51, g: 51, b: 51, a: 1 };
          }
          const varBg = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();
          const fromVar = parseCssColor(varBg);
          if (fromVar) return { ...fromVar, a: 1 };
          if (hero) {
            const bg = parseCssColor(getComputedStyle(hero).backgroundColor);
            if (bg && bg.a > 0.01) return { ...bg, a: 1 };
          }
          let el = hero || document.body;
          while (el) {
            const bg = parseCssColor(getComputedStyle(el).backgroundColor);
            if (bg && bg.a > 0.01) return { ...bg, a: 1 };
            el = el.parentElement;
          }
          return { r: 255, g: 255, b: 255, a: 1 };
        }

        function infoItemBg(el) {
          const item = el.closest('.sec-custom-info-item');
          if (item) {
            const bg = parseCssColor(getComputedStyle(item).backgroundColor);
            if (bg && bg.a > 0.01) return { ...bg, a: 1 };
          }
          const varBg = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();
          const parsed = parseCssColor(varBg);
          if (parsed) return { ...parsed, a: 1 };
          return { r: 255, g: 255, b: 255, a: 1 };
        }

        const out = [];
        for (const spec of selectors) {
          const nodes = document.querySelectorAll(spec.selector);
          const node = nodes[0];
          if (!node) {
            out.push({ id: spec.id, selector: spec.selector, missing: true });
            continue;
          }
          const fg = parseCssColor(getComputedStyle(node).color);
          const bg =
            spec.bgHint === 'hero' ? heroEffectiveBg() : infoItemBg(node);
          const ratio = fg && bg ? contrastRgb(fg, bg) : 0;
          out.push({
            id: spec.id,
            selector: spec.selector,
            text: (node.textContent || '').trim().slice(0, 48),
            fg: colorToCss(fg),
            bg: colorToCss(bg),
            ratio,
            pass: ratio >= minRatio,
            count: nodes.length,
          });
        }
        return out;
      },
      { selectors: SELECTORS, minRatio: MIN_RATIO }
    );

    langEntry.elements = measurements;

    if (SCREENSHOT_LANGS.has(site.lang)) {
      const shotPath = `${OUT_DIR}/after-sunset-v2-${site.lang}.png`;
      const hero = page.locator('.sec-custom-hero');
      const info = page.locator('.sec-custom-info-section');
      if (await hero.count()) {
        await hero.scrollIntoViewIfNeeded();
        const box = await hero.boundingBox();
        const infoBox = (await info.count()) ? await info.boundingBox() : null;
        let clip = box;
        if (box && infoBox) {
          clip = {
            x: Math.min(box.x, infoBox.x),
            y: box.y,
            width: Math.max(box.x + box.width, infoBox.x + infoBox.width) - Math.min(box.x, infoBox.x),
            height: infoBox.y + infoBox.height - box.y,
          };
        }
        await page.screenshot({ path: shotPath, clip });
      } else {
        await page.screenshot({ path: shotPath, fullPage: true });
      }
      langEntry.screenshot = shotPath;
    }
  } catch (e) {
    langEntry.error = e.message;
    console.error(`FAIL ${site.lang}: ${e.message}`);
  }

  report.langs[site.lang] = langEntry;
  await context.close();
}

await browser.close();

const reportPath = `${OUT_DIR}/after-sunset-v2-report.json`;
writeFileSync(reportPath, JSON.stringify(report, null, 2));

console.log(`\nSchloss Ambras sunset contrast (h=${SUNSET_HOUR}, need >= ${MIN_RATIO}:1)\n`);
console.log(
  'lang'.padEnd(4) +
    'element'.padEnd(14) +
    'ratio'.padStart(7) +
    '  pass  fg'.padEnd(28) +
    'bg'
);
for (const site of sitesToRun) {
  const entry = report.langs[site.lang];
  if (entry?.error) {
    console.log(`${site.lang.padEnd(4)} ERROR ${entry.error}`);
    continue;
  }
  for (const el of entry?.elements || []) {
    if (el.missing) {
      console.log(`${site.lang.padEnd(4)} ${el.id.padEnd(12)}  —     missing`);
      continue;
    }
    console.log(
      `${site.lang.padEnd(4)} ${el.id.padEnd(12)} ${el.ratio.toFixed(2).padStart(6)}:1  ${(el.pass ? 'yes' : 'NO ').padEnd(4)}  ${el.fg}  ${el.bg}`
    );
  }
  if (entry?.sunset) {
    console.log(
      `     live js ${entry.sunset.bytes}b clamp=${entry.sunset.hasClamp} TEXT2_MIN=${entry.sunset.text2Min ?? '?'} TEXT3_MIN=${entry.sunset.text3Min ?? '?'} tod=${entry.sunset.dominant}`
    );
  }
}
console.log(`\nReport: ${reportPath}`);
