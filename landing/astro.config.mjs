import { defineConfig } from 'astro/config';

// Landing/Hub-Projekt für tiroltourismus.com
// Reduzierte SEO-Landing mit Sprach-Links zu den Subdomains + Vote für soon-Sprachen.
export default defineConfig({
  site: 'https://tiroltourismus.com',
  output: 'static',
  compressHTML: true,
  build: {
    assets: 'assets',
    inlineStylesheets: 'auto',
  },
});
