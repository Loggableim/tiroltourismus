# SEO-Richtlinie – TirolTourismus

> **Projekt:** F:/tiroltourismus  
> **Stand:** 2026-05-18  
> **Geltungsbereich:** Alle öffentlichen Collections (regionen, orte, sehenswuerdigkeiten, gastro, unterkuenfte, camping, erlebnisse, events, magazin)

---

## 1. Struktur der Seite (Architektur-Übersicht)

```
STARTSEITE (/)
├── Regionen (/regionen/)
│   └── Einzelregion (/regionen/{region-slug}/)
├── Orte (/orte/)
│   └── Einzelort (/orte/{ort-slug}/)
├── Sehenswürdigkeiten (/sehenswuerdigkeiten/)
│   └── Einzelsehenswürdigkeit (/sehenswuerdigkeiten/{slug}/)
├── Gastronomie (/gastro/)
│   └── Einzelbetrieb (/gastro/{slug}/)
├── Unterkünfte (/unterkuenfte/)
│   └── Einzelunterkunft (/unterkuenfte/{slug}/)
├── Camping (/camping/)
│   └── Einzelplatz (/camping/{slug}/)
├── Erlebnisse (/erlebnisse/)
│   └── Einzelerlebnis (/erlebnisse/{slug}/)
├── Events (/events/)
│   └── Einzelevent (/events/{event-slug}/)
└── Magazin (/magazin/)
    └── Artikel (/magazin/{artikel-slug}/)
```

**Themencluster** (als Taxonomy / Filter):  
`/themen/wandern/`, `/themen/ski/`, `/themen/familie/`, `/themen/kulinarik/`, `/themen/wellness/`, `/themen/kultur/`, `/themen/events/`, `/themen/natur/`

**Flache Hierarchie** – maximal 2 Ebenen tief, um Crawl-Tiefe niedrig zu halten.

---

## 2. URL-Strategie

| Regel | Umsetzung |
|-------|-----------|
| **Sprache** | Kein Sprach-Prefix (deutsch = default), ggf. `/en/` für englische Version |
| **Slug-Syntax** | Kleinschrift, Bindestriche statt Unterstriche, keine Umlaute (ä→ae, ö→oe, ü→ue, ß→ss) |
| **Collection-Prefix** | Jeder Inhaltstyp bekommt einen eigenen Prefix (s. Architektur) |
| **Paginated Listings** | `/regionen/seite/2/` – kanonisch auf Seite 1 via `<link rel=canonical>` |
| **Filter-/Facetten-URLs** | `?thema=wandern&ort=...` – **nicht indexieren** via `noindex` oder robots.txt |
| **Keine Trailing-Slashes** | Einheitlich mit oder ohne – Empfehlung: **mit** Slash (trailing slash beibehalten) |
| **Keine IDs in URLs** | Nur sprechende Slugs (keine `/detail/1234`) |

---

## 3. Title-Tag-Format pro Collection

> `{Hauptkeyword} | {Subkeyword} | Tirol Tourismus`

