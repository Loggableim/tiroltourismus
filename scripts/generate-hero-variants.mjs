import { readdir, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import sharp from 'sharp';

const ROOT_DIR = join(import.meta.dirname, '..');
const ROOTS = ['public/images/orte', 'public/images/sehenswuerdigkeiten'];
const VARIANTS = [
  { suffix: '-420.webp', width: 420, quality: 80 },
  { suffix: '-720.webp', width: 720, quality: 60 },
  { suffix: '-800.webp', width: 800, quality: 80 },
];

for (const root of ROOTS) {
  const absRoot = join(ROOT_DIR, root);
  const dirs = (await readdir(absRoot, { withFileTypes: true })).filter(d => d.isDirectory()).map(d => d.name);
  for (const slug of dirs) {
    const source = join(absRoot, slug, 'hero_1.png');
    try { await stat(source); } catch { continue; }
    for (const { suffix, width, quality } of VARIANTS) {
      const target = join(absRoot, slug, `hero_1${suffix}`);
      if (existsSync(target)) continue;
      await sharp(source).resize({ width, withoutEnlargement: true }).webp({ quality })
        .toFile(target);
    }
  }
}
console.log('hero variants generated');
