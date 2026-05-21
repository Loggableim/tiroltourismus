# Plan: Language Selector Integration (3 Varianten)

## Übersicht

Integration von **3 Language-Selector-Varianten** in `BaseLayout.astro`:
1. **Topbar Dropdown** (Mockup 1) — primär, für Desktop
2. **Floating Globe** (Mockup 3) — sekundär, immer sichtbar
3. **Footer Flaggen-Reihe** (Mockup 5) — Abschluss, für alle Seiten

Zielsprachen: DE (default), EN, FR, IT, NL (+5 später erweiterbar)
Aktuell existieren: `src/data/` (DE), `src/data/en/`, `src/data/fr/`

---

## Task 1: Language Config zentralisieren

**Datei:** `src/lib/languages.js` (neu)

```js
export const LANGUAGES = [
  { code: 'de', flag: '🇩🇪', name: 'Deutsch', nameNative: 'Deutsch', default: true },
  { code: 'en', flag: '🇬🇧', name: 'English', nameNative: 'English' },
  { code: 'fr', flag: '🇫🇷', name: 'Français', nameNative: 'Français' },
  { code: 'it', flag: '🇮🇹', name: 'Italiano', nameNative: 'Italiano' },
  { code: 'nl', flag: '🇳🇱', name: 'Nederlands', nameNative: 'Nederlands' },
];

export const DEFAULT_LOCALE = 'de';
export function isDefaultLocale(locale) { return locale === DEFAULT_LOCALE; }
export function localePrefix(locale) { return isDefaultLocale(locale) ? '' : `/${locale}`; }
export function switchLangPath(currentPath, fromLocale, toLocale) {
  // Entfernt current locale prefix, fügt neuen hinzu
  const prefix = fromLocale === DEFAULT_LOCALE ? '' : `/${fromLocale}`;
  const withoutPrefix = currentPath.startsWith(prefix)
    ? currentPath.slice(prefix.length) || '/'
    : currentPath;
  if (toLocale === DEFAULT_LOCALE) return withoutPrefix;
  if (withoutPrefix === '/') return `/${toLocale}`;
  return `/${toLocale}${withoutPrefix}`;
}
```

Nutzen: Alle 3 Komponenten plus BaseLayout importieren aus einer Source of Truth.

---

## Task 2: BaseLayout.astro — Umbau

### 2a. Frontmatter-Änderungen

- `import { LANGUAGES, switchLangPath } from '../lib/languages.js';`
- `switchLangPath()` Funktion (Zeilen 40-46) ersetzen durch Import
- `locale` bleibt als Prop, `langCode`, `fullLocale`, `localePrefix` bleiben

### 2b. hreflang-Tags (Zeilen 161-162) erweitern

Aktuell nur DE + EN. Alle 5 Sprachen als `<link rel="alternate">` ausgeben:

```astro
{LANGUAGES.map(l => (
  <link rel="alternate" href={`https://www.tirol-tourismus.at${switchLangPath(currentPath, locale, l.code)}`} hreflang={l.code} />
))}
```

### 2c. Topbar-Dropdown (Zeilen 277-279 ersetzen)

**ALT:**
```astro
<div class="topbar-lang">
  <a href={switchLangPath('de')} class={locale === 'de' ? 'active' : ''}>DE</a>
  <a href={switchLangPath('en')} class={locale === 'en' ? 'active' : ''}>EN</a>
</div>
```

**NEU:**
```astro
<div class="topbar-lang-selector" id="langSelector">
  <button class="lang-current" onclick="toggleLang()">
    <span class="lang-flag">{LANGUAGES.find(l => l.code === locale).flag}</span>
    <span class="lang-code">{locale.toUpperCase()}</span>
    <svg class="lang-chevron" viewBox="0 0 10 6" width="10" height="6"><path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
  </button>
  <div class="lang-dropdown">
    {LANGUAGES.map(l => (
      <a href={switchLangPath(currentPath, locale, l.code)} class:list={{ active: l.code === locale }}>
        <span class="lang-flag">{l.flag}</span>
        <span class="lang-name">{l.nameNative}</span>
      </a>
    ))}
  </div>
