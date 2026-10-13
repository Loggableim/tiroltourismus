/**
 * Focused T-001 check. No production build.
 * Usage: node scripts/check-seo-index.mjs
 * Runs once with BUILD_LANGS=de and once with BUILD_LANGS=fr.
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const here = fileURLToPath(import.meta.url);

if (process.argv[2] !== '--run') {
  let failed = false;
  for (const lang of ['de', 'fr']) {
    const result = spawnSync(process.execPath, [here, '--run'], {
      env: { ...process.env, BUILD_LANGS: lang },
      stdio: 'inherit',
    });
    if (result.status !== 0) failed = true;
  }
  process.exit(failed ? 1 : 0);
}

const { readEntry, readCollection, isPublished, shouldIndex, getContentQuality } = await import('../src/lib/content.js');
const { PUBLISHED_LANGS, LANG_DOMAINS, BUILD_LANGS } = await import('../src/lib/languages.js');
const {
  includeInSitemap,
  hreflangAlternates,
  sitemapAlternateLinks,
  detailAlternateHref,
  localeUrlSlug,
  parseLocalizedPath,
  pickXDefaultHref,
} = await import('../src/lib/hreflang.js');

const buildLang = BUILD_LANGS[0];
const failures = [];
function assert(cond, message) {
  if (!cond && failures.length < 40) failures.push(message);
}

const LANG_PREFIX = /^\/(de|en|fr|cs|nl|it|es|zh)(\/|$)/;

assert(BUILD_LANGS.length === 1 && BUILD_LANGS[0] === process.env.BUILD_LANGS, `BUILD_LANGS=${BUILD_LANGS.join(',')}`);
assert(pickXDefaultHref([]) === null, 'empty x-default');
assert(pickXDefaultHref([
  { code: 'en', href: 'https://en.tiroltourismus.com/a/' },
  { code: 'fr', href: 'https://fr.tiroltourismus.com/a/' },
]) === 'https://en.tiroltourismus.com/a/', 'x-default falls back to first');
assert(pickXDefaultHref([
  { code: 'fr', href: 'https://fr.tiroltourismus.com/a/' },
  { code: 'de', href: 'https://de.tiroltourismus.com/a/' },
]) === 'https://de.tiroltourismus.com/a/', 'x-default prefers de');
assert(localeUrlSlug({ slug: 'from-entry' }, 'from-dir') === 'from-entry', 'entry.slug wins');
assert(localeUrlSlug({ slug: '   ' }, 'from-dir') === 'from-dir', 'blank slug falls back');
assert(detailAlternateHref('/gastro/old-slug/', 'de', 'zh', 'new-slug') === 'https://cn.tiroltourismus.com/gastro/new-slug/', 'zh slug swap stays on subdomain root');

const prefixed = parseLocalizedPath('/cs/gastro/example/', buildLang);
assert(prefixed.locale === 'cs' && prefixed.slug === 'example', 'language prefix wins');
const plain = parseLocalizedPath('/gastro/example/', buildLang);
assert(plain.locale === buildLang && plain.isEntryDetail, `plain locale ${plain.locale}`);

for (const blocked of ['/suche/', '/404/', '/500/', '/login/', '/dashboard/', '/admin/', '/en/suche/', 'https://de.tiroltourismus.com/suche/?q=innsbruck']) {
  assert(includeInSitemap(blocked) === false, `excluded ${blocked}`);
}
assert(includeInSitemap('/impressum/') === true, 'impressum stays');
assert(includeInSitemap('/gastro/') === true, 'listing stays');
assert(includeInSitemap('/gastro/this-slug-does-not-exist-t001/') === false, 'missing detail stays out');

const qualityCollections = ['unterkuenfte', 'camping', 'gastro', 'orte', 'sehenswuerdigkeiten'];
const samples = { thin: null, rich: null };
const counts = {};

for (const collection of qualityCollections) {
  const entries = readCollection(collection, buildLang).filter((item) => isPublished(item.entry));
  let thin = 0;
  let rich = 0;
  for (const item of entries) {
    const indexable = shouldIndex(item.entry, collection);
    if (indexable) rich += 1;
    else thin += 1;
    if (!samples.thin && !indexable) samples.thin = { collection, slug: item.slug, score: getContentQuality(item.entry, collection) };
    if (!samples.rich && indexable) samples.rich = { collection, slug: item.slug, score: getContentQuality(item.entry, collection) };
  }
  counts[collection] = { published: entries.length, thin, rich };
  const draft = readCollection(collection, buildLang).find((item) => !isPublished(item.entry));
  if (draft) assert(includeInSitemap(`/${collection}/${draft.slug}/`) === false, `unpublished ${collection}/${draft.slug}`);
}

assert(samples.thin, 'found a thin detail page');
assert(samples.rich, 'found an indexable detail page');
if (samples.thin) {
  assert(includeInSitemap(`/${samples.thin.collection}/${samples.thin.slug}/`) === false, 'thin page excluded');
  const hidden = hreflangAlternates({
    path: `/${samples.thin.collection}/${samples.thin.slug}/`,
    locale: buildLang,
    noindex: true,
  });
  assert(hidden.links.length === 0 && hidden.xDefault === null, 'noindex emits no hreflang');
}
if (samples.rich) {
  assert(includeInSitemap(`/${samples.rich.collection}/${samples.rich.slug}/`) === true, 'rich page included');
  const other = buildLang === 'de' ? 'en' : 'de';
  const otherEntry = readEntry(samples.rich.collection, samples.rich.slug, other);
  const otherIndexable = Boolean(otherEntry && isPublished(otherEntry) && shouldIndex(otherEntry, samples.rich.collection));
  assert(
    includeInSitemap(`/${other}/${samples.rich.collection}/${samples.rich.slug}/`) === otherIndexable,
    `prefixed ${other} inclusion`,
  );
}

function assertDetail(collection, slug) {
  const { links, xDefault } = hreflangAlternates({
    path: `/${collection}/${slug}/`,
    locale: buildLang,
    noindex: false,
  });
  const codes = new Set(links.map((link) => link.code));
  for (const lang of PUBLISHED_LANGS) {
    const entry = readEntry(collection, slug, lang);
    const published = Boolean(entry && isPublished(entry));
    assert(codes.has(lang) === published, `${collection}/${slug} ${lang} present=${codes.has(lang)} published=${published}`);
    if (!published) continue;
    const link = links.find((item) => item.code === lang);
    const url = new URL(link.href);
    assert(url.origin === LANG_DOMAINS[lang], `${link.href} origin`);
    assert(url.pathname === `/${collection}/${localeUrlSlug(entry, slug)}/`, `${link.href} path`);
    assert(!LANG_PREFIX.test(url.pathname), `${link.href} prefix`);
  }
  if (codes.has('de')) assert(xDefault === links.find((link) => link.code === 'de').href, `${collection}/${slug} x-default de`);
  else if (links[0]) assert(xDefault === links[0].href, `${collection}/${slug} x-default first`);

  const host = LANG_DOMAINS[buildLang].replace('https://', '');
  const sitemapLinks = sitemapAlternateLinks(`https://${host}/${collection}/${slug}/`);
  const sitemapLangs = new Set(sitemapLinks.map((link) => link.lang));
  for (const link of links) assert(sitemapLangs.has(link.hreflang), `sitemap missing ${link.hreflang}`);
  if (xDefault) {
    const xd = sitemapLinks.find((link) => link.lang === 'x-default');
    assert(xd && xd.url === xDefault, 'sitemap x-default');
  }
}

if (samples.rich) assertDetail(samples.rich.collection, samples.rich.slug);

const deGastro = new Set(readCollection('gastro', 'de').filter((item) => isPublished(item.entry)).map((item) => item.slug));
const csGastro = new Set(readCollection('gastro', 'cs').map((item) => item.slug));
const missingCs = [...deGastro].filter((slug) => !csGastro.has(slug)).sort();
assert(missingCs.length > 0, 'expected gastro slugs missing in cs');
for (const slug of missingCs) {
  const { links } = hreflangAlternates({ path: `/gastro/${slug}/`, locale: 'de', noindex: false });
  assert(!links.some((link) => link.code === 'cs'), `cs alternate leaked for ${slug}`);
  assert(!sitemapAlternateLinks(`https://de.tiroltourismus.com/gastro/${slug}/`).some((link) => link.lang === 'cs-CZ'), `sitemap copied cs for ${slug}`);
}

const staticPage = hreflangAlternates({ path: '/impressum/', locale: buildLang, noindex: false });
assert(staticPage.links.length === PUBLISHED_LANGS.length, `static alternates ${staticPage.links.length}`);
assert(staticPage.xDefault === 'https://de.tiroltourismus.com/impressum/', `static x-default ${staticPage.xDefault}`);
for (const link of staticPage.links) {
  const url = new URL(link.href);
  assert(url.origin === LANG_DOMAINS[link.code], `static origin ${link.href}`);
  assert(url.pathname === '/impressum/', `static path ${link.href}`);
}
const staticNoindex = hreflangAlternates({ path: '/impressum/', locale: buildLang, noindex: true });
assert(staticNoindex.links.length === 0 && staticNoindex.xDefault === null, 'static noindex');

const regionen = readCollection('regionen', buildLang).find((item) => isPublished(item.entry));
if (regionen) {
  assert(includeInSitemap(`/regionen/${regionen.slug}/`) === true, 'regionen detail is not quality-filtered');
  assertDetail('regionen', regionen.slug);
}

const redirects = fs.readFileSync('landing/public/_redirects', 'utf8');
for (const line of [
  '/it/* https://it.tiroltourismus.com/:splat 301',
  '/es/* https://es.tiroltourismus.com/:splat 301',
  '/zh/* https://cn.tiroltourismus.com/:splat 301',
  '/it https://it.tiroltourismus.com/ 301',
  '/es https://es.tiroltourismus.com/ 301',
  '/zh https://cn.tiroltourismus.com/ 301',
]) assert(redirects.includes(line), `redirect missing: ${line}`);

const indexXml = fs.readFileSync('landing/public/sitemap-index.xml', 'utf8');
assert(!indexXml.includes('sitemap-migration'), 'index advertises migration sitemaps');
assert(fs.existsSync('landing/public/sitemap-migration-0.xml'), 'migration file 0 missing');
assert(fs.existsSync('landing/public/sitemap-migration-1.xml'), 'migration file 1 missing');
const robots = fs.readFileSync('landing/public/robots.txt', 'utf8');
assert(!robots.includes('sitemap-migration'), 'robots advertises migration sitemaps');
assert(robots.includes('Sitemap: https://tiroltourismus.com/sitemap-index.xml'), 'landing robots sitemap');
const migrationScript = fs.readFileSync('scripts/generate-migration-sitemaps.mjs', 'utf8');
assert(!/writeFileSync\([^)]*sitemap-index/.test(migrationScript), 'regen writes sitemap-index');
const robotsScript = fs.readFileSync('scripts/generate-robots.mjs', 'utf8');
assert(robotsScript.includes('Sitemap: ${domain}/sitemap-index.xml'), 'language robots target');
assert(!/Sitemap:.*sitemap-migration/.test(robotsScript), 'language robots migration target');

const configModule = await import('../astro.config.mjs');
assert(configModule.default.site === LANG_DOMAINS[buildLang], `astro site ${configModule.default.site}`);

console.log(JSON.stringify({
  buildLang,
  site: configModule.default.site,
  thin: samples.thin,
  rich: samples.rich,
  missingCs,
  counts,
  failures: failures.length,
}, null, 2));

if (failures.length) {
  console.error(`FAIL ${failures.length} assertion(s) for BUILD_LANGS=${buildLang}`);
  for (const failure of failures) console.error(`  - ${failure}`);
  process.exit(1);
}
console.log(`OK BUILD_LANGS=${buildLang}`);
