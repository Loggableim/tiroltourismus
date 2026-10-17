/** fakt-02: ausgeblendete (Nicht-Tirol-)Einträge, sprachübergreifend per Slug. */
import fs from 'fs';
import path from 'path';
let _h = null;
export function isHiddenSlug(collection, slug) {
  if (!_h) {
    try { _h = JSON.parse(fs.readFileSync(path.resolve(process.cwd(), 'src/data/_hidden-nicht-tirol.json'), 'utf-8')); }
    catch { _h = {}; }
  }
  const list = _h[collection];
  return Array.isArray(list) && list.includes(slug);
}