</div>
```

CSS (im `<style is:inline>` Bereich von BaseLayout einfügen, nach `.topbar`-Styles):
```css
.topbar-lang-selector{position:relative;display:flex;align-items:center}
.lang-current{display:flex;align-items:center;gap:5px;padding:3px 8px;border-radius:6px;cursor:pointer;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.08);color:rgba(255,255,255,.8);font-size:11px;font-weight:600;letter-spacing:.5px;text-transform:uppercase;transition:all .2s}
.lang-current:hover{background:rgba(255,255,255,.12)}
.lang-flag{font-size:14px;line-height:1}
.lang-chevron{transition:transform .2s;opacity:.6}
.lang-selector.open .lang-chevron{transform:rotate(180deg)}
.lang-dropdown{position:absolute;top:100%;left:0;margin-top:4px;min-width:140px;background:rgba(10,10,18,.95);backdrop-filter:blur(24px);border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:4px;display:none;flex-direction:column;box-shadow:0 12px 40px rgba(0,0,0,.5);z-index:2000}
.lang-selector.open .lang-dropdown{display:flex}
.lang-dropdown a{display:flex;align-items:center;gap:8px;padding:7px 12px;border-radius:6px;font-size:12px;color:rgba(255,255,255,.6);text-decoration:none;transition:all .15s}
.lang-dropdown a:hover{background:rgba(255,255,255,.06);color:#fff}
.lang-dropdown a.active{color:var(--pink);font-weight:600;background:rgba(255,20,147,.1)}
```

JS (im existierenden `<script is:inline>` oder neuem Block):
```js
// Language selector toggle
document.addEventListener('click', function(e) {
  const sel = document.getElementById('langSelector');
  if (!sel) return;
  if (sel.contains(e.target) && e.target.closest('.lang-current')) {
    sel.classList.toggle('open');
  } else {
    sel.classList.remove('open');
  }
});
```

### 2d. Floating Globe (neuer Block vor Footer)

Nach dem `<slot />` (Zeile 352) einfügen:

```astro
<!-- ═══ FLOATING LANGUAGE GLOBE ═══ -->
<div class="floating-lang" id="floatingLang">
  <button class="floating-lang-btn" onclick="document.getElementById('floatingLang').classList.toggle('open')" aria-label="Sprache ändern">
    🌐
  </button>
  <div class="floating-lang-panel">
    {LANGUAGES.map(l => (
      <a href={switchLangPath(currentPath, locale, l.code)} class:list={{ active: l.code === locale }}>
        <span class="fl-flag">{l.flag}</span>
        <span class="fl-name">{l.name}</span>
        {l.code === locale && <span class="fl-check">✓</span>}
      </a>
    ))}
  </div>
</div>
```

CSS:
```css
.floating-lang{position:fixed;right:24px;top:50%;transform:translateY(-50%);z-index:999}
.floating-lang-btn{width:46px;height:46px;border-radius:50%;background:rgba(10,10,18,.5);backdrop-filter:blur(20px);border:1px solid var(--glass-border);display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:20px;transition:all .3s var(--ease);color:var(--text);box-shadow:0 6px 24px rgba(0,0,0,.25)}
.floating-lang-btn:hover{transform:scale(1.1);border-color:var(--pink)}
.floating-lang-panel{position:absolute;right:56px;top:50%;transform:translateY(-50%);background:rgba(10,10,18,.95);backdrop-filter:blur(24px);border:1px solid var(--glass-border);border-radius:var(--radius-lg);padding:6px;display:none;flex-direction:column;gap:2px;min-width:180px;box-shadow:0 16px 48px rgba(0,0,0,.5)}
.floating-lang.open .floating-lang-panel{display:flex}
.floating-lang-panel a{display:flex;align-items:center;gap:10px;padding:9px 14px;border-radius:8px;font-size:12px;color:var(--text2);text-decoration:none;transition:all .15s}
.floating-lang-panel a:hover{background:var(--glass);color:var(--text)}
.floating-lang-panel a.active{color:var(--pink);font-weight:600;background:rgba(255,20,147,.08)}
.fl-flag{font-size:18px;width:22px;text-align:center}
.fl-name{flex:1}
.fl-check{color:var(--pink);font-size:12px}
@media(max-width:768px){.floating-lang{display:none}}
```

### 2e. Footer Flaggen-Reihe (Zeilen 381-388 Bereich)

Nach dem Footer-Social-Block (nach `footer-social`) in der Brand-Spalte einfügen:

```astro
<div class="footer-lang">
  <span class="footer-lang-label">🌐</span>
  {LANGUAGES.map(l => (
    <a href={switchLangPath(currentPath, locale, l.code)} class:list={{ active: l.code === locale }}>
      {l.flag} {l.name}
    </a>
  ))}
</div>
```

CSS:
```css
.footer-lang{display:flex;align-items:center;gap:6px;margin-top:16px;flex-wrap:wrap}
.footer-lang-label{font-size:14px;margin-right:2px}
.footer-lang a{display:flex;align-items:center;gap:5px;padding:4px 10px;border-radius:100px;font-size:11px;font-weight:500;color:var(--text3);text-decoration:none;transition:all .2s;background:var(--surface);border:1px solid var(--glass-border)}
.footer-lang a:hover{color:var(--text);border-color:var(--pink)}
.footer-lang a.active{color:var(--pink);background:rgba(255,20,147,.08);border-color:rgba(255,20,147,.25)}
```

---

## Task 3: `[locale]/index.astro` anpassen

Aktuell `getStaticPaths()` gibt nur `['de', 'en']` zurück. Für FR/IT/NL später erweitern — erstmal lassen wie es ist, da noch keine übersetzten Daten existieren. Der Language Selector zeigt alle 5 Sprachen an, aber FR/IT/NL-Seiten 404en bis die Daten da sind.

Optional: FR/IT/NL-Links im Selector mit `noindex` markieren oder auf `de`-Version redirecten lassen.

---

## Task 4: Sprach-Code für `switchLangPath` verbessern

Die aktuelle Funktion (Z.40-46) kennt nur DE/EN. Neue generische Version:

```js
function switchLangPath(targetLang) {
  const current = Astro.url.pathname;
  // Remove current locale prefix (if any)
  const localePattern = locale === 'de' ? '' : `/${locale}`;
  const withoutPrefix = localePattern
    ? current.replace(new RegExp(`^${localePattern}(/|$)`), '/')
    : current;
  // Add target locale prefix
  if (targetLang === 'de') return withoutPrefix;
  if (withoutPrefix === '/') return `/${targetLang}`;
  return `/${targetLang}${withoutPrefix}`;
}
```

Oder import aus `languages.js`.

---

## Dateien-Übersicht

| Datei | Änderung |
|-------|----------|
| `src/lib/languages.js` | **NEU** — Language-Konfig + Helper |
| `src/layouts/BaseLayout.astro` | **EDIT** — Topbar-Dropdown + Floating Globe + Footer + hreflang |
| `mockups/language-selector/` | bleibt als Referenz |

---

## Reihenfolge der Umsetzung

1. `src/lib/languages.js` erstellen
2. `BaseLayout.astro` Frontmatter: Import + switchLangPath ersetzen
3. Topbar-Dropdown einbauen (HTML + CSS + JS)
4. Floating Globe einbauen (HTML + CSS)
5. Footer Flaggen einbauen (HTML + CSS)
6. hreflang-Tags erweitern
7. Test: Build, locale-switching prüfen

---

## Offene Fragen

- FR/IT/NL noch ohne Daten → Sollen die Flags trotzdem klickbar sein (führen zu 404)?
  → Vorschlag: anzeigen aber deaktiviert/transparent bis Daten da sind
- Floating Globe auf Mobile ausblenden? → Ja, via `@media(max-width:768px)`