| Collection | Format | Beispiel |
|-----------|--------|---------|
| **Startseite** | `{Tagline} | Tirol Tourismus` | `Urlaub in Tirol | Offizielles Tourismusportal` |
| **Regionen (Liste)** | `Regionen in Tirol | {Bundesland} | Tirol Tourismus` | `Regionen in Tirol | Urlaubsregionen von A–Z` |
| **Region (Detail)** | `{Region} | Urlaub in {Region}, Tirol` | `Zillertal | Urlaub im Zillertal, Tirol` |
| **Orte (Liste)** | `Orte in Tirol | {Überschrift}` | `Orte & Gemeinden in Tirol | Alle Orte von A–Z` |
| **Ort (Detail)** | `{Ort} | Urlaub in {Ort}, Tirol` | `Mayrhofen | Urlaub in Mayrhofen, Tirol` |
| **Sehenswürdigkeiten (Liste)** | `Sehenswürdigkeiten in Tirol | {Top-Attraktionen}` | `Sehenswürdigkeiten in Tirol | Die Top 25 Attraktionen` |
| **Sehenswürdigkeit (Detail)** | `{Name} | Sehenswürdigkeit in {Ort}, Tirol` | `Swarovski Kristallwelten | Sehenswürdigkeit in Wattens` |
| **Gastronomie (Liste)** | `Restaurants in Tirol | {Küchenrichtung}` | `Restaurants & Gasthäuser in Tirol | Gutbürgerlich & Regional` |
| **Gastro (Detail)** | `{Restaurant-Name} | {Ort} | Gastronomie Tirol` | `Gasthof Post | Mayrhofen | Gastronomie Tirol` |
| **Unterkünfte (Liste)** | `Unterkünfte in Tirol | {Kategorie}` | `Hotels & Ferienwohnungen in Tirol | Jetzt buchen` |
| **Unterkunft (Detail)** | `{Unterkunft} | {Ort} | {Sterne/Eigenschaft}` | `Hotel Edelweiß | Mayrhofen | 4-Sterne-Hotel` |
| **Camping (Liste)** | `Campingplätze in Tirol | {Region}` | `Campingplätze in Tirol | Natur pur erleben` |
| **Camping (Detail)** | `{Campingplatz} | Camping in {Ort}, Tirol` | `Camping Aufenfeld | Camping in Mayrhofen` |
| **Erlebnisse (Liste)** | `Erlebnisse in Tirol | {Thema}` | `Erlebnisse & Aktivitäten in Tirol | Wandern, Ski & mehr` |
| **Erlebnis (Detail)** | `{Erlebnis-Titel} in {Ort} | Tirol` | `Gletscherbahn Hintertux | Ganzjährig Skifahren` |
| **Events (Liste)** | `Veranstaltungen in Tirol | {Monat/Jahr}` | `Events & Veranstaltungen in Tirol | 2026` |
| **Event (Detail)** | `{Event-Name} | {Datum} | Tirol Events` | `Almabtrieb Mayrhofen | September 2026 | Tirol` |
| **Magazin (Liste)** | `Magazin | {Rubrik} | Tirol Tourismus` | `Magazin | Wandern in Tirol | Tipps & Inspiration` |
| **Magazin (Detail)** | `{Artikel-Titel} | Tirol Magazin` | `Die 10 schönsten Wanderwege im Zillertal | Tirol Magazin` |

**Title-Längen-Limit:** Maximal 60 Zeichen (Desktop) – wichtigsten Keywords vorne platzieren.  
**Brand:** „Tirol Tourismus“ am Ende (Trennzeichen `|`).

---

## 4. Meta-Description-Format pro Collection

> Maximal 155–160 Zeichen, Call-to-Action, unique.

| Collection | Format | Beispiel |
|-----------|--------|---------|
| **Startseite** | Kurze Zusammenfassung + CTA | `Entdecken Sie Tirol: atemberaubende Natur, alpines Flair & kulinarische Genüsse. Jetzt Ihren Traumurlaub planen!` |
| **Region (Liste)** | Überblick Regionen | `Von den Ötztaler Alpen bis zum Zillertal – alle Urlaubsregionen Tirols im Überblick. Finden Sie Ihre Lieblingsregion!` |
| **Region (Detail)** | Unique Selling Points der Region | `Erleben Sie das Zillertal: 300 km Wanderwege, Skigebiete & traditionelle Hütten. Ihr Urlaub im Zillertal beginnt hier.` |
| **Ort (Detail)** | Besonderheiten + Lage | `Mayrhofen – das Herz des Zillertals. Genießen Sie Bergpanorama, Skispaß & Après-Ski. Jetzt Urlaub buchen!` |
| **Sehenswürdigkeit (Detail)** | Was + Wo + Warum | `Swarovski Kristallwelten in Wattens: Tauchen Sie ein in die funkelnde Welt des Kristalls. Tickets & Infos hier.` |
| **Gastro (Detail)** | Küche + Ambiente + Adresse | `Gasthof Post in Mayrhofen: Tiroler Klassiker & internationale Spezialitäten. Jetzt Tisch reservieren!` |
| **Unterkunft (Detail)** | Ausstattung + Lage + Preis | `Hotel Edelweiß in Mayrhofen: 4-Sterne-Komfort mit Bergblick. Wellnessbereich & Halbpension. Jetzt buchen!` |
| **Camping (Detail)** | Lage + Ausstattung + Natur | `Camping Aufenfeld an der Ziller: Stellplätze mit Bergpanorama, moderner Sanitärbereich. Camping in Tirol.` |
| **Erlebnis (Detail)** | Aktivität + Ort + Dauer | `Gletscherbahn Hintertux: Ganzjährig Skivergnügen auf 3.250 m. Infos zu Preisen & Öffnungszeiten.` |
| **Event (Detail)** | Was + Wann + Wo + Tickets | `Almabtrieb Mayrhofen im September 2026: Traditioneller Almabtrieb mit Fest. Jetzt Termin merken!` |
| **Magazin (Detail)** | Teaser + Leser-Nutzen | `Die 10 schönsten Wanderwege im Zillertal: Von leicht bis anspruchsvoll. Inkl. Karte & Einkehrtipps.` |

