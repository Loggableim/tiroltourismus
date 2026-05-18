/**
 * geocode-retry.mjs — Nachschlag für fehlgeschlagene Einträge
 * Holt Koordinaten für alle Einträge ohne `koordinaten`.
 * Mit 429-Handling + Retry + fallback-Query.
 */

import fs from 'fs';
import path from 'path';

const DATA_DIR = path.resolve(process.cwd(), 'src/data');
const DRY_RUN = process.argv.includes('--dry-run');

let stats = { ok: 0, fail: 0, skip: 0 };

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function geocodeWithRetry(query, maxRetries = 3) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    if (attempt > 0) {
      const wait = Math.min(5000 * Math.pow(2, attempt - 1), 60000);
      console.log(`     ⏳ Retry ${attempt}/${maxRetries} in ${wait/1000}s...`);
      await sleep(wait);
    }

    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1&accept-language=de`;
    try {
      const res = await fetch(url, {
        headers: { 'User-Agent': 'TirolTourismus/2.0 (geocoding-script)' }
      });

      if (res.status === 429) {
        console.log(`     ⚠ 429 Too Many Requests`);
        continue; // retry with backoff
      }
      if (!res.ok) {
        console.log(`     ⚠ HTTP ${res.status}`);
        return null;
      }
      const data = await res.json();
      if (!data || data.length === 0) return null;
      return {
        lat: parseFloat(data[0].lat).toFixed(4),
        lng: parseFloat(data[0].lon).toFixed(4),
      };
    } catch (e) {
      console.log(`     ⚠ Error: ${e.message}`);
      continue;
    }
  }
  return null;
}

async function processCollection(name) {
  const dir = path.join(DATA_DIR, name);
  if (!fs.existsSync(dir)) return;

  const items = fs.readdirSync(dir, { withFileTypes: true }).filter(d => d.isDirectory());

  for (const item of items) {
    const jsonPath = path.join(dir, item.name, 'index.json');
    if (!fs.existsSync(jsonPath)) continue;

    let entry;
    try { entry = JSON.parse(fs.readFileSync(jsonPath, 'utf-8')); }
    catch { continue; }

    if (entry.koordinaten?.lat && entry.koordinaten?.lng) {
      stats.skip++;
      continue;
    }

    // Baue Query — probiere mehrere Varianten
    const queries = [];
    const q1 = [entry.adresse, entry.ort, entry.name].filter(Boolean).join(', ');
    if (q1) queries.push(`${q1}, Tirol, Österreich`);

    const q2 = entry.name ? `${entry.name}, Tirol, Österreich` : null;
    if (q2 && q2 !== queries[0]) queries.push(q2);

    const q3 = entry.ort ? `${entry.ort}, Tirol, Österreich` : null;
    if (q3 && q3 !== queries[0] && q3 !== q2) queries.push(q3);

    if (queries.length === 0) {
      console.log(`  ⏭  ${item.name}: kein Suchbegriff`);
      stats.skip++;
      continue;
    }

    let result = null;
    for (const q of queries) {
      console.log(`  🔍 ${item.name} → "${q.substring(0, 50)}..."`);
      result = await geocodeWithRetry(q);
      if (result) {
        console.log(`     ✅ ${result.lat}, ${result.lng}`);
        break;
      }
      console.log(`     ❌`);
      await sleep(1200);
    }

    if (result) {
      entry.koordinaten = { lat: result.lat, lng: result.lng };
      if (!DRY_RUN) {
        fs.writeFileSync(jsonPath, JSON.stringify(entry, null, 2) + '\n', 'utf-8');
      }
      stats.ok++;
    } else {
      stats.fail++;
    }

    await sleep(1200);
  }
}

async function main() {
  console.log('=== Geocode Retry ===');
  if (DRY_RUN) console.log('🔷 DRY RUN');

  const COLLECTIONS = ['gastro', 'orte', 'regionen', 'sehenswuerdigkeiten', 'unterkuenfte'];

  for (const coll of COLLECTIONS) {
    console.log(`\n📁 ${coll}:`);
    await processCollection(coll);
  }

  console.log('\n=== Ergebnis ===');
  console.log(`✅ Neu geocoded: ${stats.ok}`);
  console.log(`❌ Fehlgeschlagen: ${stats.fail}`);
  console.log(`⏭  Übersprungen: ${stats.skip}`);
  if (DRY_RUN) console.log('🔷 DRY RUN');
}

main().catch(console.error);
