/**
 * languages.js — Zentrale Sprachkonfiguration für tiroltourismus.com
 * Alle 3 Selector-Komponenten (Topbar, Floating, Footer) nutzen diese Config.
 *
 * Cloudflare Pages Free/Pro limit: 20,000 files per deploy.
 * With 8 languages × ~5,500 pages each = 44,000 files — over limit.
 * ES/ZH/NL/CS set to ready:false until we upgrade to Business plan.
 */

export const LANGUAGES = [
  { code: 'de', flag: '🇩🇪', name: 'Deutsch', nameNative: 'Deutsch', default: true, ready: true },
  { code: 'en', flag: '🇬🇧', name: 'English', nameNative: 'English', ready: true },
  { code: 'fr', flag: '🇫🇷', name: 'Français', nameNative: 'Français', ready: true },
  { code: 'it', flag: '🇮🇹', name: 'Italiano', nameNative: 'Italiano', ready: false },
  // ES/ZH/NL/CS ready:false — Cloudflare Pages 20k file limit
  // Re-enable when upgrading to Business plan
  { code: 'es', flag: '🇪🇸', name: 'Español', nameNative: 'Español', ready: false },
  { code: 'zh', flag: '🇨🇳', name: '中文', nameNative: '中文', ready: false },
  { code: 'nl', flag: '🇳🇱', name: 'Nederlands', nameNative: 'Nederlands', ready: false },
  { code: 'cs', flag: '🇨🇿', name: 'Czech', nameNative: 'Čeština', ready: false },
];

export const LANGUAGES_READY = LANGUAGES.filter((l) => l.ready).map((l) => l.code);
export const DEFAULT_LOCALE = 'de';

/**
 * Gibt zurück ob ein Locale die Standard-Sprache ist (de → kein Prefix)
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
 */
export function switchLangPath(currentPath, fromLocale, toLocale) {
  const langCodes = LANGUAGES.map(l => l.code).join('|');
  // RegEx: ^/de/ oder ^/en/ usw. am Anfang des Pfads erkennen und entfernen.
  // Wichtig: KEINE doppelten Backslashes — new RegExp() braucht kein Escaping
  // für '/' wie im Literal /pattern/. Einfach '^/(langCodes)(/|$)'.
  const prefixRegex = new RegExp(`^/(${langCodes})(/|$)`);
  const match = currentPath.match(prefixRegex);
  const withoutPrefix = match ? currentPath.slice(match[1].length + 1) || '/' : currentPath;
  if (isDefaultLocale(toLocale)) return withoutPrefix;
  if (withoutPrefix === '/') return `/${toLocale}`;
  return `/${toLocale}${withoutPrefix}`;
}

/**
 * Prüft ob eine Sprache bereits übersetzte Daten hat.
 */
export function isLanguageReady(code) {
  return LANGUAGES_READY.includes(code);
}
