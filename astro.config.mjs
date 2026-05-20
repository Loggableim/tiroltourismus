import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';

const LANGUAGES = ['de', 'en', 'fr', 'it', 'es', 'zh'];
const LOCALE_MAP = { de:'de-AT', en:'en-US', fr:'fr-FR', it:'it-IT', es:'es-ES', zh:'zh-CN' };
const LOCALE_PATTERN = /^\/(en|fr|it|es|zh)(\/|$)/;

export default defineConfig({
  integrations: [react(), sitemap({
    i18n: {
      defaultLocale: 'de',
      locales: Object.fromEntries(LANGUAGES.map(l => [l, LOCALE_MAP[l]])),
    },
    serialize: (entry) => {
      const path = entry.url;
      const match = path.match(LOCALE_PATTERN);
      const currentLang = match ? match[1] : 'de';

      return {
        url: entry.url,
        // Lastmod für heutige Pages
        ...(path !== '/' && !path.match(LOCALE_PATTERN) && { lastmod: new Date().toISOString() }),
        links: LANGUAGES.map(l => {
          let url;
          if (l === 'de') {
            // DE: prefix entfernen
            url = match ? path.replace(LOCALE_PATTERN, '/') : path;
          } else if (currentLang === 'de') {
            // Von DE zu anderer Sprache: prefix hinzufügen
            url = `/${l}${path === '/' ? '' : path}`;
          } else {
            // Von Sprache X zu Sprache Y: prefix ersetzen
            url = path.replace(LOCALE_PATTERN, `/${l}$2`);
          }
          // Doppelte Slashes vermeiden
          url = url.replace(/\/\/+/g, '/');
          return { lang: LOCALE_MAP[l], url };
        }),
      };
    },
  })],
  output: 'static',
  site: 'https://tiroltourismus.com',
  build: {
    assets: 'assets',
    inlineStylesheets: 'auto',
  },
  compressHTML: true,
  vite: {
    build: {
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