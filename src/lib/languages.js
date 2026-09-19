/**
 * languages.js — Zentrale Sprachkonfiguration für tiroltourismus.com
 *
 * Subdomain-Architektur (2026-09-19):
 *   tiroltourismus.com      → Landing/Hub (reduziert, SEO-optimiert, Vote für soon-Sprachen)
 *   de.tiroltourismus.com   → Deutsch (voll)
 *   en.tiroltourismus.com   → English (voll)
 *   fr.tiroltourismus.com   → Français (voll)
 *   cs.tiroltourismus.com   → Čeština (voll)
 *   nl.tiroltourismus.com   → Nederlands (voll)
 *
 * BUILD_LANGS env steuert, welche Sprache gebaut wird (Single-Lang-Builds).
 * Ohne BUILD_LANGS (Dev): Multi-Lang-Modus — de auf Root, andere mit Prefix.
 */

// ── Domain-Map: jede Sprache hat ihre eigene Subdomain ──
export const LANG_DOMAINS = {
  de: 'https://de.tiroltourismus.com',
  en: 'https://en.tiroltourismus.com',
  fr: 'https://fr.tiroltourismus.com',
  cs: 'https://cs.tiroltourismus.com',
  nl: 'https://nl.tiroltourismus.com',
  it: 'https://it.tiroltourismus.com',
  es: 'https://es.tiroltourismus.com',
  zh: 'https://zh.tiroltourismus.com',
  // soon-Sprachen: noch keine Subdomain — zeigen auf die Landing
  pl: 'https://tiroltourismus.com',
  hu: 'https://tiroltourismus.com',
  sk: 'https://tiroltourismus.com',
};

// ── Landing/Hub-Domain ──
export const LANDING_DOMAIN = 'https://tiroltourismus.com';

// ── Alle 8 Sprachen (Metadaten) ──
export const LANGUAGES = [
  { code: 'de', flag: '🇩🇪', name: 'Deutsch',     nameNative: 'Deutsch',     default: true },
  { code: 'en', flag: '🇬🇧', name: 'English',     nameNative: 'English' },
  { code: 'fr', flag: '🇫🇷', name: 'Français',    nameNative: 'Français' },
  { code: 'it', flag: '🇮🇹', name: 'Italiano',    nameNative: 'Italiano' },
  { code: 'es', flag: '🇪🇸', name: 'Español',     nameNative: 'Español' },
  { code: 'zh', flag: '🇨🇳', name: '中文',         nameNative: '中文' },
  { code: 'nl', flag: '🇳🇱', name: 'Nederlands', nameNative: 'Nederlands' },
  { code: 'cs', flag: '🇨🇿', name: 'Čeština',  nameNative: 'Čeština' },
];

// ── Veröffentlichte Sprachen (haben Subdomain + volle Inhalte) ──
export const PUBLISHED_LANGS = ['de', 'en', 'fr', 'cs', 'nl', 'it', 'es', 'zh'];

// ── Soon-Sprachen (Landing zeigt Vote-Button) ──
export const SOON_LANGS = ['pl', 'hu', 'sk'];

// ── BUILD_LANGS env steuert, welche Sprachen in diesem Build gebaut werden ──
const buildLangsEnv = typeof process !== 'undefined' && process.env.BUILD_LANGS;
const BUILD_LANGS = buildLangsEnv
  ? buildLangsEnv.split(',').map(s => s.trim()).filter(Boolean)
  : ['de', 'en', 'fr', 'cs', 'nl']; // Default (Dev): Multi-Lang

export { BUILD_LANGS };

// ready = true nur für Sprachen, die in diesem Build gebaut werden
LANGUAGES.forEach(l => {
  l.ready = BUILD_LANGS.includes(l.code);
});

export const LANGUAGES_READY = LANGUAGES.filter((l) => l.ready).map((l) => l.code);

// Default-Locale: bei Single-Lang-Builds ist das die einzige Sprache,
// bei Multi-Lang-Builds (Dev) ist es 'de'.
export const DEFAULT_LOCALE = BUILD_LANGS.length === 1 ? BUILD_LANGS[0] : 'de';

/**
 * Gibt zurück ob ein Locale die Default-Sprache ist (kein Prefix in URLs)
 */
export function isDefaultLocale(locale) {
  return !locale || locale === DEFAULT_LOCALE;
}

/**
 * Locale-Prefix für URLs. Single-Lang: immer '' (Root-Serving).
 * Multi-Lang: 'de' → '', 'en' → '/en'
 */
export function localePrefix(locale) {
  if (BUILD_LANGS.length === 1) return '';
  return isDefaultLocale(locale) ? '' : `/${locale}`;
}

/**
 * Static-Path-Parameter für [...locale]-Routen.
 * Single-Lang-Build:
 *   de  → []            (DE-Root-Seiten übernehmen)
 *   en  → [undefined]   (Root-Serving auf en.tiroltourismus.com)
 * Multi-Lang (Dev):
 *   → ['en', 'fr', ...] (mit Prefix; de übernimmt Root)
 */
export function localeParams() {
  if (BUILD_LANGS.length === 1) {
    return BUILD_LANGS[0] === 'de' ? [] : [undefined];
  }
  return BUILD_LANGS.filter(l => l !== 'de');
}

/**
 * Pfad von einer aktuellen Sprache zu einer Zielsprache umschalten.
 * Gibt absolute URL mit Subdomain zurück.
 *
 * Beispiele (Single-Lang-Build en):
 *   switchLangPath('/gastro/taverna/', 'en', 'de')
 *   → 'https://de.tiroltourismus.com/gastro/taverna/'
 *
 * Beispiele (Multi-Lang Dev):
 *   switchLangPath('/en/gastro/taverna/', 'en', 'fr')
 *   → 'https://fr.tiroltourismus.com/fr/gastro/taverna/'
 */
export function switchLangPath(currentPath, fromLocale, toLocale) {
  const langCodes = LANGUAGES.map(l => l.code).join('|');
  const prefixRegex = new RegExp(`^/(${langCodes})(/|$)`);
  const match = currentPath.match(prefixRegex);
  const withoutPrefix = match ? currentPath.slice(match[1].length + 1) || '/' : currentPath;

  const targetDomain = LANG_DOMAINS[toLocale] || LANDING_DOMAIN;

  // Pfad bauen: Single-Lang → immer Root; Multi-Lang → Prefix für Non-Default
  let path = withoutPrefix;
  if (BUILD_LANGS.length > 1 && !isDefaultLocale(toLocale)) {
    path = withoutPrefix === '/' ? `/${toLocale}` : `/${toLocale}${withoutPrefix}`;
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

// ── SEO-Maps ──
export const HREFLANG_MAP = { de:'de-AT', en:'en-US', fr:'fr-FR', it:'it-IT', es:'es-ES', zh:'zh-CN', nl:'nl-NL', cs:'cs-CZ' };
export const OG_LOCALE_MAP = { de:'de_AT', en:'en_US', fr:'fr_FR', it:'it_IT', es:'es_ES', zh:'zh_CN', nl:'nl_NL', cs:'cs_CZ' };
