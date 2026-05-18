import fs from 'fs';
import path from 'path';

const DATA_DIR = path.resolve(process.cwd(), 'src/data');

/**
 * Alle Einträge einer Collection lesen (z.B. regionen, unterkuenfte, orte, gastro)
 * returns [{ slug, entry }, ...]
 */
export function readCollection(name) {
  const dir = path.join(DATA_DIR, name);
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
export function readEntry(collection, slug) {
  const jsonPath = path.join(DATA_DIR, collection, slug, 'index.json');
  try { return JSON.parse(fs.readFileSync(jsonPath, 'utf-8')); }
  catch { return null; }
}

/** Singleton lesen (z.B. home.json, einstellungen.json) */
export function readSingleton(name) {
  const jsonPath = path.join(DATA_DIR, `${name}.json`);
  try { return JSON.parse(fs.readFileSync(jsonPath, 'utf-8')); }
  catch { return null; }
}

/** Published-only Filter */
export function isPublished(entry) {
  return !entry.status || entry.status === 'published';
}
