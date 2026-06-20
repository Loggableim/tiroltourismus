import fs from 'fs';
import path from 'path';

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

/** Cache für eine oder alle Collections invalidieren */
export function invalidateCollectionCache(cacheKey) {
  if (cacheKey) _collectionCache.delete(cacheKey);
  else _collectionCache.clear();
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
  
  const locationCollections = ['regionen', 'unterkuenfte', 'camping', 'gastro', 'orte', 'sehenswuerdigkeiten', 'erlebnisse', 'events'];
  const results = [];

  function haversineDist(lat1, lng1, lat2, lng2) {
    const R = 6371;
    const dLat = (parseFloat(lat2) - parseFloat(lat1)) * Math.PI / 180;
    const dLng = (parseFloat(lng2) - parseFloat(lng1)) * Math.PI / 180;
    const a = Math.sin(dLat/2)**2 + Math.cos(parseFloat(lat1)*Math.PI/180) * Math.cos(parseFloat(lat2)*Math.PI/180) * Math.sin(dLng/2)**2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  }

  for (const coll of locationCollections) {
    const entries = readCollection(coll, locale);
    for (const e of entries) {
      if (coll === collection && e.slug === entry.slug) continue; // skip self
      const e2 = e.entry;
      
      let score = 0;
      let distKm = null;

      // Same region → strong match
      if (entry.region && e2.region && entry.region === e2.region) {
        score = 100;
      }

      // Same ort → strong match
      if (entry.ort && e2.ort && entry.ort.toLowerCase() === e2.ort.toLowerCase()) {
        score = Math.max(score, 80);
      }

      // Distance-based if both have coordinates
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
        results.push({ collection: coll, slug: e.slug, entry: e2, score, dist_km: distKm });
      }
    }
  }

  // Sort by score desc, then dist_km asc
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
 * HTML-Content mit automatischen internen Links anreichern.
 * Überspringt bereits bestehende Links und HTML-Tags.
 * Linkt maximal `maxLinks` Entitäten (Standard: 2).
 */
export function autoLinkContent(html, currentEntry = null, locale = 'de', maxLinks = 2) {
  if (!html || typeof html !== 'string') return html || '';
  
  const entityMap = _buildEntityMap(locale);
  const currentSlug = currentEntry?.slug;
  const currentName = (currentEntry?.name || currentEntry?.titel || '').toLowerCase();
  
  let linked = 0;
  let result = html;
  
  for (const entity of entityMap) {
    if (linked >= maxLinks) break;
    
    // Skip self-linking
    if (currentSlug && entity.slug === currentSlug) continue;
    if (currentName && entity.name.toLowerCase() === currentName) continue;
    
    const escaped = entity.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(?<!<[^>]*)(?<!href="[^"]*)(?<![\\w\\d])(${escaped})(?![\\w\\d])`, 'gi');
    
    if (regex.test(result)) {
      result = result.replace(regex, (match) => {
        if (linked >= maxLinks) return match;
        linked++;
        return `<a href="${entity.href}" class="auto-link">${match}</a>`;
      });
    }
  }
  
  return result;
}
