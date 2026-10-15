/** Build-time related entries + contextual description links (module cache). */
import fs from 'fs';
import path from 'path';
import { BUILD_LANGS, DEFAULT_LOCALE, localeParams, localePrefix } from './languages.js';

const DATA_DIR = path.resolve(process.cwd(), 'src/data');

function getDataDir(locale = 'de') {
  if (!locale || locale === 'de') return DATA_DIR;
  return path.join(DATA_DIR, locale);
}

function readCollection(name, locale = 'de') {
  const dir = path.join(getDataDir(locale), name);
  if (!fs.existsSync(dir)) return [];
  const entries = [];
  for (const item of fs.readdirSync(dir, { withFileTypes: true })) {
    if (!item.isDirectory()) continue;
    const jsonPath = path.join(dir, item.name, 'index.json');
    if (!fs.existsSync(jsonPath)) continue;
    try {
      const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
      if (data.status === 'archived') continue;
      entries.push({ slug: item.name, entry: data });
    } catch {
      /* skip invalid JSON */
    }
  }
  return entries;
}

function isPublished(entry) {
  return !entry.status || entry.status === 'published';
}

const LINK_COLLECTIONS = [
  'unterkuenfte',
  'sehenswuerdigkeiten',
  'gastro',
  'camping',
  'erlebnisse',
];

const DETAIL_COLLECTIONS = [
  ...LINK_COLLECTIONS,
  'orte',
  'regionen',
  'events',
  'magazin',
];

const COLLECTION_EMOJI = {
  sehenswuerdigkeiten: '🏛️',
  gastro: '🍽️',
  unterkuenfte: '🏨',
  camping: '🏕️',
  erlebnisse: '🎯',
  orte: '🏘️',
  events: '🎪',
  regionen: '🏔️',
  magazin: '📰',
};

const HEADINGS = {
  de: { same: 'In der Nähe', cross: 'Mehr entdecken in der Region' },
  en: { same: 'Nearby', cross: 'Discover more in the area' },
  fr: { same: 'À proximité', cross: 'Découvrir plus dans la région' },
  it: { same: 'Nelle vicinanze', cross: 'Scopri di più nella regione' },
  es: { same: 'Cerca de aquí', cross: 'Descubre más en la región' },
  zh: { same: '附近推荐', cross: '探索周边更多' },
  nl: { same: 'In de buurt', cross: 'Meer ontdekken in de regio' },
  cs: { same: 'V okolí', cross: 'Objevte více v regionu' },
};

let _indexBuilt = false;
/** @type {Map<string, { byKey: Map<string, object>, grid: Map<string, string[]>, names: object[] }>} */
const _localeIndex = new Map();

function builtLocales() {
  return localeParams().map((loc) => loc || DEFAULT_LOCALE);
}

function entryName(entry) {
  return (entry.name || entry.titel || '').trim();
}

function entryHref(locale, collection, slug) {
  const prefix = localePrefix(locale);
  return `${prefix}/${collection}/${slug}/`;
}

function haversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function gridKey(lat, lng, cellDeg = 0.1) {
  return `${Math.floor(lat / cellDeg)}_${Math.floor(lng / cellDeg)}`;
}