---

## 5. H1–H2–H3 Hierarchie

### Grundregeln

- **H1:** Einzige H1 pro Seite – enthält das primäre Keyword (muss nicht identisch mit Title sein).
- **H2:** Gliederung der Hauptabschnitte – sekundäre Keywords.
- **H3:** Unterpunkte eines H2-Abschnitts – Longtail/Detail-Keywords.
- **Keine H4–H6 für SEO-relevante Struktur** (nur für optische Staffelung innerhalb von H3-Blöcken).

### Schema pro Seitentyp

| Element | Startseite | Listing | Detail | Magazin |
|---------|-----------|---------|--------|---------|
| **H1** | Slogan / USP | Collection-Name | Name des Objekts | Artikel-Titel |
| **H2** | Top-Kategorien, Highlights | Filterhinweise, Subregionen | Beschreibung, Anfahrt, Tipps | Einleitung, Abschnitt 1, Abschnitt 2 |
| **H3** | – | – | Details (Öffnungszeiten, Preise) | Sub-Überschriften im Text |

**Beispiel Detailseite (Region):**
```
H1: Urlaub im Zillertal
H2: Die schönsten Wanderwege im Zillertal
H3: Leichte Familienwanderungen
H3: Alpin-Touren für Geübte
H2: Skigebiete im Zillertal
H2: Anreise & Unterkünfte
```

---

## 6. Interne Verlinkungsstrategie

### 6.1 Breadcrumbs

`Startseite > Regionen > Zillertal > Mayrhofen`

- **Schema:** `BreadcrumbList` (JSON-LD)
- **Trennzeichen:** `>` (keine Icons für Screenreader)
- **Auf jeder Collection/Detailseite** (außer Startseite)

### 6.2 Tags / Schlagwörter

- Jeder Detail-Eintrag bekommt thematische Tags aus dem Cluster-Set.
- Tag-Seite: `/themen/{tag-slug}/` – aggregiert alle Collections zu einem Thema.
- Tag-Seiten erhalten **`noindex`**, wenn Inhalt dünn; ggf. kanonisch auf Listing-Seite.

### 6.3 Related Content

- **Region ↔ Orte:** Jede Region zeigt ihre Orte.
- **Ort ↔ Unterkünfte/Gastro/Sehenswürdigkeiten:** Cross-Links zwischen den Collections.
- **Erlebnis ↔ Region/Ort:** Jedes Erlebnis verlinkt auf die zugehörige Region und den Ort.
- **Magazin:** Jeder Artikel verlinkt auf relevante Einträge (z. B. Wanderartikel → Wanderwege, Hütten).
- **Ankertexte:** Natürlich, keyword-haltig, nie generisch („hier klicken“).

### 6.4 Sitemap-Integration

- Alle öffentlichen Seiten (außer Tags/Facetten) in der XML-Sitemap.
- Priorität: Startseite 1.0, Listing 0.8, Detail 0.6, Magazin 0.5.

---

## 7. JSON-LD Schema-Typen

