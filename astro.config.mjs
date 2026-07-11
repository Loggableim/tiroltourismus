import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';

// ── Subdomain-Split: site-URL hängt von BUILD_LANGS ab ──
const buildLangs = process.env.BUILD_LANGS || 'de,en,fr';
const langs = buildLangs.split(',').map(s => s.trim()).filter(Boolean);

// Wenn nur eine Sprache gebaut wird (z.B. cs), ist das die Default-Sprache
const isSingleLang = langs.length === 1;
const singleLang = isSingleLang ? langs[0] : null;

// Domain-Map
const LANG_DOMAINS = {
  de: 'https://tiroltourismus.com',
  en: 'https://tiroltourismus.com',
  fr: 'https://tiroltourismus.com',
  it: 'https://tiroltourismus.com',
  es: 'https://tiroltourismus.com',
  zh: 'https://tiroltourismus.com',
  nl: 'https://nl.tiroltourismus.com',
  cs: 'https://cs.tiroltourismus.com',
};

const siteUrl = isSingleLang ? LANG_DOMAINS[singleLang] : 'https://tiroltourismus.com';

// Hreflang: alle 8 Sprachen (auch wenn nicht alle in diesem Build sind)
const HREFLANG_LANGUAGES = ['de', 'en', 'fr', 'it', 'es', 'zh', 'nl', 'cs'];
const LOCALE_MAP = { de:'de-AT', en:'en-US', fr:'fr-FR', it:'it-IT', es:'es-ES', zh:'zh-CN', nl:'nl-NL', cs:'cs-CZ' };
const LOCALE_PATTERN = /^\/(en|fr|it|es|zh|nl|cs)(\/|$)/;

export default defineConfig({
  site: siteUrl,
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
      const sitePrefix = siteUrl;
      const relativePath = path.startsWith(sitePrefix) ? path.slice(sitePrefix.length) : path;
      const match = relativePath.match(LOCALE_PATTERN);
      const currentLang = match ? match[1] : 'de';

      const buildUrl = (lang, relPath) => {
        const p = relPath.replace(LOCALE_PATTERN, '/').replace(/\/+/g, '/');
        const domain = LANG_DOMAINS[lang] || LANG_DOMAINS.de;
        if (lang === 'de') return `${domain}${p}`;
        const prefix = p === '/' ? `/${lang}` : `/${lang}${p}`;
        return `${domain}${prefix}`;
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
