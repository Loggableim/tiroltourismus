/**
 * hreflang.js — gemeinsame Alternate-URLs für HTML und die Astro-Sitemap.
 *
 * Detail-URLs: nur Sprachen, in denen readEntry einen published Entry liefert.
 * Der href nutzt den Slug dieser Sprache (entry.slug, sonst Verzeichnisname).
 * Statische Seiten: alle PUBLISHED_LANGS.
 * noindex: keine Alternates und kein x-default.
 * x-default: de, wenn de dabei ist, sonst der erste Alternate.
 *
 * Sitemap-Aufnahme bleibt enger: die fünf Detail-Collections nur bei
 * published + shouldIndex. suche/404/500/login/dashboard/admin bleiben draussen.
 */
import { readEntry, isPublished, shouldIndex, readSingleton } from './content.js';
import {
  PUBLISHED_LANGS,
  HREFLANG_MAP,
  OG_LOCALE_MAP,
  BUILD_LANGS,
  switchLangPath,
} from './languages.js';

const READ_ENTRY_COLLECTIONS = [
  'unterkuenfte',
  'camping',
  'gastro',
  'orte',
  'sehenswuerdigkeiten',
  'regionen',
  'events',
  'magazin',
  'erlebnisse',
];

const SITEMAP_QUALITY_COLLECTIONS = [
  'unterkuenfte',
  'camping',
  'gastro',
  'orte',
  'sehenswuerdigkeiten',
];

const SITEMAP_EXCLUDED = new Set(['suche', '404', '500', 'login', 'dashboard', 'admin']);

function pathnameOf(input) {
  if (typeof input !== 'string' || !input) return '/';
  if (/^https?:\/\//i.test(input)) {
    try { return new URL(input).pathname || '/'; }
    catch { return '/'; }
  }
  return input.split('?')[0].split('#')[0] || '/';
}

export function parseLocalizedPath(input, explicitLocale) {
  let pathname = pathnameOf(input);
  if (!pathname.startsWith('/')) pathname = `/${pathname}`;
  pathname = pathname.replace(/\/+/g, '/');

  const segments = pathname.split('/').filter(Boolean);
  let locale = null;
  let rest = segments;
  if (segments.length && PUBLISHED_LANGS.includes(segments[0])) {
    locale = segments[0];
    rest = segments.slice(1);
  } else if (explicitLocale && PUBLISHED_LANGS.includes(explicitLocale)) {
    locale = explicitLocale;
  } else if (BUILD_LANGS.length === 1) {
    locale = BUILD_LANGS[0];
  } else {
    locale = 'de';
  }

  const collection = rest[0] || null;
  const slug = rest.length === 2 ? rest[1] : null;
  const isEntryDetail = Boolean(slug && (READ_ENTRY_COLLECTIONS.includes(collection) || collection === 'bezirke'));

  return { pathname, locale, segments: rest, collection, slug, isEntryDetail };
}

export function localeUrlSlug(entry, directorySlug) {
  const fromEntry = typeof entry?.slug === 'string' ? entry.slug.trim() : '';
  return fromEntry || directorySlug;
}

function variantSlug(collection, slug, locale) {
  if (collection === 'bezirke') {
    const data = readSingleton('bezirke', locale);
    return data && data[slug] ? slug : null;
  }
  const entry = readEntry(collection, slug, locale);
  if (!entry || !isPublished(entry)) return null;
  return localeUrlSlug(entry, slug);
}

function replaceDetailSlug(pathname, slug) {
  const parts = pathname.split('/');
  let idx = parts.length - 1;
  while (idx >= 0 && parts[idx] === '') idx -= 1;
  if (idx >= 0) parts[idx] = slug;
  return parts.join('/') || '/';
}

export function detailAlternateHref(pathname, fromLocale, toLocale, toSlug) {
  const path = toSlug ? replaceDetailSlug(pathname, toSlug) : pathname;
  return switchLangPath(path, fromLocale, toLocale);
}

function linkFor(code, href) {
  return {
    code,
    hreflang: HREFLANG_MAP[code] || code,
    href,
    ogLocale: OG_LOCALE_MAP[code] || code,
  };
}

export function pickXDefaultHref(links) {
  if (!links.length) return null;
  const de = links.find((link) => link.code === 'de');
  return (de || links[0]).href;
}

export function hreflangAlternates({ path, locale, noindex = false, availableLanguages = null } = {}) {
  if (noindex) return { links: [], xDefault: null };

  const parsed = parseLocalizedPath(path, locale);
  const allow = Array.isArray(availableLanguages) ? new Set(availableLanguages) : null;
  const langs = PUBLISHED_LANGS.filter((code) => !allow || allow.has(code));

  let links;
  if (parsed.isEntryDetail) {
    links = [];
    for (const lang of langs) {
      const slug = variantSlug(parsed.collection, parsed.slug, lang);
      if (!slug) continue;
      links.push(linkFor(lang, detailAlternateHref(parsed.pathname, parsed.locale, lang, slug)));
    }
  } else {
    links = langs.map((lang) => linkFor(
      lang,
      switchLangPath(parsed.pathname, parsed.locale, lang),
    ));
  }

  return { links, xDefault: pickXDefaultHref(links) };
}

export function includeInSitemap(pageUrl) {
  const parsed = parseLocalizedPath(pageUrl);
  const top = parsed.segments[0];
  if (top && SITEMAP_EXCLUDED.has(top)) return false;

  if (parsed.isEntryDetail) {
    if (parsed.collection === 'bezirke') {
      return variantSlug('bezirke', parsed.slug, parsed.locale) !== null;
    }
    const entry = readEntry(parsed.collection, parsed.slug, parsed.locale);
    if (!entry || !isPublished(entry)) return false;
    if (SITEMAP_QUALITY_COLLECTIONS.includes(parsed.collection)) {
      return shouldIndex(entry, parsed.collection);
    }
  }

  return true;
}

export function sitemapAlternateLinks(pageUrl) {
  const { links, xDefault } = hreflangAlternates({ path: pageUrl, noindex: false });
  const out = links.map((link) => ({ lang: link.hreflang, url: link.href }));
  if (xDefault) out.push({ lang: 'x-default', url: xDefault });
  return out;
}
