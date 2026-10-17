import fs from 'fs';
import path from 'path';
import { linkDescriptionText, linkifyHtml } from './related.js';
import { isHiddenSlug } from './hidden.js';

const DATA_DIR = path.resolve(process.cwd(), 'src/data');
const _collectionCache = new Map();

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
  const key = `${locale}:${name}`;
  if (_collectionCache.has(key)) return _collectionCache.get(key);
  const dir = path.join(getDataDir(locale), name);
  if (!fs.existsSync(dir)) return [];
  const entries = [];
  for (const item of fs.readdirSync(dir, { withFileTypes: true })) {
    if (!item.isDirectory()) continue;
    if (isHiddenSlug(name, item.name)) continue;
    const jsonPath = path.join(dir, item.name, 'index.json');
    if (fs.existsSync(jsonPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
        if (data.status === 'archived') continue;
        entries.push({ slug: item.name, entry: data });
      } catch (e) { console.error(`Fehler in ${jsonPath}:`, e.message); }
    }
  }
  _collectionCache.set(key, entries);
  return entries;
}

const _locationIndexCache = new Map();

/** Cache für eine oder alle Collections invalidieren */
export function invalidateCollectionCache(cacheKey) {
  if (cacheKey) {
    _collectionCache.delete(cacheKey);
    const locale = cacheKey.split(':')[0];
    if (locale) _locationIndexCache.delete(locale);
  } else {
    _collectionCache.clear();
    _locationIndexCache.clear();
  }
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
 * Entry-Qualitäts-Score (0–100) für Content-Qualitätslogik
 * 
 * Gewichtung (angepasst an aktuelle Datenrealität: 98% ohne Bild, 100% ohne Email):
 * - hero_bild:    +20  (Bild ist nice-to-have, aber nicht kritisch)
 * - email:        +10  (Kontaktmöglichkeit nice-to-have, nur für Gastro/Camping/Unterkunft)
 * - telefon:      +15  (telefon ist wichtiger für Gastro)
 * - webseite:     +10
 * - ort:          +10  (Standort ist wichtig)
 * - adresse:       +5
 * - kategorie:     +5
 * - tags (spezifisch, mehr als nur Default): +10
 * - beschreibung > 200 Zeichen: +15 (guter Text)
 * - hoehe vorhanden: +5 (für orte)
 * - einwohner vorhanden: +5 (für orte)
 * - sehenswuerdigkeiten vorhanden: +10 (für orte)
 * 
 * Tiers:
 *   A (75+):  Vollwertig → index
 *   B (50+):  Brauchbar → index
 *   C (25+):  Dünn → noindex
 *   D (<25):  Sehr dünn → noindex
 * 
 * Optionaler collection-Parameter für typspezifische Bewertung.
 * 'orte' und 'regionen' haben z.B. keine Kontaktdaten, werden anders bewertet.
 */
export function getContentQuality(entry, collection) {
  if (!entry) return 0;
  let score = 0;

  // hero_bild gibt Bonuspunkte
  if (entry.hero_bild) score += 20;
  if (entry.bilder && Array.isArray(entry.bilder) && entry.bilder.length > 0) score += 20;

  // Kontaktmöglichkeiten – nur relevant für Betriebs-Collections
  const hatKontaktDaten = ['gastro', 'camping', 'unterkuenfte', 'erlebnisse', 'events'].includes(collection);
  if (hatKontaktDaten) {
    if (entry.email) score += 10;
    if (entry.telefon) score += 15;
    if (entry.webseite) score += 10;
    if (entry.adresse) score += 5;
    if (entry.ort) score += 10;
  }

  // Standortdaten – für alle Collections
  if (entry.kategorie) score += 5;

  // Spezifische Tags (mehr als nur den Default-Tag)
  if (entry.tags && Array.isArray(entry.tags)) {
    const defaultTags = ['gastro', 'unterkunft', 'camping', 'hotel', 'ferienwohnung', 'restaurant', 'pub'];
    const relevantTags = entry.tags.filter(t => !defaultTags.includes(t));
    if (relevantTags.length >= 2) score += 10;
    else if (relevantTags.length >= 1) score += 5;
  }

  // Beschreibungstiefe
  const descLen = (entry.beschreibung || '').replace(/<[^>]+>/g, '').trim().length;
  if (descLen > 500) score += 15;
  else if (descLen > 200) score += 10;
  else if (descLen > 100) score += 5;

  // Orts-/Regions-/POI-spezifische Felder
  if (collection === 'orte' || collection === 'regionen') {
    if (entry.hoehe) score += 5;
    if (entry.einwohner) score += 5;
    if (entry.sehenswuerdigkeiten && Array.isArray(entry.sehenswuerdigkeiten) && entry.sehenswuerdigkeiten.length > 0) score += 10;
    if (entry.koordinaten) score += 5;
  }

  // Sehenswürdigkeiten-spezifische Felder
  if (collection === 'sehenswuerdigkeiten') {
    if (entry.ort) score += 10;
    if (entry.oeffnungszeiten) score += 10;
    if (entry.dauer) score += 5;
    if (entry.webseite) score += 10;
    if (entry.koordinaten) score += 5;
    if (entry.eintritt || entry.preis) score += 5;
    if (entry.beste_reisezeit) score += 5;
    if (entry.geeignet_fuer) score += 5;
  }

  return score;
}

/**
 * Qualitäts-Tier Label
 */
export function getQualityTier(score) {
  if (score >= 75) return 'A';
  if (score >= 50) return 'B';
  if (score >= 25) return 'C';
  return 'D';
}

/**
 * Sollte die Seite indexiert werden? (A+B → index, C+D → noindex)
 * Threshold 40 = Eintrag mit Beschreibung + Basisinfos ist indexierbar.
 */
export function shouldIndex(entry, collection) {
  const score = getContentQuality(entry, collection);
  return score >= 40;
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

const LOCATION_COLLECTIONS = ['regionen', 'unterkuenfte', 'camping', 'gastro', 'orte', 'sehenswuerdigkeiten', 'erlebnisse', 'events'];

function haversineDist(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = (parseFloat(lat2) - parseFloat(lat1)) * Math.PI / 180;
  const dLng = (parseFloat(lng2) - parseFloat(lng1)) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(parseFloat(lat1) * Math.PI / 180) * Math.cos(parseFloat(lat2) * Math.PI / 180) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/** Einmal pro Locale: Einträge nach Region/Ort/Koordinaten indexieren (für findNearby). */
function _buildLocationIndex(locale = 'de') {
  if (_locationIndexCache.has(locale)) return _locationIndexCache.get(locale);
  const byRegion = new Map();
  const byOrt = new Map();
  const withCoords = [];

  for (const coll of LOCATION_COLLECTIONS) {
    for (const e of readCollection(coll, locale)) {
      const item = { collection: coll, slug: e.slug, entry: e.entry };
      const region = e.entry.region;
      if (region) {
        if (!byRegion.has(region)) byRegion.set(region, []);
        byRegion.get(region).push(item);
      }
      const ort = e.entry.ort;
      if (ort) {
        const ortKey = ort.toLowerCase();
        if (!byOrt.has(ortKey)) byOrt.set(ortKey, []);
        byOrt.get(ortKey).push(item);
      }
      if (e.entry.koordinaten) withCoords.push(item);
    }
  }

  const index = { byRegion, byOrt, withCoords };
  _locationIndexCache.set(locale, index);
  return index;
}

function _nearbyCandidates(entry, locale) {
  const index = _buildLocationIndex(locale);
  const seen = new Map();

  function add(item) {
    const key = `${item.collection}:${item.slug}`;
    if (!seen.has(key)) seen.set(key, item);
  }

  if (entry.region) {
    for (const item of index.byRegion.get(entry.region) || []) add(item);
  }
  if (entry.ort) {
    for (const item of index.byOrt.get(entry.ort.toLowerCase()) || []) add(item);
  }
  if (entry.koordinaten) {
    const lat = parseFloat(entry.koordinaten.lat);
    const lng = parseFloat(entry.koordinaten.lng);
    // ~25 km bounding box (covers all haversine matches up to 20 km)
    const dLat = 25 / 111;
    const cosLat = Math.cos(lat * Math.PI / 180) || 1;
    const dLng = 25 / (111 * cosLat);
    for (const item of index.withCoords) {
      const c = item.entry.koordinaten;
      const lat2 = parseFloat(c.lat);
      const lng2 = parseFloat(c.lng);
      if (Math.abs(lat2 - lat) <= dLat && Math.abs(lng2 - lng) <= dLng) add(item);
    }
  }

  return seen.values();
}

/**
 * Nahegelegene Einträge zu einem Entry finden (region-basiert + distanz-basiert)
 * 1. Gleiche Region → score 100
 * 2. Gleicher Ort → score 50
 * 3. Distanz < 10km → score nach Entfernung
 *
 * Berücksichtigt NUR Collections mit Standort (kein 'magazin')
 * Gibt maximal `limit` Ergebnisse
 */
export function findNearby(entry, collection, locale = 'de', limit = 8) {
  if (!entry) return [];

  const results = [];
  const entrySlug = entry.slug;

  for (const { collection: coll, slug, entry: e2 } of _nearbyCandidates(entry, locale)) {
    if (coll === collection && slug === entrySlug) continue;

    let score = 0;
    let distKm = null;

    if (entry.region && e2.region && entry.region === e2.region) {
      score = 100;
    }

    if (entry.ort && e2.ort && entry.ort.toLowerCase() === e2.ort.toLowerCase()) {
      score = Math.max(score, 80);
    }

    if (entry.koordinaten && e2.koordinaten) {
      distKm = haversineDist(
        entry.koordinaten.lat, entry.koordinaten.lng,
        e2.koordinaten.lat, e2.koordinaten.lng
      );
      if (distKm < 1) score = Math.max(score, 90);
      else if (distKm < 5) score = Math.max(score, 70);
      else if (distKm < 10) score = Math.max(score, 50);
      else if (distKm < 20) score = Math.max(score, 30);
    }

    if (score > 0) {
      results.push({ collection: coll, slug, entry: e2, score, dist_km: distKm });
    }
  }

  results.sort((a, b) => b.score - a.score || (a.dist_km || 999) - (b.dist_km || 999));
  return results.slice(0, limit);
}

/**
 * Cache für entityMap (per locale)
 */
const _entityCache = new Map();

export function invalidateEntityCache(locale) {
  if (locale) _entityCache.delete(locale);
  else _entityCache.clear();
}

function _buildEntityMap(locale = 'de') {
  if (_entityCache.has(locale)) return _entityCache.get(locale);
  const pref = locale === 'de' ? '' : `/${locale}`;
  const map = [];
  const collections = [
    { name: 'regionen', prefix: `${pref}/regionen/`, nameField: 'titel', weight: 5 },
    { name: 'orte', prefix: `${pref}/orte/`, nameField: 'name', weight: 4 },
    { name: 'sehenswuerdigkeiten', prefix: `${pref}/sehenswuerdigkeiten/`, nameField: 'name', weight: 3 },
    { name: 'magazin', prefix: `${pref}/magazin/`, nameField: 'titel', weight: 2 },
    { name: 'erlebnisse', prefix: `${pref}/erlebnisse/`, nameField: 'name', weight: 2 },
    { name: 'events', prefix: `${pref}/events/`, nameField: 'name || titel', weight: 2 },
    { name: 'gastro', prefix: `${pref}/gastro/`, nameField: 'name', weight: 2 },
  ];
  for (const coll of collections) {
    const entries = readCollection(coll.name, locale);
    for (const e of entries) {
      const name = e.entry.name || e.entry.titel || '';
      if (name && name.length > 2) {
        map.push({
          name,
          slug: e.slug,
          href: coll.prefix + e.slug + '/',
          weight: coll.weight,
          collection: coll.name,
        });
      }
    }
  }
  map.sort((a, b) => b.name.length - a.name.length);
  _entityCache.set(locale, map);
  return map;
}

/**
 * HTML-Content mit automatischen internen Links anreichern (siehe related.js).
 * @param {string} [collection] — Collection des aktuellen Eintrags
 * @param {string} [slug] — Slug des aktuellen Eintrags
 */
export function autoLinkContent(html, currentEntry = null, locale = 'de', maxLinks = 5, collection = null, slug = null) {
  if (!html || typeof html !== 'string') return html || '';
  const preparedHtml = stripDescriptionSectionMarkers(html);
  if (collection && slug) {
    return linkDescriptionText(preparedHtml, collection, slug, locale, maxLinks, currentEntry);
  }
  const entityMap = _buildEntityMap(locale);
  const currentSlug = currentEntry?.slug;
  const currentName = (currentEntry?.name || currentEntry?.titel || '').toLowerCase();
  // Nur Entitäten, deren Name im Text vorkommt (Performance + weniger Regexe).
  const probe = preparedHtml.replace(/<[^>]+>/g, ' ').toLowerCase();
  const entities = entityMap.filter((entity) => {
    if (currentSlug && entity.slug === currentSlug) return false;
    if (currentName && entity.name.toLowerCase() === currentName) return false;
    return probe.includes(String(entity.name).toLowerCase());
  });
  return linkifyHtml(preparedHtml, entities, maxLinks);
}

/** Remove the standalone field heading accidentally included in legacy rich text. */
export function stripDescriptionSectionMarkers(html) {
  if (typeof html !== 'string' || !html) return html || '';

  return html
    .replace(
      /(^|<br\s*\/?>|<\/p>|<p\b[^>]*>|\r?\n)\s*===\s*beschreibung\s*===\s*(?=<br\s*\/?>|<\/p>|<p\b|\r?\n|$)/gi,
      '$1',
    )
    .replace(/<p\b[^>]*>\s*<\/p>/gi, '')
    .replace(/^\s+|^(?:<br\s*\/?>\s*)+/i, '');
}

const _existsCache = new Map();

/**
 * Prüft schnell (mit Cache), ob ein Eintrag in einer Sprache existiert und veröffentlicht ist.
 */
export function entryExists(collection, slug, locale = 'de') {
  const key = `${locale}:${collection}:${slug}`;
  if (_existsCache.has(key)) return _existsCache.get(key);
  const dataDir = !locale || locale === 'de' ? DATA_DIR : path.join(DATA_DIR, locale);
  const jsonPath = path.join(dataDir, collection, slug, 'index.json');
  if (!fs.existsSync(jsonPath)) {
    _existsCache.set(key, false);
    return false;
  }
  const entry = readEntry(collection, slug, locale);
  const valid = Boolean(entry && isPublished(entry));
  _existsCache.set(key, valid);
  return valid;
}

/**
 * Gibt alle Sprachen aus den übergebenen Locales (Standard: alle 8) zurück,
 * in denen ein Eintrag wirklich existiert und veröffentlicht ist.
 * Wenn indexableOnly: true, werden für Qualitäts-Collections nur indexierbare Einträge gezählt.
 */
export function getAvailableLocalesForEntry(collection, slug, options = {}) {
  const { indexableOnly = false, locales = ['de', 'en', 'fr', 'cs', 'nl', 'it', 'es', 'zh'] } = options;
  if (collection === 'bezirke') {
    return locales.filter(l => {
      const b = readSingleton('bezirke', l);
      return Boolean(b && b[slug]);
    });
  }

  const QUALITY_COLLECTIONS = ['unterkuenfte', 'gastro', 'camping', 'orte', 'sehenswuerdigkeiten'];
  return locales.filter(l => {
    if (!entryExists(collection, slug, l)) return false;
    if (indexableOnly && QUALITY_COLLECTIONS.includes(collection)) {
      const entry = readEntry(collection, slug, l);
      return Boolean(entry && shouldIndex(entry, collection));
    }
    return true;
  });
}

/**
 * Ermittelt verfügbare Sprachen für einen gegebenen Pfad (z.B. /unterkuenfte/alpenrose/ oder /en/magazin/xyz/).
 */
export function getAvailableLocalesForPath(pathname, options = {}) {
  const locales = options.locales || ['de', 'en', 'fr', 'cs', 'nl', 'it', 'es', 'zh'];
  const prefixRegex = new RegExp(`^/(${locales.join('|')})(/|$)`);
  const match = pathname.match(prefixRegex);
  const cleanPath = (match ? pathname.slice(match[1].length + 1) : pathname).replace(/^\/+|\/+$/g, '');
  const segments = cleanPath.split('/').filter(Boolean);

  if (segments.length === 2) {
    const [collection, slug] = segments;
    return getAvailableLocalesForEntry(collection, slug, { ...options, locales });
  }

  // Alle anderen Seiten (Home, Listen, Info/Service) existieren in allen veröffentlichten Sprachen
  return locales;
}
