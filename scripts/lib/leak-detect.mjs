// Erkennt geleakte LLM-Denkspuren / Meta-Text / Wiederholungsschleifen in übersetztem Content.
export const LEAK_PATTERNS = [
  /\bwe need to\b/i, /\btranslate (?:it |this |the text )?into\b/i, /\bkeep (?:the )?html tags\b/i,
  /\bthe instruction\b/i, /\bno explanations\b/i, /^\s*translation\s*:/im, /\bhere is the (?:translation|translated)\b/i,
  /<\/?think>/i, /DerText\s*:/, /\bthe (?:given|german|original) text\b/i, /\bwe (?:should|must|can) (?:output|produce|translate)\b/i,
  /\boutput (?:only|the) (?:the )?(?:translation|translated)\b/i, /\bas an ai\b/i, /\(Note:\s/i, /<\|(?:start|channel|message|im_start|im_end)\|>/, /```(?:html)?/, /\blet'?s translate\b/i, /\bif you have more (?:text|context)\b/i, /\bthe translation is\b/i,
];
export function repetitionLoop(s, max = 10) {
  const toks = String(s).split(/\s+/).filter(Boolean);
  let run = 1;
  for (let i = 1; i < toks.length; i++) {
    run = toks[i] === toks[i - 1] ? run + 1 : 1;
    if (run > max) return toks[i];
  }
  // Mehrwort-Schleifen (Phrase bis 4 Wörter, >10x hintereinander)
  for (let n = 2; n <= 4; n++) {
    for (let i = 0; i + n * 11 <= toks.length; i++) {
      const p = toks.slice(i, i + n).join(' ');
      let k = 1;
      while (toks.slice(i + k * n, i + (k + 1) * n).join(' ') === p) k++;
      if (k > 10) return p;
    }
  }
  return null;
}
export function detectLeak(value) {
  if (typeof value !== 'string' || value.length < 8) return null;
  for (const re of LEAK_PATTERNS) if (re.test(value)) return `Leak-Muster ${re}`;
  const r = repetitionLoop(value);
  if (r) return `Wiederholungsschleife "${r.slice(0, 40)}"`;
  return null;
}

/** CJK in locales other than zh (e.g. DE file with 厨房). Used by scan-leaks only — not content-gate. */
const CJK_IN_TEXT = /[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]/;
/** Felder mit CJK-Sprachsuffix (z. B. beschreibung_cn) sind legitim chinesisch. */
const CJK_FIELD = /(^|[._])(cn|zh|ja|ko)(\b|\[|\.|$)/i;
export function detectCjkInNonZh(value, lang, field = '') {
  if (lang === 'zh') return null;
  if (field && CJK_FIELD.test(field)) return null;
  if (typeof value !== 'string' || value.length < 2) return null;
  const m = value.match(CJK_IN_TEXT);
  if (!m) return null;
  return `CJK in Nicht-ZH-Locale (z. B. „${m[0]}“)`;
}
export function* walkStrings(obj, p = '') {
  if (typeof obj === 'string') yield [p, obj];
  else if (Array.isArray(obj)) for (let i = 0; i < obj.length; i++) yield* walkStrings(obj[i], `${p}[${i}]`);
  else if (obj && typeof obj === 'object') for (const [k, v] of Object.entries(obj)) yield* walkStrings(v, p ? `${p}.${k}` : k);
}
