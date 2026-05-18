/**
 * geocode-coordinates.mjs — optimierte Version
 * 
 * Sammelt alle unique Ortsnamen aus allen Collections,
 * geocoded jeden Ort nur einmal,
 * schreibt Koordinaten in alle passenden JSONs.
 * 
 * Usage:   node scripts/geocode-coordinates.mjs
 * Dryrun:  node scripts/geocode-coordinates.mjs --dry-run
 */

import fs from 'fs';
import path from 'path';

const DATA_DIR = path.resolve(process.cwd(), 'src/data');
const DRY_RUN = process.argv.includes('--dry-run');
const DELAY_MS = 1100;

const COLLECTIONS = [
  'erlebnisse', 'sehenswuerdigkeiten', 'unterkuenfte',
  'gastro', 'camping', 'orte', 'events'
];

let stats = { geocoded: 0, failed: 0, skipped: 0, written: 0 };

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function geocode(query) {
  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1&accept-language=de`;
  const res = await fetch(url, {
    headers: { 'User-Agent': 'TirolTourismus/2.0 (geocoding-script)' }
  });
  if (!res.ok) return null;
  const data = await res.json();
  if (!data || data.length === 0) return null;
  return {
    lat: parseFloat(data[0].lat).toFixed(4),
    lng: parseFloat(data[0].lon).toFixed(4),
  };
}

// Phase 1: Alle Einträge einlesen + unique Ortsnamen sammeln
console.log('=== Phase 1: Einträge analysieren ===\n');

const entries = []; // { collection, slug, entry, query }
const uniqueQueries = new Map(); // query → { lat, lng } | null
const queryEntries = new Map();  // query → [{ collection, slug }]

for (const coll of COLLECTIONS) {
  const dir = path.join(DATA_DIR, coll);
  if (!fs.existsSync(dir)) continue;

  const items = fs.readdirSync(dir, { withFileTypes: true }).filter(d => d.isDirectory());

  for (const item of items) {
    const jsonPath = path.join(dir, item.name, 'index.json');
    if (!fs.existsSync(jsonPath)) continue;

    let entry;
    try { entry = JSON.parse(fs.readFileSync(jsonPath, 'utf-8')); }
    catch { continue; }

    if (entry.koordinaten?.lat && entry.koordinaten?.lng) {
      stats.skipped++;
      continue;
    }

    // Query aus Ort + Region + Adresse bauen
    const parts = [];
    if (entry.adresse) parts.push(entry.adresse);
    if (entry.ort) parts.push(entry.ort);
    if (!entry.ort && entry.ortschaft) parts.push(entry.ortschaft);
    if (entry.plz) parts.push(entry.plz);
    parts.push('Tirol', 'Österreich');

    // Für orte-collection: name verwenden
    if (coll === 'orte' && entry.name) {
      const q = `${entry.name}, Tirol, Österreich`;
      if (!uniqueQueries.has(q)) {
        uniqueQueries.set(q, undefined);
        queryEntries.set(q, []);
      }
      queryEntries.get(q).push({ collection: coll, slug: item.name, entry, jsonPath });
      continue;
    }

    let query = parts.filter(Boolean).join(', ');
    if (!query || query === 'Tirol, Österreich') {
      // Fallback: entry name
      if (entry.name) {
        query = `${entry.name}, Tirol, Österreich`;
      } else {
        stats.skipped++;
        continue;
      }
    }

    if (!uniqueQueries.has(query)) {
      uniqueQueries.set(query, undefined);
      queryEntries.set(query, []);
    }
    queryEntries.get(query).push({ collection: coll, slug: item.name, entry, jsonPath });
  }
}

console.log(`Einträge ohne Koordinaten: ${[...queryEntries.values()].reduce((a, b) => a + b.length, 0)}`);
console.log(`Unique Queries: ${uniqueQueries.size}\n`);

// Phase 2: Geocoding
console.log('=== Phase 2: Geocoding ===\n');

let i = 0;
for (const [query, _] of uniqueQueries) {
  i++;
  const result = await geocode(query);
  if (result) {
    uniqueQueries.set(query, result);
    console.log(`[${i}/${uniqueQueries.size}] 🔍 "${query.substring(0, 60)}..." ✅ ${result.lat}, ${result.lng}`);
    stats.geocoded++;
  } else {
    uniqueQueries.set(query, null);
    console.log(`[${i}/${uniqueQueries.size}] 🔍 "${query.substring(0, 60)}..." ❌ Kein Treffer`);
    stats.failed++;
  }

  if (i < uniqueQueries.size) await sleep(DELAY_MS);
}

// Phase 3: Koordinaten schreiben
console.log('\n=== Phase 3: Koordinaten schreiben ===\n');

for (const [query, coords] of uniqueQueries) {
  if (!coords) continue;
  const items = queryEntries.get(query);
  for (const { entry, jsonPath } of items) {
    entry.koordinaten = { lat: coords.lat, lng: coords.lng };
    if (!DRY_RUN) {
      fs.writeFileSync(jsonPath, JSON.stringify(entry, null, 2) + '\n', 'utf-8');
    }
    stats.written++;
  }
}

console.log('=== Zusammenfassung ===');
console.log(`Unique Queries geocoded: ${stats.geocoded}`);
console.log(`Fehlgeschlagen: ${stats.failed}`);
console.log(`Übersprungen (schon vorhanden): ${stats.skipped}`);
console.log(`Einträge mit Koordinaten befüllt: ${stats.written}`);
if (DRY_RUN) console.log('🔷 DRY RUN — keine Dateien geändert');
