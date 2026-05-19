# SEO Meta Audit — tiroltourismus.com (Astro 5)

**Datum:** 2026-05-19  
**Prüfer:** Hermes Agent D1  
**Projekt:** F:/tiroltourismus — ~5400 Seiten, JSON-driven

---

## 1. Meta Description — WIRD NICHT AUSGEGEBEN (KRITISCH)

**Datei:** `src/layouts/BaseLayout.astro:158`

```astro
<meta name="description" content={siteDesc}>
```

`siteDesc` ist der globale Fallback (Zeile 35). Der Page-spezifische `description`-Prop wird **ignoriert**.  
Betrifft auch OpenGraph (Zeile 175) und Twitter (Zeile 186). Alle ~5400 Seiten teilen dieselbe generische Description.

| Betroffene Tags | Aktuell | Soll |
|---|---|---|
| `<meta name="description">` | globaler Fallback | `{description ?? siteDesc}` |
| `<meta property="og:description">` | globaler Fallback | `{description ?? siteDesc}` |
| `<meta name="twitter:description">` | globaler Fallback | `{description ?? siteDesc}` |

**Fix:**
```astro
<meta name="description" content={description ?? siteDesc}>
<meta property="og:description" content={description ?? siteDesc} />
<meta name="twitter:description" content={description ?? siteDesc} />
```

> `generateMetaDescription()` in `seo.js` produziert bereits gute 120–160-Zeichen-Descriptions — sie werden nur nie ins HTML geschrieben.

---

## 2. Domain-Mismatch: astro.config ≠ BaseLayout (KRITISCH)

| Ort | Domain |
|---|---|
| `astro.config.mjs:8` `site:` | `https://tiroltourismus.com` |
| `BaseLayout.astro:49` `siteURL` | `https://www.tirol-tourismus.at` |
| `robots.txt:5` Sitemap | `https://tiroltourismus.com/sitemap-index.xml` |

**Folgen:**
- Sitemap generiert URLs mit `tiroltourismus.com`, aber JSON-LD (WebSite, Organization) und Canonical-URLs referenzieren `www.tirol-tourismus.at`
- Suchmaschinen sehen unterschiedliche Domains → Duplicate-Content-Risiko, Confusion Signals

**Fix:** Eine kanonische Domain festlegen und an allen drei Stellen konsistent setzen. Empfehlung: `https://tiroltourismus.com` (da sitemap/robots schon darauf zeigen).

---

## 3. Kein JSON-LD BreadcrumbList

**Status:** Breadcrumbs werden visuell über `Breadcrumbs.astro` gerendert (sauber, mit Startseite-Präfix), aber **kein** `schema.org/BreadcrumbList` JSON-LD.

**Fundorte mit Breadcrumbs:**
- Alle Detail-Pages via `DetailPage.astro` → `Breadcrumbs.astro`
- FAQ-Pages, einige Index-Pages (teils inline, teils via Komponente)

**Fix:** In `Breadcrumbs.astro` oder `BaseLayout.astro` eine BreadcrumbList-JSON-LD generieren:
```js
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": items.map((item, i) => ({
    "@type": "ListItem",
    "position": i + 1,
    "name": item.label,
    "item": item.href ? siteURL + item.href : undefined,
  })),
}
```

---

## 4. Kein Entity-spezifisches JSON-LD auf Detailseiten

| Collection | Mögliches Schema | Status |
|---|---|---|
| Campingplätze | `LodgingBusiness` / `Campground` | ❌ Fehlt |
| Unterkünfte | `Hotel` / `LodgingBusiness` | ❌ Fehlt |
| Regionen | `TouristDestination` | ❌ Fehlt |
| Orte | `City` / `Place` | ❌ Fehlt |
| Gastro | `Restaurant` / `FoodEstablishment` | ❌ Fehlt |
| Sehenswürdigkeiten | `TouristAttraction` / `LandmarksOrHistoricalBuildings` | ❌ Fehlt |
| Events | `Event` | ❌ Fehlt |
| FAQ | `FAQPage` | ✅ Vorhanden |

**Fix:** `DetailPage.astro` könnte entity-spezifisches JSON-LD aus den Entry-Daten generieren und an `BaseLayout` übergeben. Adress-Daten (ort, adresse, plz, koordinaten) sind in den meisten Collections vorhanden.

---

## 5. EN-Locale-Detailseiten nur für Regionen

