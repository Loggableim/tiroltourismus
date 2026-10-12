import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';

import { readEntry, isPublished, shouldIndex, readSingleton, getAvailableLocalesForEntry } from './src/lib/content.js';

// ── Subdomain-Architektur: site-URL hängt von BUILD_LANGS ab ──
// Single-Lang-Build (z.B. BUILD_LANGS=cs) → alle Seiten auf cs.tiroltourismus.com (Root-Paths)
// Multi-Lang (Dev, ohne BUILD_LANGS) → de auf Root, andere mit Prefix (lokales Dev)
const buildLangs = (process.env.BUILD_LANGS || '').split(',').map(s => s.trim()).filter(Boolean);
const isSingleLang = buildLangs.length === 1;
const singleLang = isSingleLang ? buildLangs[0] : null;

const LANG_DOMAINS = {
  de: 'https://de.tiroltourismus.com',
  en: 'https://en.tiroltourismus.com',
  fr: 'https://fr.tiroltourismus.com',
  cs: 'https://cs.tiroltourismus.com',
  nl: 'https://nl.tiroltourismus.com',
  it: 'https://it.tiroltourismus.com',
  es: 'https://es.tiroltourismus.com',
  zh: 'https://cn.tiroltourismus.com',
};
const LANDING_DOMAIN = 'https://tiroltourismus.com';
const PUBLISHED_LANGS = ['de', 'en', 'fr', 'cs', 'nl', 'it', 'es', 'zh'];
const HREFLANG_MAP = { de:'de-AT', en:'en-US', fr:'fr-FR', cs:'cs-CZ', nl:'nl-NL', it:'it-IT', es:'es-ES', zh:'zh-CN' };

const siteUrl = isSingleLang ? (LANG_DOMAINS[singleLang] || LANDING_DOMAIN) : LANDING_DOMAIN;

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
    filter: (page) => {
      try {
        const url = new URL(page);
        const segments = url.pathname.split('/').filter(Boolean);

        let locale = isSingleLang ? (singleLang || 'de') : 'de';
        let pathSegments = segments;
        if (!isSingleLang && segments.length > 0 && PUBLISHED_LANGS.includes(segments[0])) {
          locale = segments[0];
          pathSegments = segments.slice(1);
        }

        const normalizedPath = '/' + pathSegments.join('/') + (pathSegments.length > 0 ? '/' : '');
        const EXCLUDED_PREFIXES = ['/404', '/500', '/login', '/dashboard', '/admin', '/suche'];
        if (EXCLUDED_PREFIXES.some(p => normalizedPath === p || normalizedPath.startsWith(p + '/'))) {
          return false;
        }

        if (pathSegments.length === 2) {
          const [collection, slug] = pathSegments;
          if (collection === 'bezirke') {
            const b = readSingleton('bezirke', locale);
            return Boolean(b && b[slug]);
          }
          const QUALITY_COLLECTIONS = ['unterkuenfte', 'gastro', 'camping', 'orte', 'sehenswuerdigkeiten'];
          if (QUALITY_COLLECTIONS.includes(collection)) {
            const entry = readEntry(collection, slug, locale);
            if (!entry || !isPublished(entry) || !shouldIndex(entry, collection)) {
              return false;
            }
          } else {
            const entry = readEntry(collection, slug, locale);
            if (!entry || !isPublished(entry)) {
              return false;
            }
          }
        }
        return true;
      } catch {
        return true;
      }
    },
    entryLimit: 10000,
    lastmod: new Date(),
    serialize: (entry) => {
      const relPath = entry.url.startsWith(siteUrl) ? entry.url.slice(siteUrl.length) : entry.url;
      const cleanPath = relPath.replace(/^\/+|\/+$/g, '');
      const segments = cleanPath.split('/').filter(Boolean);

      let pathSegments = segments;
      if (!isSingleLang && segments.length > 0 && PUBLISHED_LANGS.includes(segments[0])) {
        pathSegments = segments.slice(1);
      }

      let availableLangs = PUBLISHED_LANGS;
      if (pathSegments.length === 2) {
        const [collection, slug] = pathSegments;
        availableLangs = getAvailableLocalesForEntry(collection, slug, { indexableOnly: true });
      }

      const pathSuffix = pathSegments.length > 0 ? `/${pathSegments.join('/')}/` : '/';
      const links = availableLangs.map(l => ({
        lang: HREFLANG_MAP[l],
        url: `${LANG_DOMAINS[l]}${pathSuffix}`,
      }));
      return { url: entry.url, links };
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
