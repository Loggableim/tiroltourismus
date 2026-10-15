/**
 * duration.js — Localize German duration strings from the dataset for the UI.
 *
 * The Erlebnisse data (all locales) stores durations in German, e.g.
 *   "1,5 Stunden", "1 Tag", "2 bis 3 Stunden", "ca. 75 Minuten",
 *   "Halbtags bis Ganztags (3 bis 6 Stunden)", "18:00 bis 01:00 Uhr (7 Stunden)"
 *
 * `localizeDuration(raw, locale)` parses number + unit combinations and renders
 * them in the requested language. Anything without a recognisable duration token
 * is returned unchanged, so nothing is ever hidden or invented.
 */

const CONF = {
  de: {
    hour: ['Stunde', 'Stunden'],
    day: ['Tag', 'Tage', 'Tagen'],
    minute: ['Minute', 'Minuten'],
    half: 'Halbtags',
    full: 'Ganztags',
    approx: 'ca.',
    range: 'bis',
    time: 'Uhr',
    decimal: ',',
    space: true,
  },
  en: {
    hour: ['hour', 'hours'],
    day: ['day', 'days'],
    minute: ['minute', 'minutes'],
    half: 'Half-day',
    full: 'Full day',
    approx: 'approx.',
    range: 'to',
    time: '',
    decimal: '.',
    space: true,
  },
  fr: {
    hour: ['heure', 'heures'],
    day: ['jour', 'jours'],
    minute: ['minute', 'minutes'],
    half: 'Demi-journée',
    full: 'Journée complète',
    approx: 'env.',
    range: 'à',
    time: '',
    decimal: ',',
    space: true,
  },
  it: {
    hour: ['ora', 'ore'],
    day: ['giorno', 'giorni'],
    minute: ['minuto', 'minuti'],
    half: 'Mezza giornata',
    full: 'Giornata intera',
    approx: 'ca.',
    range: 'a',
    time: '',
    decimal: ',',
    space: true,
  },
  es: {
    hour: ['hora', 'horas'],
    day: ['día', 'días'],
    minute: ['minuto', 'minutos'],
    half: 'Medio día',
    full: 'Día completo',
    approx: 'aprox.',
    range: 'a',
    time: '',
    decimal: ',',
    space: true,
  },
  nl: {
    hour: ['uur', 'uur'],
    day: ['dag', 'dagen'],
    minute: ['minuut', 'minuten'],
    half: 'Halve dag',
    full: 'Hele dag',
    approx: 'ca.',
    range: 'tot',
    time: '',
    decimal: ',',
    space: true,
  },
  cs: {
    hour: ['hodina', 'hodiny', 'hodin'],
    day: ['den', 'dny', 'dní'],
    minute: ['minuta', 'minuty', 'minut'],
    half: 'Půlden',
    full: 'Celý den',
    approx: 'cca',
    range: 'až',
    time: '',
    decimal: ',',
    space: true,
  },
  zh: {
    hour: ['小时', '小时', '小时'],
    day: ['天', '天', '天'],
    minute: ['分钟', '分钟', '分钟'],
    half: '半天',
    full: '全天',
    approx: '约',
    range: '至',
    time: '',
    decimal: '.',
    space: false,
  },
};

// Fractional German phrases that can follow a parsed duration.
const PHRASES = {
  en: { 'flugzeit': 'flight time', 'auf dem wasser': 'on the water' },
  fr: { 'flugzeit': 'temps de vol', 'auf dem wasser': "sur l'eau" },
  it: { 'flugzeit': 'tempo di volo', 'auf dem wasser': "sull'acqua" },
  es: { 'flugzeit': 'tiempo de vuelo', 'auf dem wasser': 'en el agua' },
  nl: { 'flugzeit': 'vluchttijd', 'auf dem wasser': 'op het water' },
  cs: { 'flugzeit': 'doba letu', 'auf dem wasser': 'na vodě' },
  zh: { 'flugzeit': '飞行时间', 'auf dem wasser': '水上' },
};

const UNIT_RE = /(\d+(?:[.,]\d+)?)\s*(?:(?:–|—|-|bis)\s*(\d+(?:[.,]\d+)?)\s*)?(Stunden|Stunde|Std\.?|Tage|Tagen|Tag|Minuten|Minute|Min\.?|h)(?![0-9A-Za-zÀ-ÿ])/gi;

function unitKind(token) {
  const t = token.toLowerCase();
  if (t.startsWith('stund') || t.startsWith('std') || t === 'h') return 'hour';
  if (t.startsWith('tag')) return 'day';
  return 'minute';
}

function pluralIndex(n, len) {
  if (len <= 1) return 0;
  if (len === 2) return n === 1 ? 0 : 1;
  if (n === 1) return 0;
  if (n > 1 && n < 5) return 1;
  return 2;
}

function fmtNumber(n, cfg) {
  const str = String(n);
  return cfg.decimal === '.' ? str.replace(',', '.') : str.replace('.', ',');
}

function pickUnit(cfg, kind, n) {
  const forms = cfg[kind];
  return forms[pluralIndex(n, forms.length)] || forms[0];
}

export function localizeDuration(raw, locale) {
  if (raw === null || raw === undefined) return raw;
  const value = String(raw);
  const lang = CONF[locale] ? locale : 'en';
  if (lang === 'de') return value;

  const cfg = CONF[lang];
  const sep = cfg.space ? ' ' : '';
  let matched = false;

  let out = value.replace(UNIT_RE, (match, aRaw, bRaw, unitToken) => {
    matched = true;
    const a = parseFloat(aRaw.replace(',', '.'));
    const b = bRaw !== undefined ? parseFloat(bRaw.replace(',', '.')) : null;
    const nForPlural = b !== null ? Math.max(a, b) : a;
    const unit = pickUnit(cfg, unitKind(unitToken), nForPlural);
    if (b !== null) {
      return `${fmtNumber(a, cfg)}–${fmtNumber(b, cfg)}${sep}${unit}`;
    }
    return `${fmtNumber(a, cfg)}${sep}${unit}`;
  });

  const beforePhrase = out;
  out = out
    .replace(/\bhalbtags\b|\bhalber\s+tag\b|\bhalben\s+tag\b/gi, cfg.half)
    .replace(/\bganzt(?:ags|ägig)\b/gi, cfg.full);
  if (out !== beforePhrase) matched = true;

  if (!matched) return value;

  if (PHRASES[lang]) {
    Object.keys(PHRASES[lang]).forEach((de) => {
      out = out.replace(new RegExp(de, 'gi'), PHRASES[lang][de]);
    });
  }

  out = out
    .replace(/\bca\.?|\bcirca\b|\betwa\b/gi, cfg.approx)
    .replace(/\bbis\b/gi, cfg.range)
    .replace(/\buhr\b/gi, cfg.time)
    .replace(/(\d),(\d)/g, (m, a, b) => `${a}${cfg.decimal}${b}`)
    .replace(/\s{2,}/g, ' ')
    .replace(/\s+([,.;:)])/g, '$1')
    .trim();

  if (!cfg.space) out = out.replace(/\s*([至])\s*/g, '$1');

  return out;
}

export default localizeDuration;
