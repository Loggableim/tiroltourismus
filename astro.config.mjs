import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';

const HREFLANG_LANGUAGES = ['de', 'en', 'fr', 'it'];
const LOCALE_MAP = { de:'de-AT', en:'en-US', fr:'fr-FR', it:'it-IT' };
const LOCALE_PATTERN = /^\/(en|fr|it)(\/|$)/;

export default defineConfig({
  site: 'https://tiroltourismus.com',
  output: 'static',
  compressHTML: true,
  build: {
    assets: 'assets',
    inlineStylesheets: 'auto',
  },
  image: {
    service: {
      entrypoint: 'astro/assets/services/sharp',
    },
  },
  integrations: [react(), sitemap({
    filter: (page) => !['/404/', '/500/', '/login/', '/dashboard/', '/admin/'].some(p => page.startsWith(p)),
    entryLimit: 10000,
    serialize: (entry) => {
      const path = entry.url;
      const sitePrefix = 'https://tiroltourismus.com';
      const relativePath = path.startsWith(sitePrefix) ? path.slice(sitePrefix.length) : path;
      const match = relativePath.match(LOCALE_PATTERN);
      const currentLang = match ? match[1] : 'de';

      const buildUrl = (lang, relPath) => {
        const p = relPath.replace(LOCALE_PATTERN, '/').replace(/\/+/g, '/');
        if (lang === 'de') return `${sitePrefix}${p}`;
        const prefix = p === '/' ? `/${lang}` : `/${lang}${p}`;
        return `${sitePrefix}${prefix}`;
      };

      return {
        url: entry.url,
        links: HREFLANG_LANGUAGES.map(l => ({
          lang: LOCALE_MAP[l],
          url: buildUrl(l, relativePath),
        })),
      };
    },
  })],
  vite: {
    build: {
      cssMinify: 'lightningcss',
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom'],
          },
        },
      },
    },
  },
});
