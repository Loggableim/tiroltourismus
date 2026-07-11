/**
 * languages.js — Zentrale Sprachkonfiguration für tiroltourismus.com
 *
 * Subdomain-Split-Architektur (2026-07-02):
 *   tiroltourismus.com      → de, en, fr  (Hauptprojekt)
 *   cs.tiroltourismus.com   → cs           (CS-Projekt)
 *   nl.tiroltourismus.com   → nl           (NL-Projekt)
 *
 * BUILD_LANGS env steuert, welche Sprachen gebaut werden.
 * Cloudflare Pages Build-Config pro Projekt:
 *   Hauptprojekt:  BUILD_LANGS=de,en,fr
 *   CS-Projekt:    BUILD_LANGS=cs
 *   NL-Projekt:    BUILD_LANGS=nl
 */

// ── Domain-Map: jede Sprache hat ihre eigene Domain ──
export const LANG_DOMAINS = {
  de: 'https://tiroltourismus.com',
  en: 'https://tiroltourismus.com',
  fr: 'https://tiroltourismus.com',
  it: 'https://tiroltourismus.com',
  es: 'https://tiroltourismus.com',
  zh: 'https://tiroltourismus.com',
  nl: 'https://nl.tiroltourismus.com',
  cs: 'https://cs.tiroltourismus.com',
};

// ── Alle 8 Sprachen (Metadaten) ──
export const LANGUAGES = [
  { code: 'de', flag: '🇩🇪', name: 'Deutsch',     nameNative: 'Deutsch',     default: true },
  { code: 'en', flag: '🇬🇧', name: 'English',     nameNative: 'English' },
  { code: 'fr', flag: '🇫🇷', name: 'Français',    nameNative: 'Français' },
  { code: 'it', flag: '🇮🇹', name: 'Italiano',    nameNative: 'Italiano' },
  { code: 'es', flag: '🇪🇸', name: 'Español',     nameNative: 'Español' },
  { code: 'zh', flag: '🇨🇳', name: '中文',         nameNative: '中文' },
  { code: 'nl', flag: '🇳🇱', name: 'Nederlands', nameNative: 'Nederlands', ready: false },
  { code: 'cs', flag: '🇨🇿', name: 'Čeština',  nameNative: 'Čeština',  ready: false },
];

// ── BUILD_LANGS env steuert, welche Sprachen gebaut werden ──
const buildLangsEnv = typeof process !== 'undefined' && process.env.BUILD_LANGS;
const BUILD_LANGS = buildLangsEnv
  ? buildLangsEnv.split(',').map(s => s.trim()).filter(Boolean)
  : ['de', 'en', 'fr', 'cs', 'nl']; // Default: Hauptprojekt mit CS+NL

// ready = true nur für Sprachen, die in diesem Build gebaut werden
LANGUAGES.forEach(l => {
  l.ready = BUILD_LANGS.includes(l.code);
});

export const LANGUAGES_READY = LANGUAGES.filter((l) => l.ready).map((l) => l.code);

// Default-Locale: bei Single-Lang-Builds ist das die einzige Sprache,
// bei Multi-Lang-Builds (Hauptprojekt) ist es 'de'.
export const DEFAULT_LOCALE = BUILD_LANGS.length === 1 ? BUILD_LANGS[0] : 'de';

/**
 * Gibt zurück ob ein Locale die Default-Sprache ist (kein Prefix in URLs)
 */
export function isDefaultLocale(locale) {
  return !locale || locale === DEFAULT_LOCALE;
}

/**
 * Locale-Prefix für URLs. 'de' → '', 'en' → '/en'
 */
export function localePrefix(locale) {
  return isDefaultLocale(locale) ? '' : `/${locale}`;
}

/**
 * Pfad von einer aktuellen Sprache zu einer Zielsprache umschalten.
 * Gibt absolute URL mit Subdomain zurück.
 *
 * Beispiele:
 *   switchLangPath('/gastro/taverna/', 'de', 'cs')
 *   → 'https://cs.tiroltourismus.com/gastro/taverna/'
 *
 *   switchLangPath('/en/gastro/taverna/', 'en', 'fr')
 *   → 'https://tiroltourismus.com/fr/gastro/taverna/'
 */
export function switchLangPath(currentPath, fromLocale, toLocale) {
  const langCodes = LANGUAGES.map(l => l.code).join('|');
  const prefixRegex = new RegExp(`^/(${langCodes})(/|$)`);
  const match = currentPath.match(prefixRegex);
  const withoutPrefix = match ? currentPath.slice(match[1].length + 1) || '/' : currentPath;

  const targetDomain = LANG_DOMAINS[toLocale] || LANG_DOMAINS.de;

  // Pfad mit Locale-Prefix bauen
  let path;
  if (isDefaultLocale(toLocale)) {
    path = withoutPrefix;
  } else if (withoutPrefix === '/') {
    path = `/${toLocale}`;
  } else {
    path = `/${toLocale}${withoutPrefix}`;
  }

  // Normalisieren: doppelte Slashes entfernen, trailing slash sicherstellen
  path = path.replace(/\/+/g, '/');
  if (path !== '/' && !path.endsWith('/')) path += '/';

  return `${targetDomain}${path}`;
}

/**
 * Prüft ob eine Sprache bereits übersetzte Daten hat.
 */
export function isLanguageReady(code) {
  return LANGUAGES_READY.includes(code);
}

/**
 * Prüft ob DE-Seiten im aktuellen Build gebaut werden sollen.
 * (Für DE-Routen ohne [locale]-Prefix)
 */
export function shouldBuildDe() {
  return BUILD_LANGS.includes('de');
}
