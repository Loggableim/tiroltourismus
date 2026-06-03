/**
 * languages.js — Zentrale Sprachkonfiguration für tiroltourismus.com
 * Alle 3 Selector-Komponenten (Topbar, Floating, Footer) nutzen diese Config.
 */

export const LANGUAGES = [
  { code: 'de', flag: '🇩🇪', name: 'Deutsch', nameNative: 'Deutsch', default: true, ready: true },
  { code: 'en', flag: '🇬🇧', name: 'English', nameNative: 'English', ready: true },
  { code: 'fr', flag: '🇫🇷', name: 'Français', nameNative: 'Français', ready: true },
  { code: 'it', flag: '🇮🇹', name: 'Italiano', nameNative: 'Italiano', ready: true },
  { code: 'es', flag: '🇪🇸', name: 'Español', nameNative: 'Español', ready: true },
  { code: 'zh', flag: '🇨🇳', name: '中文', nameNative: '中文', ready: true },
  // All 8 languages (DE/EN/FR/IT/ES/ZH/NL/CS) now active with full hreflang and routes.
  { code: 'nl', flag: '🇳🇱', name: 'Nederlands', nameNative: 'Nederlands', ready: true },
  { code: 'cs', flag: '🇨🇿', name: 'Czech', nameNative: 'Čeština', ready: true },
];

export const LANGUAGES_READY = LANGUAGES.filter((l) => l.ready).map((l) => l.code); // alle aktuell freigegebenen Sprachen routen
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
 * Erkennt automatisch Locale-Prefixe im Pfad (auch /de/ auf [locale]-Seiten).
 * Beispiele:
 *   switchLangPath('/en/regionen/', 'en', 'de') → '/regionen/'
 *   switchLangPath('/de/regionen/', 'de', 'en') → '/en/regionen/'
 *   switchLangPath('/regionen/', 'de', 'fr')    → '/fr/regionen/'
 *   switchLangPath('/', 'de', 'en')             → '/en/'
 */
export function switchLangPath(currentPath, fromLocale, toLocale) {
  // Detect and strip any configured locale prefix.
  const langCodes = LANGUAGES.map(l => l.code).join('|');
  const prefixRegex = new RegExp(`^\\/(${langCodes})(\\/|$)`);
  const match = currentPath.match(prefixRegex);
  const withoutPrefix = match ? currentPath.slice(match[1].length + 1) || '/' : currentPath;
  // Add target prefix
  if (isDefaultLocale(toLocale)) return withoutPrefix;
  if (withoutPrefix === '/') return `/${toLocale}`;
  return `/${toLocale}${withoutPrefix}`;
}

/**
 * Prüft ob eine Sprache bereits übersetzte Daten hat.
 * Für "coming soon"-Markierung im Selector.
 */
export function isLanguageReady(code) {
  return LANGUAGES_READY.includes(code);
}