function hashSeed(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function seededShuffle(items, seedKey) {
  const arr = [...items];
  let s = hashSeed(seedKey);
  for (let i = arr.length - 1; i > 0; i--) {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    const j = s % (i + 1);
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

export function getLinkSeed() {
  if (typeof process !== 'undefined' && process.env.LINK_SEED) {
    return process.env.LINK_SEED;
  }
  const now = new Date();
  const d = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()));
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const week = Math.ceil(((d - yearStart) / 86400000 + 1) / 7);
  return `${d.getUTCFullYear()}-W${String(week).padStart(2, '0')}`;
}

function ensureIndex() {
  if (_indexBuilt) return;
  for (const locale of builtLocales()) {
    if (!BUILD_LANGS.includes(locale)) continue;
    const byKey = new Map();
    const grid = new Map();
    const names = [];

    for (const collection of DETAIL_COLLECTIONS) {
      const entries = readCollection(collection, locale).filter((e) => isPublished(e.entry));
      for (const { slug, entry } of entries) {
        const name = entryName(entry);
        const key = `${collection}__${slug}`;
        const rec = {
          collection,
          slug,
          locale,
          name,
          ort: (entry.ort || '').toLowerCase(),
          region: (entry.region || '').toLowerCase(),
          koordinaten: entry.koordinaten,
          kurzbeschreibung: entry.kurzbeschreibung || '',
          href: entryHref(locale, collection, slug),
          emoji: entry.emoji || COLLECTION_EMOJI[collection] || '📍',
        };
        byKey.set(key, rec);
        if (name.length >= 6 && LINK_COLLECTIONS.includes(collection)) {
          names.push({
            name,
            href: rec.href,
            collection,
            slug,
            len: name.length,
          });
        }
        const k = entry.koordinaten;
        if (k && typeof k.lat === 'number' && typeof k.lng === 'number') {
          const gk = gridKey(k.lat, k.lng);
          if (!grid.has(gk)) grid.set(gk, []);
          grid.get(gk).push(key);
        }
      }
    }
    names.sort((a, b) => b.len - a.len);
    _localeIndex.set(locale, { byKey, grid, names });
  }
  _indexBuilt = true;
}

function getRecord(locale, collection, slug) {
  ensureIndex();
  return _localeIndex.get(locale)?.byKey.get(`${collection}__${slug}`);
}

function locationScore(from, to) {
  if (from.koordinaten && to.koordinaten) {
    return haversineKm(
      from.koordinaten.lat,
      from.koordinaten.lng,
      to.koordinaten.lat,
      to.koordinaten.lng,
    );
  }
  if (from.ort && to.ort && from.ort === to.ort) return 5;
  if (from.region && to.region && from.region === to.region) return 15;
  return Infinity;
}

function collectNearby(from, locale, { sameCollection, limitPool = 20 }) {
  ensureIndex();
  const store = _localeIndex.get(locale);
  if (!store || !from) return [];

  const candidates = [];
  const seen = new Set([`${from.collection}__${from.slug}`]);

  if (from.koordinaten) {
    const { lat, lng } = from.koordinaten;
    const cell = 0.1;
    const cx = Math.floor(lat / cell);
    const cy = Math.floor(lng / cell);
    for (let dx = -2; dx <= 2; dx++) {
      for (let dy = -2; dy <= 2; dy++) {
        const keys = store.grid.get(`${cx + dx}_${cy + dy}`) || [];
        for (const key of keys) {
          if (seen.has(key)) continue;
          const rec = store.byKey.get(key);
          if (!rec) continue;
          if (sameCollection && rec.collection !== from.collection) continue;
          if (!sameCollection && rec.collection === from.collection) continue;
          if (!LINK_COLLECTIONS.includes(rec.collection)) continue;
          const dist = locationScore(from, rec);
          if (!Number.isFinite(dist)) continue;
          seen.add(key);
          candidates.push({ ...rec, dist_km: dist });
        }
      }
    }
  }

  if (candidates.length < limitPool) {
    for (const rec of store.byKey.values()) {
      const key = `${rec.collection}__${rec.slug}`;
      if (seen.has(key)) continue;
      if (sameCollection && rec.collection !== from.collection) continue;
      if (!sameCollection && rec.collection === from.collection) continue;
      if (!LINK_COLLECTIONS.includes(rec.collection)) continue;
      const dist = locationScore(from, rec);
      if (!Number.isFinite(dist)) continue;
      seen.add(key);
      candidates.push({ ...rec, dist_km: dist });
      if (candidates.length >= limitPool * 3) break;
    }
  }

  candidates.sort((a, b) => a.dist_km - b.dist_km);
  return candidates.slice(0, limitPool);
}

function pickRotated(candidates, collection, slug, take) {
  if (!candidates.length) return [];
  const seed = `${getLinkSeed()}:${collection}__${slug}`;
  const shuffled = seededShuffle(candidates, seed);
  return shuffled.slice(0, take).map((c) => ({
    collection: c.collection,
    slug: c.slug,
    href: c.href,
    name: c.name,
    ort: c.ort,
    region: c.region,
    kurzbeschreibung: c.kurzbeschreibung,
    emoji: c.emoji,
    dist_km: c.dist_km,
  }));
}

export function getRelatedForEntry(collection, slug, locale = 'de') {
  const from = getRecord(locale, collection, slug);
  if (!from) {
    return { sameCategory: [], crossCategory: [], headings: HEADINGS[locale] || HEADINGS.de };
  }
  const samePool = collectNearby(from, locale, { sameCollection: true, limitPool: 20 });
  const crossPool = collectNearby(from, locale, { sameCollection: false, limitPool: 20 });
  return {
    sameCategory: pickRotated(samePool, collection, slug, 4),
    crossCategory: pickRotated(crossPool, collection, slug, 4),
    headings: HEADINGS[locale] || HEADINGS.de,
  };
}

const LINK_NAME_SEP = /[a-zA-Z0-9_]/;
// Nicht verlinken, wenn der Treffer Teil einer URL/eines Slugs ist:
// vorne blocken `/`, `.`, `:`, `@`, `-`, `\` — hinten `/`, `:`, `@`, `-`, `\`
// (der Punkt hinten bleibt erlaubt, damit Namen am Satzende verlinkt werden).
const LINK_EDGE_BEFORE = '[\\w./:@\\-\\\\]';
const LINK_EDGE_AFTER = '[\\w/:@\\-\\\\]';

/** Namen, die nie verlinkt werden dürfen (Roh-HTML/Markdown/etc.). */
function isLinkableEntityName(name) {
  if (typeof name !== 'string') return false;
  const trimmed = name.trim();
  if (trimmed.length < 3 || trimmed.length > 80) return false;
  if (/[<>[\]*#|]/.test(trimmed)) return false;
  return LINK_NAME_SEP.test(trimmed);
}

/**
 * Verlinkt Vorkommen von `entities[].name` in Textknoten eines HTML-Strings.
 *
 * Wichtig: Es wird nur EIN Durchlauf über den Originaltext gemacht und alle
 * Kandidaten werden anhand ihrer Positionen ermittelt. Dadurch kann ein bereits
 * erzeugter Link nicht erneut durchsucht werden (verhindert verschachtelte,
 * kaputte Anker wie href="/gastro/<a href="). Treffer innerhalb bestehender
 * Anker oder innerhalb von URLs/Pfaden werden übersprungen.
 *
 * @param {string} html
 * @param {Array<{name: string, href: string}>} entities
 * @param {number} [maxLinks]
 */
export function linkifyHtml(html, entities, maxLinks = 5) {
  if (!html || typeof html !== 'string') return html || '';
  const candidates = (entities || [])
    .filter((ent) => ent && isLinkableEntityName(ent.name) && ent.href)
    .sort((a, b) => b.name.length - a.name.length);
  if (!candidates.length || maxLinks <= 0) return html;

  const parts = html.split(/(<[^>]+>)/g);
  let linked = 0;
  let anchorDepth = 0;
  const out = [];

  for (const seg of parts) {
    if (seg.startsWith('<')) {
      if (/^<a[\s>/]/i.test(seg)) anchorDepth++;
      else if (/^<\/a[\s>]/i.test(seg)) anchorDepth = Math.max(0, anchorDepth - 1);
      out.push(seg);
      continue;
    }
    if (anchorDepth > 0 || linked >= maxLinks) {
      out.push(seg);
      continue;
    }

    const matches = [];
    for (const ent of candidates) {
      const escaped = ent.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      let re;
      try {
        re = new RegExp(`(?<!${LINK_EDGE_BEFORE})(${escaped})(?!${LINK_EDGE_AFTER})`, 'gi');
      } catch {
        continue;
      }
      let m;
      while ((m = re.exec(seg)) !== null) {
        const text = m[0];
        matches.push({ start: m.index, end: m.index + text.length, text, href: ent.href });
        if (m.index === re.lastIndex) re.lastIndex++;
      }
    }
    if (!matches.length) {
      out.push(seg);
      continue;
    }

    matches.sort((a, b) => (b.end - b.start) - (a.end - a.start) || a.start - b.start);
    const chosen = [];
    const budget = maxLinks - linked;
    for (const mt of matches) {
      if (chosen.length >= budget) break;
      if (chosen.some((c) => mt.start < c.end && mt.end > c.start)) continue;
      chosen.push(mt);
    }
    chosen.sort((a, b) => a.start - b.start);

    let cursor = 0;
    let built = '';
    for (const mt of chosen) {
      built += seg.slice(cursor, mt.start);
      built += `<a href="${mt.href}" class="auto-link">${mt.text}</a>`;
      cursor = mt.end;
    }
    built += seg.slice(cursor);
    linked += chosen.length;
    out.push(built);
  }

  return out.join('');
}

export function linkDescriptionText(
  html,
  collection,
  slug,
  locale = 'de',
  maxLinks = 5,
  currentEntry = null,
) {
  if (!html || typeof html !== 'string') return html || '';
  ensureIndex();
  const store = _localeIndex.get(locale);
  if (!store) return html;

  const selfName = (
    currentEntry?.name ||
    currentEntry?.titel ||
    getRecord(locale, collection, slug)?.name ||
    ''
  ).toLowerCase();
  const selfSlug = slug;

  const htmlLower = html.replace(/<[^>]+>/g, ' ').toLowerCase();
  const linkableNames = store.names.filter((ent) => {
    if (ent.slug === selfSlug && ent.collection === collection) return false;
    if (!isLinkableEntityName(ent.name)) return false;
    if (selfName && ent.name.toLowerCase() === selfName) return false;
    return htmlLower.includes(ent.name.toLowerCase());
  });

  return linkifyHtml(html, linkableNames, maxLinks);
}

export function getRelatedHeadings(locale) {
  return HEADINGS[locale] || HEADINGS.de;
}
