import { readdir, stat } from 'node:fs/promises';
import { join } from 'node:path';
import sharp from 'sharp';

const ROOT = join(import.meta.dirname, '..', 'public', 'images', 'magazin');
const VARIANTS = [
  { suffix: '.webp', width: 800 },
  { suffix: '_thumb.webp', width: 420 },
];
const QUALITY = 80;

const slugs = (await readdir(ROOT, { withFileTypes: true }))
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name)
  .sort();

let produced = 0;
let totalBytes = 0;

for (const slug of slugs) {
  const source = join(ROOT, slug, 'hero_1.png');
  try {
    await stat(source);
  } catch {
    continue;
  }

  for (const { suffix, width } of VARIANTS) {
    const target = join(ROOT, slug, `hero_1${suffix}`);
    await sharp(source)
      .resize({ width, withoutEnlargement: true })
      .webp({ quality: QUALITY })
      .toFile(target);
    totalBytes += (await stat(target)).size;
    produced += 1;
  }
}

console.log(`magazin hero variants: ${produced} files, ${(totalBytes / 1048576).toFixed(2)} MB`);
