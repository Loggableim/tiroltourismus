import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';
import { includeInSitemap, sitemapAlternateLinks } from './src/lib/hreflang.js';

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
    filter: (page) => includeInSitemap(page) && !page.includes('/demofrontneu') && !page.includes('/demo-tvb/'),
    entryLimit: 10000,
    lastmod: new Date(),
    serialize: (entry) => ({
      url: entry.url,
      lastmod: entry.lastmod,
      changefreq: entry.changefreq,
      priority: entry.priority,
      links: sitemapAlternateLinks(entry.url),
    }),
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
