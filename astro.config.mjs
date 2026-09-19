import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';

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
  zh: 'https://zh.tiroltourismus.com',
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
    filter: (page) => !['/404/', '/500/', '/login/', '/dashboard/', '/admin/'].some(p => page.startsWith(p)),
    entryLimit: 10000,
    serialize: (entry) => {
      // Single-Lang: alle Seiten liegen auf der Sprach-Subdomain an Root-Paths.
      // hreflang-Links zeigen cross-domain auf die anderen Sprach-Subdomains.
      const relPath = entry.url.startsWith(siteUrl) ? entry.url.slice(siteUrl.length) : entry.url;
      const links = PUBLISHED_LANGS.map(l => ({
        lang: HREFLANG_MAP[l],
        url: `${LANG_DOMAINS[l]}${relPath}`,
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
