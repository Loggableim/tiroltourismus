import fs from 'fs';
import path from 'path';

const DATA_DIR = path.resolve(process.cwd(), 'src/data');

/**
 * Bezirk → zugehörige Region-Slugs
 * Wird für die Bezirks-Navigation und Filterung verwendet.
 */
export const BEZIRK_REGIONS = {
  innsbruck: ['innsbruck'],
  'innsbruck-land': ['innsbruck-land'],
  imst: ['imst', 'oetztal'],
  landeck: ['landeck', 'arlberg', 'kaunertal'],
  reutte: ['ausserfern'],
  kufstein: ['kufstein'],
  kitzbuehel: ['kitzbuehel'],
  schwaz: ['schwaz', 'achensee', 'zillertal'],
  lienz: ['osttirol', 'lienz'],
};

/**
 * Get the data directory for a given locale.
 * 'de' (or omitted) → src/data/
 * 'en'              → src/data/en/
 */
function getDataDir(locale = 'de') {
  if (!locale || locale === 'de') return DATA_DIR;
  return path.join(DATA_DIR, locale);
}

/**
 * Alle Einträge einer Collection lesen (z.B. regionen, unterkuenfte, orte, gastro)
 * returns [{ slug, entry }, ...]
 */
export function readCollection(name, locale = 'de') {
  const dir = path.join(getDataDir(locale), name);
  if (!fs.existsSync(dir)) return [];
  const entries = [];
  for (const item of fs.readdirSync(dir, { withFileTypes: true })) {
    if (!item.isDirectory()) continue;
    const jsonPath = path.join(dir, item.name, 'index.json');
    if (fs.existsSync(jsonPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
        if (data.status === 'archived') continue;
        entries.push({ slug: item.name, entry: data });
      } catch (e) { console.error(`Fehler in ${jsonPath}:`, e.message); }
    }
  }
  return entries;
}

/** Einzelnen Eintrag lesen */
export function readEntry(collection, slug, locale = 'de') {
  const jsonPath = path.join(getDataDir(locale), collection, slug, 'index.json');
  try { return JSON.parse(fs.readFileSync(jsonPath, 'utf-8')); }
  catch { return null; }
}

/** Singleton lesen (z.B. home.json, einstellungen.json) */
export function readSingleton(name, locale = 'de') {
  const jsonPath = path.join(getDataDir(locale), `${name}.json`);
  try { return JSON.parse(fs.readFileSync(jsonPath, 'utf-8')); }
  catch { return null; }
}

/** Published-only Filter */
export function isPublished(entry) {
  return !entry.status || entry.status === 'published';
}

/**
 * Alle Einträge mit einem bestimmten Tag finden (collection-übergreifend)
 * returns [{ collection, slug, entry }, ...]
 */
export function findByTag(tag, locale = 'de') {
  const collections = ['regionen', 'unterkuenfte', 'camping', 'gastro', 'orte', 'sehenswuerdigkeiten', 'magazin', 'erlebnisse', 'events'];
  const results = [];
  for (const coll of collections) {
    const entries = readCollection(coll, locale);
    for (const e of entries) {
      if (e.entry.tags && Array.isArray(e.entry.tags) && e.entry.tags.includes(tag)) {
        results.push({ collection: coll, slug: e.slug, entry: e.entry });
      }
    }
  }
  return results;
}

/**
 * Verwandte Einträge zu einem gegebenen Entry finden (gleiche Tags)
 * Gibt maximal `limit` Ergebnisse, sortiert nach Anzahl gemeinsamer Tags
 */
export function findRelated(collection, slug, locale = 'de', limit = 4) {
  const entry = readEntry(collection, slug, locale);
  if (!entry || !entry.tags || !Array.isArray(entry.tags) || entry.tags.length === 0) return [];

  const collections = ['regionen', 'unterkuenfte', 'camping', 'gastro', 'orte', 'sehenswuerdigkeiten', 'magazin', 'erlebnisse', 'events'];
  const scored = [];

  for (const coll of collections) {
    const entries = readCollection(coll, locale);
    for (const e of entries) {
      if (coll === collection && e.slug === slug) continue; // skip self
      if (!e.entry.tags || !Array.isArray(e.entry.tags)) continue;

      // Count overlapping tags
      const overlap = e.entry.tags.filter(t => entry.tags.includes(t)).length;
      if (overlap > 0) {
        scored.push({ collection: coll, slug: e.slug, entry: e.entry, score: overlap });
      }
    }
  }

  return scored.sort((a, b) => b.score - a.score).slice(0, limit);
}