Nur `[locale]/regionen/[slug].astro` unterstützt EN.  
Alle anderen Collections (camping, unterkuenfte, gastro, erlebnisse, events, orte, sehenswuerdigkeiten) haben **keine** `[locale]`-Routen für Detailseiten → englische Besucher sehen deutschen Content.

**Fix:** Entweder `[locale]`-Routen für alle Collections bauen, oder `hreflang`-Tags korrekt auf die jeweils verfügbaren Sprachversionen beschränken (aktuell zeigen sie auf nicht-existente Seiten).

---

## 6. seo.js — solide Basis, kleine Verbesserungen

**Positiv:**
- Collection-spezifische CTAs mit Emoji
- Intelligente Satz-Extraktion (schwache Einleitungen werden übersprungen)
- Truncation an Satzgrenzen (nicht mitten im Wort)
- DE/EN-Locale-Support
- Ziel 120–160 Zeichen wird eingehalten

**Verbesserungsvorschläge:**
- Emoji in CTAs (✅, 🏔️, 🍽️) → nicht alle Search Engines rendern sie in SERPs; optional als Fallback ohne Emoji
- `extractDescription()` verwendet nur den ersten guten Satz → könnte bei sehr kurzen Sätzen mager wirken. Fallback auf 2 Sätze wenn < 80 Zeichen
- Magazin-Fallback (Zeile 242) ist sehr generisch: `"Spannender Magazinbeitrag über {name}"` — hier könnte man `entry.teaser` priorisieren und kürzen

---

## 7. Title-Tag: Suffix inkonsistent

`BaseLayout.astro:157`: `<title>{title} – tiroltourismus.com</title>`

Branding-Suffix ist `tiroltourismus.com`, aber `siteName` in Zeile 48 ist `'Tirol Tourismus'` und die Domain ist (laut JSON-LD) `www.tirol-tourismus.at`.  
Uneinheitliches Branding in SERPs.

**Fix:** `siteName` und Title-Suffix auf die kanonische Domain abstimmen, z.B. `Tirol Tourismus` (ohne Domain im Title).

---

## 8. robots.txt — Sitemap-Referenz prüfen

```txt
Sitemap: https://tiroltourismus.com/sitemap-index.xml
```

Astro-Sitemap (`@astrojs/sitemap`) generiert standardmäßig `/sitemap-index.xml` und `/sitemap-0.xml`.  
→ Pfad korrekt, Domain siehe Finding #2.

---

## 9. hreflang — potenziell broken

`BaseLayout.astro:161–162`:
```astro
<link rel="alternate" href={currentPath.replace(/^\/en(\/|$)/, '/') || '/'} hreflang="de" />
<link rel="alternate" href={`/en${currentPath.startsWith('/en') ? currentPath.replace('/en', '') : currentPath === '/' ? '' : currentPath}`} hreflang="en" />
```

- EN-Alternate wird immer ausgegeben, auch wenn keine EN-Version existiert (siehe Finding #5)
- `hreflang="x-default"` fehlt

**Fix:** `x-default` hinzufügen, auf `de` verweisend. Nur dann EN-Alternate ausgeben, wenn tatsächlich eine EN-Seite existiert.

---

## 10. og:image — kein Fallback

Nur gesetzt wenn `ogImage`-Prop übergeben wird. Kein Default-OG-Image für Seiten ohne Hero-Bild (z.B. Impressum, AGB, 404, Suche).

**Fix:** Fallback `ogImage` auf ein Standard-OG-Image (z.B. `/brand/og-default.jpg`) setzen.

---

## Zusammenfassung

| # | Finding | Schwere |
|---|---|---|
| 1 | Meta-Description wird nicht ausgegeben | 🔴 KRITISCH |
| 2 | Domain-Mismatch astro.config vs. BaseLayout | 🔴 KRITISCH |
| 3 | Kein BreadcrumbList-JSON-LD | 🟡 Mittel |
| 4 | Kein Entity-JSON-LD (Hotel, Restaurant, etc.) | 🟡 Mittel |
| 5 | EN-Detailseiten nur für Regionen | 🟡 Mittel |
| 6 | seo.js kleine Verbesserungen | 🟢 Niedrig |
| 7 | Title-Suffix inkonsistent mit Domain | 🟢 Niedrig |
| 8 | robots.txt Sitemap-Ref ok (abgesehen von Domain) | 🟢 OK |
| 9 | hreflang auf nicht-existente EN-Seiten | 🟡 Mittel |
| 10 | Kein og:image-Fallback | 🟢 Niedrig |

**Sofort-Maßnahmen:** #1 und #2 beheben — das sind Showstopper für SEO.
