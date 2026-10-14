#!/usr/bin/env node
/**
 * batch-plan.mjs
 * Plant Übersetzungs-Batches: listet DE-Einträge eines Typs, bei denen mindestens
 * eine Nicht-DE-Fassung das gewählte Feld identisch zur DE-Fassung hat.
 *
 * Aufruf: node scripts/batch-plan.mjs --kind unterkuenfte --size 10 --start-id 32 [--field beschreibung] [--locales de,cs,...]
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const DATA = path.join(ROOT, 'src', 'data');
const DEFAULT_LOCALES = ['cs', 'en', 'es', 'fr', 'it', 'nl', 'zh'];

function parseArgs(argv) {
  const opts = { kind: null, size: 10, startId: 1, field: 'beschreibung', locales: DEFAULT_LOCALES };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    const next = () => {
      const value = argv[++i];
      if (value === undefined || value.startsWith('--')) throw new Error(`Wert fehlt für ${arg}`);
      return value;
    };
    if (arg === '--kind') opts.kind = next();
    else if (arg === '--size') opts.size = parseInt(next(), 10);
    else if (arg === '--start-id') opts.startId = parseInt(next(), 10);
    else if (arg === '--field') opts.field = next();
    else if (arg === '--locales') opts.locales = next().split(',').map((s) => s.trim()).filter(Boolean);
    else throw new Error(`Unbekannte Option: ${arg}`);
  }
  if (!opts.kind) throw new Error('--kind ist erforderlich');
  if (!Number.isInteger(opts.size) || opts.size < 1) throw new Error('--size muss eine positive Ganzzahl sein');
  if (!Number.isInteger(opts.startId) || opts.startId < 0) throw new Error('--start-id muss eine Ganzzahl >= 0 sein');
  return opts;
}

function readField(file, field) {
  try {
    const data = JSON.parse(fs.readFileSync(file, 'utf8'));
    const value = data?.[field];
    return typeof value === 'string' && value.length > 0 ? value : null;
  } catch {
    return null;
  }
}

function plan(opts) {
  const deDir = path.join(DATA, opts.kind);
  if (!fs.existsSync(deDir)) throw new Error(`Typ-Verzeichnis nicht gefunden: src/data/${opts.kind}`);

  const slugs = fs
    .readdirSync(deDir, { withFileTypes: true })
    .filter((d) => d.isDirectory() && fs.existsSync(path.join(deDir, d.name, 'index.json')))
    .map((d) => d.name)
    .sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));

  const selected = [];
  let matchedFiles = 0;
  for (const slug of slugs) {
    const deValue = readField(path.join(deDir, slug, 'index.json'), opts.field);
    if (deValue === null) continue;
    const matches = opts.locales.filter((locale) => {
      const file = path.join(DATA, locale, opts.kind, slug, 'index.json');
      return fs.existsSync(file) && readField(file, opts.field) === deValue;
    });
    if (matches.length > 0) {
      selected.push(slug);
      matchedFiles += matches.length;
    }
  }

  const blocks = [];
  for (let i = 0; i < selected.length; i += opts.size) {
    blocks.push(selected.slice(i, i + opts.size));
  }
  return { selected, matchedFiles, blocks };
}

function main() {
  let opts;
  try {
    opts = parseArgs(process.argv.slice(2));
  } catch (err) {
    console.error(err.message);
    process.exit(2);
  }

  let result;
  try {
    result = plan(opts);
  } catch (err) {
    console.error(err.message);
    process.exit(2);
  }

  result.blocks.forEach((block, idx) => {
    console.log(`BATCH T-C${opts.startId + idx} (${opts.kind}): ${block.join(', ')}`);
  });
  console.log('');
  console.log(
    `Summe (${opts.kind}, Feld ${opts.field}): ${result.selected.length} Einträge, ${result.matchedFiles} Dateien, ${result.blocks.length} Batches à max. ${opts.size}`
  );
}

main();
