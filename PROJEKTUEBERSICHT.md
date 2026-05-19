# Tirol Tourismus — Vollständige Projektübersicht

> Stand: 19.05.2026 | Für ein LLM, das die Website verstehen und weiterentwickeln soll.

---

## 1. PROJEKT-STECKBRIEF

| Aspekt | Wert |
|--------|------|
| **Website** | [tiroltourismus.com](https://tiroltourismus.com) |
| **Framework** | Astro 5 (SSG — Static Site Generation) |
| **Hosting** | GitHub Pages (via GitHub Actions) |
| **Domain** | Apex-Domain `tiroltourismus.com`, DNS via Porkbun/Cloudflare |
| **SSL** | GitHub Pages Let's Encrypt (war beim letzten Stand noch ausstehend) |
| **Build-Output** | ~5.377 HTML-Seiten, ~252 MB in `dist/` |
| **Sprachen** | DE (Hauptsprache), EN (teilweise), FR (gerade im Aufbau) |
| **CSS/JS** | Single `tirol.css` (47KB) + `tirol.js` (22KB), inline Stylesheets |
| **Dependencies** | `astro`, `@astrojs/react`, `@astrojs/sitemap`, `leaflet`, `react`, `marked` |
| **Repo** | GitHub `Loggableim/tiroltourismus`, Branch `master` → Deploy |

---

## 2. ARCHITEKTUR

### 2.1 Build-Pipeline

```
src/data/*.json + src/data/{collection}/{slug}/index.json
    ↓
Astro getStaticPaths() generiert alle Seiten
    ↓
astro build → dist/
    ↓
GitHub Actions → Deploy zu GitHub Pages
```

### 2.2 Routing-Struktur

```
/                                    → DE-Homepage (index.astro)
/[locale]/                           → EN-Homepage (locale-Router)
/[locale]/regionen/[slug]            → EN-Regionen-Detailseiten
/{collection}/                       → Collection-Übersichten
/{collection}/[slug]                 → Detailseiten

Collection-Typen mit Detailseiten:
  regionen, orte, unterkuenfte, camping, gastro,
  sehenswuerdigkeiten, erlebnisse, events, magazin

Spezialseiten:
  /admin/events/                      → Admin Event-Dashboard (React)
  /admin/pending/                     → Admin Pending-Betriebe (React)
  /fuer-betriebe/registrierung/       → Betriebs-Registrierung (React)
  /merkliste/                         → Merkliste (React)
  /suche/                             → Suche (statisch)
  /preise/                            → Pricing-Seite (LemonSqueezy)
  /magazin/tag/[tag]                  → Tag-Übersicht (automatisch)
  /magazin/tags/                      → Tag-Cloud
  /faq/                               → FAQ-Seite
```

### 2.3 Datenfluss (JSON-driven)

Jeder Content-Eintrag ist ein Ordner mit `index.json` unter `src/data/{collection}/{slug}/`. Keine Datenbank, kein CMS (außer Betriebs-Registrierung via localStorage).

```
src/data/
├── regionen/          → 13 Einträge
├── orte/              → 258 Einträge
├── unterkuenfte/      → 1.111 Einträge (Hotel, Ferienwohnung, Gasthof, Ferienhaus, Jugendherberge + Camping)
├── camping/           → 236 Einträge
├── gastro/            → 3.415 Einträge (Restaurant, Cafe, Bar, Imbiss, Pub, Eiscafe…)
├── sehenswuerdigkeiten/ → 154 Einträge
├── erlebnisse/        → 6 Einträge (sehr wenig)
├── events/            → 4 Einträge (sehr wenig)
├── magazin/           → 43 Blog-Artikel
├── bezirke.json       → 9 Bezirke (Singleton)
├── einstellungen.json → Site-Konfiguration
├── faq.json           → FAQ-Fragen (Singleton)
├── home.json          → Homepage-Data (Singleton)
├── homepage.json      → Homepage-Content (Singleton)
├── keyword-plan.json  → SEO-Keyword-Plan (43 Artikel analysiert)
└── pending/           → Von Admin freigegebene Betriebe (Work-in-Progress)
```

---

## 3. DATA-SCHEMAS

### 3.1 Regionen (13)
```json
{ "titel": "Ötztal", "emoji": "🏔️", "farbe": "#0051BA",
  "kurzbeschreibung": "...", "beschreibung": "<p>HTML...</p>",
  "bilder": ["/images/..."], "hero_bild": "/images/...",
  "tags": ["wandern","ski"], "grenzen": [[lat,lng],...],
  "hoehe": "3.774 m", "flaeche": "530 km²", "bewertung": 4,
  "einwohner": "12.500", "status": "published", "featured": true }
```

### 3.2 Unterkünfte (1.111)
```json
{ "name": "Alpine Panorama Lodge", "typ": "hotel",
  "tier": "basic", "sterne": 5, "preis_ab": 189,
  "ort": "Innsbruck", "region": "innsbruck", "plz": "6020",
  "adresse": "...", "telefon": "...", "email": "...", "webseite": "...",
  "beschreibung": "<p>...", "ausstattung": ["wifi","sauna"],
  "koordinaten": {"lat": 47.26, "lng": 11.39},
  "tags": ["luxus","wellness"], "status": "published",
  "bilder": ["/images/..."], "hero_bild": "/images/..." }
```

### 3.3 Gastro (3.415)
```json
{ "name": "Gasthof Goldenes Dachl", "kategorie": "restaurant",
  "kurzbeschreibung": "...", "beschreibung": "<p>...",
  "ort": "Innsbruck", "region": "innsbruck",
  "koordinaten": {"lat": 47.26, "lng": 11.39},
  "plz": "6020", "adresse": "...", "telefon": "...",
  "emoji": "🍽️", "farbe": "#E85D3A", "tags": ["traditionell","tiroler"],
  "status": "published" }
```

### 3.4 Magazin (43 Artikel)
```json
{ "titel": "Wandern in Tirol", "slug": "wandern-in-tirol",
  "kategorie": "wandern_bergsport", "autor": "Tirol Tourismus",
  "teaser": "Kurzer Teasertext...", "inhalt": "<p>Voller HTML-Content...</p>",
  "tags": ["wandern","wanderweg"], "status": "published",
  "datum": "2026-05-15", "bilder": ["/images/..."], "hero_bild": "/images/..." }
```

### 3.5 Content-Schema-Datei
`src/lib/content-schema.js` definiert alle Collections inkl. Feld-Typen, Pflichtfelder und `related`-Beziehungen.

---

## 4. KOMPONENTEN & SECTIONS

### 4.1 Core Components (`src/components/`)

| Component | Typ | Zweck |
|-----------|-----|-------|
| `BaseLayout.astro` | Layout | Hauptlayout mit Nav, Footer, SEO-Head, Theme, Language-Switcher |
| `Hero.astro` | Sektion | Homepage-Hero mit CTA |
| `SectionHeader.astro` | Sektion | Section-Header mit Label + Title |
| `CardGrid.astro` | Grid | Raster für Karten (responsive) |
| `Breadcrumbs.astro` | Nav | Breadcrumb-Navigation |
| `SplashScreen.astro` | UI | Lade-Splashscreen (dunkel, animiert) |

### 4.2 Karten-Komponenten
| Component | Data Source |
|-----------|-------------|
| `RegionCard.astro` | regionen |
| `OrtCard.astro` | orte |
| `AccommodationCard.astro` | unterkuenfte |
| `CampingCard.astro` | camping |
| `GastroCard.astro` | gastro |
| `SightCard.astro` | sehenswuerdigkeiten |
| `ArticleCard.astro` | magazin |
| `EventCard.astro` | events |

### 4.3 Interactive React Components
| Component | Zweck |
|-----------|-------|
| `LeafletMap.jsx` | OSM/Leaflet-Karte mit Polygonen, Markern, Clustering, Filter |
| `NewsletterForm.tsx` | MailerLite-Newsletter-Anmeldung |
| `ContactForm.tsx` | Kontaktformular |
| `BetriebRegistrationForm.tsx` | Betriebs-Selbstregistrierung |
| `EventSubmissionForm.tsx` | Event-Einreichung |
| `AdminEventDashboard.tsx` | Admin: Event-Freigabe |
| `AdminPendingDashboard.tsx` | Admin: Betriebs-Freigabe |
| `MerklistePage.tsx` | Merkliste (localStorage-basiert) |

### 4.4 Detailseiten-Sections (`src/sections/`)
| Section | Zweck |
|---------|-------|
| `DetailPage.astro` | Generische Detailseite (macht 90% der Detailseiten aus) |
| `SectionHero.astro` | Hero-Bereich (Bild + Titel + Metadaten) |
| `SectionDescription.astro` | Beschreibung (mit autoLinkContent) |
| `SectionDetailsGrid.astro` | Detail-Grid (Infos, Kontakt, Preise) |
| `SectionMap.astro` | Karten-Sektion (Leaflet) |
| `SectionRelatedGrid.astro` | Verwandte Einträge (findRelated) |
| `SectionArticleHero.astro` | Magazin-Article-Hero |
| `SectionArticleContent.astro` | Magazin-Article-Content |
| `SectionFactsBar.astro` | Fakten-Bar |
| `SectionPrice.astro` | Preis-Anzeige |
| `SectionTags.astro` | Tags |
| `SectionTipps.astro` | Tipps-Sektion |
| `SectionCTA.astro` | CTA-Sektion |

---

## 5. LIBRARIES (src/lib/)

| Datei | Zweck |
|-------|-------|
| `content.js` | Kern-Read-API für Collections, Entries, Singletons, findRelated, findNearby (Haversine), autoLinkContent |
| `content-schema.js` | Schema-Definitionen aller Collections (Dokumentation) |
| `seo.js` | SEO-Meta-Description-Generator (120-160 Zeichen pro Collection-Typ) |

---

## 6. BUSINESS-MODELL (Free-Mium / LemonSqueezy)

### 6.1 Tier-System
- **Basic (Gratis):** Hero + Kontaktdaten, Rest hinter Paywall
- **Silver (19€/Monat):** Beschreibung, Bilder, Bewertung, Kontakt — freigeschaltet
- **Gold (49€/Monat):** Alles + Hervorhebung/Gold-Styling

### 6.2 Implementierung
- `PaywallOverlay.astro` — Glassmorphism-Overlay für Basic-Tier
- `src/config/pricing.js` — LemonSqueezy Store-ID (379815) + Variant-IDs
- `webhook/server.js` — Optionaler Webhook-Server (Express, Node.js)
- Client-seitig: localStorage > LemonSqueezy-Checkout > Tier freigeschaltet
- **Aktuell:** ALLE 1.111 Unterkünfte sind auf "basic" — Paywall greift überall

### 6.3 Webhook-Server
- Pfad: `webhook/`
- Server: `server.js` (Express, Port variabel)
- Service: `tirol-webhook.service`
- Wird für serverseitige Subscription-Persistenz benötigt (aktuell optional)

---

## 7. ÜBERSETZUNGEN (i18n)

### 7.1 Status
| Sprache | Fortschritt | Details |
|---------|-------------|---------|
| **DE** | 🟢 100% | Hauptsprache, alle Collections vollständig |
| **EN** | 🟡 ~20% | Nur homepage + regionen (Innsbruck, Ötztal) übersetzt |
| **FR** | 🔴 ~1% | 14 Orte übersetzt (gerade im Aufbau via translate_worker.py) |

### 7.2 Übersetzungs-Engine
- `scripts/translate.py` — Python-Engine rotiert über 4 Ollama-Keys
- `scripts/translate_worker.py` — Worker-Version (parallel, 3 Threads)
- Modell: `ministral-3:14b` (>600 Wörter) / `ministral-3:3b` (≤600 Wörter)
- Chinesisch (zh) → `deepseek-v4-flash` via opencode-go

---

## 8. QUALITÄTS-STATUS NACH COLLECTION

| Collection | Items | Beschreibung | Koordinaten | Bilder | Tags | Ort | Region |
|-----------|-------|-------------|-------------|-------|------|-----|--------|
| **regionen** | 13 | 12/13 (92%) | 0 | 0 | 13 | n/a | n/a |
| **unterkuenfte** | 1.111 | 1.111 (100%) | 1.079 (97%) | 0 | 1.111 | 1.067 | 1.052 |
| **camping** | 236 | 236 (100%) | 236 (100%) | 0 | 236 | 173 | 76 |
| **gastro** | 3.415 | **0 (0%)** | 3.415 (100%) | 0 | 3.415 | 1.625 | 3.415 |
| **orte** | 258 | 258 (100%) | 256 (99%) | 0 | 258 | n/a | 258 |
| **sehenswuerdigkeiten** | 154 | 52 (34%) | 154 (100%) | 0 | 154 | 154 | 154 |
| **erlebnisse** | 6 | 6 (100%) | 6 (100%) | 0 | 6 | 6 | 6 |
| **events** | 4 | 4 (100%) | 4 (100%) | 0 | 4 | 4 | 4 |
| **magazin** | 43 | 0 (via teaser/inhalt) | n/a | 43 | 43 | n/a | n/a |

---

## 9. KRITISCHE MÄNGEL & BAUSTELLEN

### 🟥 KRITISCH

#### 9.1 Gastro-Beschreibungen fehlen komplett (0/3.415)
- **Problem:** Alle 3.415 Gastro-Einträge haben KEINE Beschreibung
- **Auswirkung:** SEO beschädigt, Paywall sinnlos, Detailseiten leer
- **Ursache:** Gastro-Daten kamen von OSM-Scraper (nur Koordinaten + Kategorie)
- **Lösung:** Batch-Enrichment via LLM (beschreibung aus Name + Kategorie + Ort generieren)
- **Script-Ansätze vorhanden:** `scripts/batch_extend.py`, `scripts/extend_descriptions.py` (brauchen funktionierenden API-Key)

#### 9.2 Sehenswürdigkeiten — nur 52/154 mit Beschreibung
- **Problem:** Nur 34% haben eine Beschreibung
- **Auswirkung:** 102 Detailseiten sind quasi leer (nur Koordinaten + Kategorie)
- **Lösung:** Gleicher Batch-Enrichment-Prozess wie Gastro

#### 9.3 Alle Unterkünfte auf "basic" — kein Umsatz
- **Problem:** Alle 1.111 Unterkünfte sind Tier "basic"
- **Auswirkung:** Paywall blockiert alles, aber niemand kann auf Silver/Gold upgraden
- **Lösung:** Betriebe müssen Tier-Upgrade buchen können (LemonSqueezy-Checkout) ODER
  einige Highlight-Einträge manuell auf silver/gold setzen für Demo-Zwecke

#### 9.4 API-Key-Problematik
- **Problem:** OpenAI-kompatible API-Calls via urllib.request gehen NICHT direkt vom Terminal (HTTP 403)
- **Workaround:** API-Key funktioniert nur über Hermes' Provider-Routing (Kanban Worker, execute_code sandbox)
- **Lösung:** `.env` hat den Key mit `*** redacted`. Muss aus `auth.json` oder via Process-Env geladen werden
- **Betrifft:** Alle Batch-Scripts (enrich, translate, generate)

### 🟡 MITTEL

#### 9.5 Bilder fehlen flächendeckend
- **Problem:** Keine Collection hat Bilder (außer Magazin mit 43)
- **Auswirkung:** Detailseiten haben keine visuellen Inhalte
- **Lösung:** FLUX-API (Key vorhanden: sk-yhwjsrzaorlcrqjcpgwveuzbugitxpgwehawlmpozeoavtxu) für autom. Bildgenerierung
- **Script-Ansätze:** `scripts/add_image_fields.py` (rudimentär)

#### 9.6 Events & Erlebnisse extrem dünn
- **Events:** Nur 4 Einträge (kein Kalender, keine wiederkehrenden Events)
- **Erlebnisse:** Nur 6 Einträge (viel zu wenig für ein Tourismusportal)
- **Lösung:** Content-Generierung + OSM-Scraper für Events

#### 9.7 Magazin — nur 43 Artikel
- **Problem:** Für 5.400 Seiten Website sind 43 Blog-Artikel extrem wenig
- **SEO-Impact:** Fehlende interne Verlinkung, wenig Authority-Content
- **Lösung:** Content-Plan (keyword-plan.json existiert) abarbeiten — Ziel: 100+ Artikel

#### 9.8 EN-Übersetzung nur ~20%
- **Problem:** Nur homepage + innsbruck + oetztal übersetzt
- **Lösung:** translate.py/translate_worker.py weiter ausführen für regionen, orte, unterkuenfte, magazin

#### 9.9 FR-Übersetzung gerade erst am Anfang
- **Problem:** Erst 14 Orte übersetzt
- **Lösung:** translate_worker.py für FR weiterlaufen lassen

#### 9.10 Unresolved Region-Zuordnungen (75 Einträge)
- **Problem:** Region-Fix-Statistik zeigt 75 unresolved + 39 ohne Koordinaten
- **Lösung:** Manuelle Nacharbeit oder verbesserte Geocoding-Pipeline

### 🟢 KLEIN / NIEDRIG

#### 9.11 SSL-Zertifikat für tiroltourismus.com
- **Status:** War beim letzten Stand noch ausstehend (GitHub Let's Encrypt)
- **Prüfung:** `gh api repos/Loggableim/tiroltourismus/pages | jq .https_enforced`

#### 9.12 Kein dynamisches Such-Feature (außer Pagefind bei Build)
- **Aktuell:** Statische Suche via Pagefind-Index (wird bei Build generiert)
- **Limitierung:** Keine Live-Suche, keine Filter-Kombination

#### 9.13 Betriebe-Registrierung nur localStorage
- **Problem:** Registrierte Betriebe landen nur im localStorage des Users
- **Workflow:** Admin muss JSON manuell exportieren und in `src/data/pending/` ablegen
- **Lösung:** Webhook/Server-Komponente für serverseitige Persistenz

#### 9.14 Region-Grenzen (Polygone) nur teilweise vorhanden
- **Regionen mit Polygonen:** Innsbruck, Ötztal (via grenzen-Feld)
- **Ohne Polygone:** Die meisten anderen Regionen
- **Script:** `scripts/generate-boundaries.py` (existiert, getestet)

#### 9.15 Cross-Linking-Script (crosslink_v5.py) existiert, wurde noch nicht vollständig ausgeführt
- **Zweck:** Automatische Verlinkung von Blog → Orte/Gastro/Unterkünfte
- **Status:** v5 ist final, muss auf alle 43 Artikel angewendet werden
- **Alternative:** autoLinkContent in `content.js` macht das zur Build-Zeit

---

## 10. SCRIPTS & AUTOMATION

### 10.1 Content-Generierung
| Script | Zweck | Status |
|--------|-------|--------|
| `scripts/osm_scraper.py` | OSM-Overpass-API-Scraper für Gastro/POIs | ✅ Funktioniert |
| `scripts/osm_gastro_scraper.py` | Gastro-spezifischer OSM-Scraper (v2) | ✅ Funktioniert |
| `scripts/batch_extend.py` | Beschreibungen via LLM generieren (Gastro) | ⚠️ API-Key-Problem |
| `scripts/extend_descriptions.py` | Beschreibungen für Unterkünfte erweitern | ⚠️ API-Key-Problem |
| `scripts/translate.py` | Mehrsprachen-Übersetzung (DE→EN/FR/...) | ✅ Funktioniert (mit Ollama-Keys) |
| `scripts/translate_worker.py` | Parallel-Übersetzung (3 Threads) | ✅ Funktioniert |
| `scripts/crosslink_v5.py` | Cross-Linking Blog→Orte/Gastro/... | ✅ Final, muss ausgeführt |
| `scripts/add_image_fields.py` | Bild-Felder zu JSONs hinzufügen | ⚠️ Basis |
| `scripts/generate-boundaries.py` | Region-Grenzen via OSM/Nominatim | ✅ Funktioniert |
| `scripts/geocode_coordinates.py` | Koordinaten via Nominatim | ✅ Funktioniert |
| `scripts/create-seo-board.py` | Airtable-SEO-Board erstellen | ✅ Funktioniert |
| `scripts/create-tirol-maps-board.py` | Airtable-Maps-Board | ✅ Funktioniert |

### 10.2 Root-Scripts (Deprecated/Temp)
Im Root liegen zahlreiche Batch-Scripts (`b16_*`, `enrich_batch*`, `check_*`, `debug_*`, `test_*`) — viele sind temporär/experimentell und können aufgeräumt werden.

### 10.3 GitHub Actions Workflows
| Workflow | Zweck |
|----------|-------|
| `.github/workflows/deploy.yml` | Build + Deploy zu GitHub Pages bei Push auf master |
| `.github/workflows/backup.yml` | Wöchentliches JSON-Backup (Mo 03:00 UTC) |

### 10.4 Cross-Link Script (crosslink_v5.py)
- **Pfad:** `F:/tiroltourismus/crosslink_v5.py` („P4a – FINAL")
- **Funktion:** Ersetzt Entity-Namen in Blog-Artikeln durch Markdown-Links
- **Qualität:** Blocklist für generische Namen, min 6 Zeichen, max 3 Links/Artikel
- **Tags-Zuordnung:** TAG_MAP-Dictionary für kategorie→tags-Mapping
- **Ausführung:** Python-Script, muss manuell gestartet werden

---

## 11. OFFENE AUFGABEN (PRIORISIERT)

### 🔴 Priorität 1 — Content-Qualität
1. **Gastro-Beschreibungen generieren** (3.415 Items) — LLM-Batch-Enrichment
2. **Sehenswürdigkeiten-Beschreibungen generieren** (102 fehlende)
3. **Bilder für Gastro/Unterkünfte/Orte generieren** — FLUX.1-schnell-API
4. **Einige Unterkünfte auf Silver/Gold setzen** für Paywall-Demo

### 🟡 Priorität 2 — Content-Ausbau
5. **Events aufstocken** (OSM + manuelle Einträge) — Ziel: 50+
6. **Erlebnisse aufstocken** — Ziel: 30+
7. **Magazin-Artikel generieren** — Ziel: 100+ (laut keyword-plan.json)
8. **Crosslink-Script ausführen** (crosslink_v5.py auf alle 43 Artikel)
9. **EN-Übersetzung fertigstellen** (alle Collections)

### 🔵 Priorität 3 — Infrastruktur
10. **FR-Übersetzung fortsetzen** (translate_worker.py)
11. **SSL-Zertifikat prüfen/aktivieren** (tiroltourismus.com)
12. **Region-Polygone für fehlende Regionen generieren**
13. **Unresolved Region-Zuordnungen fixen** (75 Einträge)
14. **Temporäre Root-Scripts aufräumen** (>100 Debug/Test-Scripts)

### 🟣 Priorität 4 — Features
15. **Live-Suche implementieren** (Pagefind reicht vielleicht, aber Filter-Kombination?)
16. **Event-Kalender** (wiederkehrende Events, Monatsansicht)
17. **Betriebe-Backend** (echte Persistenz statt localStorage)
18. **Analytics-Dashboard** (nur in Gold-Tier beworben, nicht implementiert)
19. **Bewertungs-System** (Sterne werden angezeigt, aber nirgends gesammelt)

---

## 12. TECHNISCHE DETAILS FÜR LLM

### 12.1 Wichtige Dateipfade

```
Astro-Config:        F:/tiroltourismus/astro.config.mjs
Package:             F:/tiroltourismus/package.json
TS-Config:           F:/tiroltourismus/tsconfig.json
Main Layout:         src/layouts/BaseLayout.astro
Content API:         src/lib/content.js
Content Schemas:     src/lib/content-schema.js
SEO Generator:       src/lib/seo.js
Pricing Config:      src/config/pricing.js
SEO Guidelines:      scripts/seo-content-guidelines.md
Project Conventions: CONVENTIONS.md (ALT — bezieht sich auf alte HTML-Version!)
README:              README.md
LemonSqueezy:        LEMONSQUEEZY.md
Webhook Server:      webhook/server.js
Translate Engine:    scripts/translate.py
Translate Worker:    scripts/translate_worker.py
Cross-Link Script:   crosslink_v5.py
```

### 12.2 Wie Content geladen wird

```js
// Einträge lesen
readCollection('gastro', 'de')       // Alle Gastro-Einträge (DE)
readEntry('unterkuenfte', 'slug', 'de') // Einzelnen Eintrag
readSingleton('homepage', 'en')      // Singleton (homepage.json, EN)

// Verwandte finden
findRelated('magazin', 'slug', 'de', 4)  // Tag-basiert
findNearby(entry, 'unterkuenfte', 'de', 8) // Distanz-basiert (Haversine)

// Auto-Linking
autoLinkContent(html, currentEntry, 'de', 2) // 2 interne Links

// SEO
generateMetaDescription(entry, 'unterkuenfte', 'de', {typLabel: 'Hotel'})
```

### 12.3 Wichtige Konventionen für neue Einträge

- **Slug:** Lowercase, kebab-case, max 50 Zeichen
- **Status:** `published` (sichtbar), `draft` (unsichtbar), `archived` (ausgeblendet)
- **Tier:** `basic` (default), `silver`, `gold`
- **Bilder:** WebP, 1200×675px (16:9), max 150KB, Pfad: `/images/{collection}/{slug}.webp`
- **Tags:** 3-5 relevante Tags pro Eintrag, kollektionsübergreifend konsistent
- **beschreibung:** HTML, wird mit autoLinkContent angereichert
- **koordinaten:** `{"lat": 47.26, "lng": 11.39}` — Pflicht für Kartenanzeige

### 12.4 Wichtige Config-Felder (einstellungen.json)

```json
{
  "site_name": "tiroltourismus.com",
  "site_description": "Das offizielle Tourismusportal für Tirol – bunt, dunkel, anders.",
  "kontakt_email": "office@tiroltourismus.com",
  "kontakt_telefon": "+43 512 1234567",
  "social": {
    "instagram": "...", "tiktok": "...",
    "facebook": "...", "youtube": "..."
  }
}
```

### 12.5 API-Keys & Credentials
```
FLUX-Key:     sk-yhwjsrzaorlcrqjcpgwveuzbugitxpgwehawlmpozeoavtxu
Ollama Keys:  4 Keys in scripts/translate.py rotierend
Store-ID:     379815 (LemonSqueezy)
Variant-IDs:  silver=1671559, gold=1671576
```

**API-Problem:** OpenAI-kompatible Keys funktionieren nur über Hermes' Provider-Routing, NICHT direkt via urllib.request aus Terminal. Ollama-Keys hingegen funktionieren direkt.

---

## 13. DEPLOYMENT

### 13.1 Automatisch
```bash
git push origin master
# → GitHub Actions buildet + deployt (ca. 1-2 Min)
```

### 13.2 Manuell
```bash
npm run build    # → dist/
npm run preview  # → Lokale Vorschau
```

### 13.3 Lokale Entwicklung
```bash
npm ci
npm run dev      # → http://127.0.0.1:4321
```

---

## 14. NICHT VERGESSEN

- `CONVENTIONS.md` ist **veraltet** — bezieht sich auf alte HTML-Phase ohne Build-Tool
- Root-Verzeichnis enthält viele temporäre Debug/Test-Scripts (sollten aufgeräumt werden)
- Der `webhook/`-Ordner ist ein separates Node.js-Projekt (eigenes package.json)
- Region-Polygone (`entry.grenzen`) sind JSON-Arrays von [lat,lng]-Paaren
- Das `[locale]`-Routing funktioniert über Ordner in `src/pages/[locale]/`
- `dist/` wird bei jedem Build komplett neu generiert
- **WICHTIG:** Beim Arbeiten mit Dateien den Workspace-Pfad `F:/tiroltourismus` als Basis verwenden