| Schema-Typ | Verwendung | Erforderliche Felder |
|-----------|-----------|---------------------|
| **SoftwareApp** | (optional, für interaktive Tools/Karten) | `name`, `applicationCategory`, `operatingSystem` |
| **Article** | Magazin-Artikel | `headline`, `author`, `datePublished`, `image`, `publisher` |
| **FAQPage** | FAQ-Seiten (z. B. „Häufige Fragen“ pro Region) | `mainEntity` (Array von `Question`/`AcceptedAnswer`) |
| **LocalBusiness** | Gastronomie & Unterkünfte | `name`, `address` (PostalAddress), `telephone`, `aggregateRating` (optional) |
| **Event** | Events | `name`, `startDate`, `location` (Place/PostalAddress), `offers` (optional) |
| **BreadcrumbList** | Alle Detailseiten | `itemListElement` (Array von `ListItem`) |
| **Product** | (optional) Buchbare Pakete/Erlebnisse | `name`, `description`, `offers` |

**Globales Schema:**
- **Organization** (für Tirol Tourismus): `name`, `logo`, `url`, `sameAs` (Social-Media-Profile)
- **WebSite**: `name`, `url`, `searchAction` (für interne Suche)

---

## 8. Bild-Optimierung

### 8.1 Format

- **Standard:** WebP (browser-kompatibel via `<picture>`-Fallback auf JPEG/PNG)
- **Auflösungen:** 3 Stufen (480w, 900w, 1920w) – `srcset` für responsive Auslieferung
- **Komprimierung:** WebP Q=80 (visuell verlustfrei)

### 8.2 Alt-Texte

- Pflichtfeld auf jedem `<img>`.
- Beschreibt das Bild **inhaltlich** und **im Kontext der Seite**.
- Keyword-Einsatz nur, wenn natürlich passend.
- **Format:** „{Motiv} in {Ort} | {Region} – {kurze Beschreibung}“
- **Beispiel:** „Bergpanorama des Zillertals vom Mayrhofner Penken – Blick auf die Zillertaler Alpen“

### 8.3 Weitere Metadaten

- `title`: kurz (< 80 Zeichen)
- Dateiname: `{ort}-{motiv}-{nummer}.webp` – kleingeschrieben, Bindestriche

---

## 9. Sitemap-Strategie

### 9.1 Aufbau

```
sitemap.xml (Index)
├── sitemap-pages.xml        (statische Seiten: Startseite, Kontakt, Impressum)
├── sitemap-regionen.xml     (alle Region-Details)
├── sitemap-orte.xml         (alle Ort-Details)
├── sitemap-sehenswuerdigkeiten.xml
├── sitemap-gastro.xml
├── sitemap-unterkuenfte.xml
├── sitemap-camping.xml
├── sitemap-erlebnisse.xml
├── sitemap-events.xml
└── sitemap-magazin.xml      (alle Magazin-Artikel)
```

### 9.2 Regeln

- Jede Sub-Sitemap: max. 20.000 URLs (Google-Limit).
- `lastmod`: Bei jeder Inhaltsänderung aktualisiert.
- `changefreq`: Magazin `weekly`, Events `daily` (während Saison), Rest `monthly`.
- `priority`: Startseite 1.0, Listings 0.8, Details 0.6, Magazin 0.5.
- `robots.txt`: Zeigt auf `sitemap.xml`.

### 9.3 Ausschluss

- Tag-/Themenseiten mit dünnem Inhalt → `noindex`.
- Facetten-/Filter-URLs (`?page=`, `?sort=`) → `noindex`.
- Interne Such-Ergebnisse → `noindex`.
- Technische Pfade (`/admin/`, `/api/`) → per robots.txt blockiert.

---

## 10. Qualitätssicherung & Monitoring

- **Crawl-Test:** `site:tiroltourismus.at` nach Start wöchentlich prüfen.
- **Duplicate-Content-Check:** Sobald ≥ 5 Detailseiten pro Collection vorhanden.
- **Mobile-First:** Alle Strukturen zuerst für mobile Viewports optimieren.
- **Core Web Vitals:** LCP < 2,5 s, FID < 100 ms, CLS < 0,1.
- **Monitoring-Tools:** Google Search Console (GSC) + Bing Webmaster Tools + Crawlstat.

---

*Ende der SEO-Richtlinie. Bei Änderungen an der Architektur oder neuen Collections bitte dieses Dokument aktualisieren.*
