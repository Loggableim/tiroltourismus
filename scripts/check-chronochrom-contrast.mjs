/**
 * Chronochrom WCAG AA contrast check (shared public/assets/js/tirol.js).
 *
 * All language Cloudflare projects (de/en/fr/cs/nl/it/es/zh → *.tiroltourismus.com)
 * ship the SAME Chronochrom core. This script verifies every tod interpolation
 * step for --text vs --bg (>= 4.5:1). It does NOT unify or modify per-locale
 * HomepageArt themes (.art-de, .art-en, …) which keep their own --art-* palettes.
 *
 * Live subdomain verification: scripts/check-chronochrom-live.mjs
 */

import { readFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import vm from 'vm';

const TEXT_MIN = 4.5;
const TEXT2_MIN = 4.5;
const TEXT3_MIN = 4.5;

const tirolPath = join(dirname(fileURLToPath(import.meta.url)), '..', 'public/assets/js/tirol.js');
const src = readFileSync(tirolPath, 'utf8');

const startMarker = '/* CHRONOCHROM_CORE_START';
const endMarker = '/* CHRONOCHROM_CORE_END */';
const start = src.indexOf(startMarker);
const end = src.indexOf(endMarker);
if (start < 0 || end < 0) {
  console.error('CHRONOCHROM_CORE markers not found in tirol.js');
  process.exit(1);
}

function loadChronochrom({ skipClamp = false } = {}) {
  let core = src.slice(start, end).replace(/\/\* CHRONOCHROM_CORE_START[^*]*\*\//, '');
  if (skipClamp) {
    core = core.replace(
      'return clampChronochromTextContrast(result);',
      'return result;'
    );
  }
  const sandbox = {};
  vm.createContext(sandbox);
  vm.runInContext(
    core +
      `
    this.computeInterpolatedColors = computeInterpolatedColors;
    this.contrastRatioHex = contrastRatioHex;
    this.contrastRgbaOnBg = contrastRgbaOnBg;
    this.PHASES = PHASES;
  `,
    sandbox
  );
  return sandbox;
}

const chrono = loadChronochrom();
const chronoRaw = loadChronochrom({ skipClamp: true });

const { computeInterpolatedColors, contrastRatioHex, contrastRgbaOnBg, PHASES } = chrono;

const samples = [];
for (let h = 0; h <= 24; h += 0.25) {
  samples.push({ label: `hour ${h.toFixed(2)}`, hour: h });
}
samples.push({ label: 'override day (noon)', hour: PHASES[3].peak });
samples.push({ label: 'override night (twilight)', hour: PHASES[6].peak });

const rows = [];
let failed = false;

for (const s of samples) {
  const colors = computeInterpolatedColors(s.hour);
  const textRatio = contrastRatioHex(colors.bg, colors.text);
  const text2Ratio = contrastRgbaOnBg(colors.bg, colors.text2);
  const text3Ratio = contrastRgbaOnBg(colors.bg, colors.text3);

  const okText = textRatio >= TEXT_MIN;
  const okText2 = text2Ratio >= TEXT2_MIN;
  const okText3 = text3Ratio >= TEXT3_MIN;
  if (!okText) failed = true;

  rows.push({
    label: s.label,
    phase: colors.dominant,
    bg: colors.bg,
    text: colors.text,
    textRatio,
    text2Ratio,
    text3Ratio,
    ok: okText,
    okMuted: okText2 && okText3,
  });
}

rows.sort((a, b) => a.textRatio - b.textRatio);

console.log('Chronochrom contrast check (WCAG AA: --text vs --bg >= 4.5:1; text2/text3 shown for reference)\n');
console.log('Worst samples by --text contrast:');
console.log(
  'label'.padEnd(28) +
    'phase'.padEnd(12) +
    'text'.padEnd(8) +
    'text2'.padEnd(8) +
    'text3'.padEnd(8) +
    'bg'.padEnd(10) +
    'ok'
);
for (const r of rows.slice(0, 12)) {
  console.log(
    r.label.padEnd(28) +
      r.phase.padEnd(12) +
      r.textRatio.toFixed(2).padStart(6) +
      r.text2Ratio.toFixed(2).padStart(7) +
      r.text3Ratio.toFixed(2).padStart(7) +
      (' ' + r.bg).padEnd(10) +
      (r.ok ? 'pass' : 'FAIL')
  );
}

const worst = rows[0];
console.log(
  `\nMinimum --text contrast: ${worst.textRatio.toFixed(3)}:1 @ ${worst.label} (${worst.bg} / ${worst.text})`
);

const h175 = 17.5;
const before = chronoRaw.computeInterpolatedColors(h175);
const after = computeInterpolatedColors(h175);
const beforeRatio = chronoRaw.contrastRatioHex(before.bg, before.text);
const afterRatio = contrastRatioHex(after.bg, after.text);
console.log(
  `\nHour 17.5 (afternoon↔sunset blend): text contrast ${beforeRatio.toFixed(2)}:1 → ${afterRatio.toFixed(2)}:1`
);
console.log(`  before: bg ${before.bg} text ${before.text}`);
console.log(`  after:  bg ${after.bg} text ${after.text}`);

const mutedFails = rows.filter((r) => !r.okMuted);
if (mutedFails.length) {
  console.log(
    `\nNote: ${mutedFails.length} sample(s) have text2/text3 composite < ${TEXT2_MIN}:1 / ${TEXT3_MIN}:1 (informational).`
  );
}

if (failed) {
  const bad = rows.filter((r) => !r.ok);
  console.error(`\n${bad.length} sample(s) failed --text contrast (need >= ${TEXT_MIN}:1).`);
  process.exit(1);
}

console.log(`\nAll ${rows.length} samples passed.`);
