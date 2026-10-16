import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const PUBLIC_DIR = fileURLToPath(new URL('../../public/', import.meta.url));

// Konventionen: orte `<base>-420.webp` / `<base>-800.webp`, magazin `<base>.webp` / `<base>_thumb.webp`
const VARIANTS = [
  { suffix: '-420.webp', width: 420 },
  { suffix: '-800.webp', width: 800 },
  { suffix: '_thumb.webp', width: 420 },
  { suffix: '.webp', width: 800 },
];

export function resolveHeroImage(src) {
  if (!src) return null;
  if (!src.endsWith('.png')) return { src, srcset: undefined, sizes: undefined };
  const base = src.slice(0, -'.png'.length);
  const found = VARIANTS
    .map(v => ({ path: `${base}${v.suffix}`, width: v.width }))
    .filter(v => existsSync(join(PUBLIC_DIR, v.path)))
    .sort((a, b) => a.width - b.width);
  if (found.length === 0) return { src, srcset: undefined, sizes: undefined };
  return {
    src: found[0].path,
    srcset: found.map(v => `${v.path} ${v.width}w`).join(', '),
    sizes: '100vw',
  };
}
