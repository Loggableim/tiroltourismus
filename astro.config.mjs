import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';
import { LANGUAGES_READY } from './src/lib/languages.js';

export default defineConfig({
  integrations: [react(), sitemap({
    i18n: {
      defaultLocale: 'de',
      locales: {
        de: 'de-AT',
        en: 'en-US',
        fr: 'fr-FR',
        it: 'it-IT',
        es: 'es-ES',
        zh: 'zh-CN',
      },
    },
    serialize: (entry) => {
      const path = entry.url;
      const langMatch = path.match(/^\/(en|fr|it|es|zh)(\/|$)/);
      const lang = langMatch ? langMatch[1] : 'de';
      return {
        url: entry.url,
        links: LANGUAGES_READY.map(l => ({
          lang: l === 'de' ? 'de-AT' : ({en:'en-US',fr:'fr-FR',it:'it-IT',es:'es-ES',zh:'zh-CN'})[l],
          url: l === 'de' 
            ? path.replace(/^\/(en|fr|it|es|zh)(\/|$)/, '/') 
            : path.replace(/^\/(en|fr|it|es|zh)(\/|$)/, `/${l}$1`),
        })),
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