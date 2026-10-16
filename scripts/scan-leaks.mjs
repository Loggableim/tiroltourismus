#!/usr/bin/env node
// Vollscan aller übersetzten Inhalte auf Leaks. --json für maschinenlesbare Ausgabe.
import fs from 'node:fs'; import path from 'node:path';
import { detectCjkInNonZh, detectLeak, walkStrings } from './lib/leak-detect.mjs';
const DATA = 'src/data';
const LOC = ['cs','en','es','fr','it','nl','zh','hu','pl','sk'];
const hits = [];
function get(o, p) { try { return p.split(/\.|\[|\]/).filter(Boolean).reduce((a, k) => a?.[k], o); } catch { return undefined; } }
function walk(dir, cb) { for (const e of fs.readdirSync(dir, { withFileTypes: true })) { const f = path.join(dir, e.name); if (e.isDirectory()) walk(f, cb); else if (e.name.endsWith('.json')) cb(f); } }
for (const loc of LOC) {
  const d = path.join(DATA, loc); if (!fs.existsSync(d)) continue;
  walk(d, (f) => {
    let j; try { j = JSON.parse(fs.readFileSync(f, 'utf8')); } catch { return; }
    const deFile = path.join(DATA, path.relative(d, f)); let de = null;
    try { de = JSON.parse(fs.readFileSync(deFile, 'utf8')); } catch {}
    for (const [p, v] of walkStrings(j)) {
      let why = detectLeak(v) || detectCjkInNonZh(v, loc);
      if (!why && de) { const s = get(de, p); if (typeof s === 'string' && s.length > 40 && v.length > 3 * s.length && v.length > 300) why = `>3x länger als DE (${v.length}/${s.length})`; }
      if (why) hits.push({ file: f, lang: loc, field: p, why, deFile: de ? deFile : null });
    }
  });
}
// auch DE-Quelle selbst
walk(DATA, (f) => { if (LOC.some(l => f.startsWith(path.join(DATA, l) + '/'))) return; let j; try { j = JSON.parse(fs.readFileSync(f, 'utf8')); } catch { return; } for (const [p, v] of walkStrings(j)) { const why = detectLeak(v) || detectCjkInNonZh(v, 'de'); if (why) hits.push({ file: f, lang: 'de', field: p, why }); } });
if (process.argv.includes('--json')) console.log(JSON.stringify(hits, null, 1));
else { for (const h of hits) console.log(`${h.lang}\t${h.file}\t${h.field}\t${h.why}`); console.error(`Treffer: ${hits.length}`); }
process.exit(hits.length ? 1 : 0);
