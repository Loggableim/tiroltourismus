# 🏔️ tiroltourismus.com — Brand Guide / CD-Manual

> **Stand:** Mai 2026  
> **Designgewinner:** Gipfellinie (FLUX.2-pro)  
> **Dual-Identity:** AlpenPop (Tag) × ALPENPEAK (Nacht)  
> **Inhaber:** Dominik Rainer, Haller Straße 3, A-6020 Innsbruck

---

## 1. Markenversprechen

**Tirol ANDERS.**  
Zwei Seelen, ein Land. Hell, bunt und frech am Tag. Dunkel, dramatisch und gold in der Nacht.  
Tirol ist die erste alpine Destination mit Dual-Mode-Identity — ein Portal, zwei Erlebnisse.

---

## 2. Logo — Gipfellinie (Primärlogo)

| Eigenschaft | Wert |
|---|---|
| **Typ** | FLUX.2-pro generiertes Bild (PNG, 1280×512) |
| **Motiv** | Abstrakte Bergsilhouette aus fließenden Kurven |
| **Farbverlauf** | Pink #FF1493 → Gold #D4A800 → Blau #0066FF |
| **Einsatz** | Hero-Hintergrund (full-bleed, object-fit:cover) |
| **Datei** | `brand/hero-logos/konzept1_gipfellinie_20260517_083224.png` |

### 2.1 Navigations-Logo (Secondary)

| Eigenschaft | Wert |
|---|---|
| **Typ** | Inline-SVG (handcodiert) |
| **Motiv** | Buchstaben T-I-R-O-L als Berg-Zacken + "tourismus" |
| **Farben** | Rot #C8102E, Pink #FF1493, Gold #D4A800, Blau #0066FF |
| **ViewBox** | `4 4 404 46` |
| **Breite** | 360px (Nav) / 340px (Footer) |
| **Datei** | `brand/logos/tirol-zacken-lockup.svg` |
| **Status** | ✅ Produktiv |

### 2.2 Hero-Logos (6 Konzepte — Auswahl)

| # | Name | Status | Akzentfarbe |
|---|---|---|---|
| 1 | **Gipfellinie** 🏆 | **GEWINNER** — Hero-Background | Pink #FF1493 |
| 2 | Dualmodus | Archiviert | Orange #FF6B35 |
| 3 | Alpiner Kristall | Archiviert | Violett #8B5CF6 |
| 4 | Typografisch | Archiviert | Blau #0066FF |
| 5 | Aurora | Archiviert | Cyan #00E5FF |
| 6 | Linienkunst | Archiviert | Gold #FFD700 |

---

## 3. Farben (Corporate Colors)

### 3.1 Tag-Modus (AlpenPop)

| Rolle | Farbe | Hex | CSS-Variable |
|---|---|---|---|
| **Primärakzent** | Pink | `#FF1493` | `--pink` |
| **Sekundärakzent** | Gold | `#D4A800` | `--gold` |
| **Gold hell** | Gold hell | `#FFD700` | `--gold-light` |
| **Hintergrund** | Hellbeige | `#F5F3F0` | `--bg` |
| **Text** | Fast Schwarz | `#1A1A1A` | `--text` |
| **CTA** | Pink | `#FF1493` | `--pink` (btn-pink) |
| **Blau (Akzent)** | IKEA-Blau | `#0051BA` | `--blue` |

### 3.2 Nacht-Modus (ALPENPEAK)

| Rolle | Farbe | Hex | CSS-Variable |
|---|---|---|---|
| **Hintergrund** | Tiefschwarz | `#0A0A12` | `--bg` |
| **Fläche** | Dunkelviolett | `#10101E` | `--bg2` |
| **Text** | Warmweiß | `#F0EDEE` | `--text` |
| **Glass** | Weiß 6% | `rgba(255,255,255,.06)` | `--glass` |
| **Pink-Glow** | — | `rgba(255,20,147,.18)` | `--pink-glow` |
| **Gold-Glow** | — | `rgba(255,215,0,.15)` | `--gold-glow` |

---

## 4. Typografie

| Element | Font | Größe | Gewicht |
|---|---|---|---|
| **Display (Hero, Titel)** | `Bebas Neue` | 72–180px (clamp) | 700 |
| **Body (Fließtext)** | `Montserrat` | 14–17px | 300–600 |
| **Sektion-Header** | `Bebas Neue` | 36–64px | 400 |
| **Label** | `Montserrat` | 11–13px | 600, uppercase |
| **Buttons** | `Montserrat` | 13–14px | 700, uppercase |

---

## 5. Dual-Mode System

### 5.1 Phasen

| Zeitraum | Modus | Erlebnis |
|---|---|---|
| 6:00–19:59 | **AlpenPop** (Tag) | Hell, klar, frech — hohe Kontraste, warme Töne |
| 20:00–5:59 | **ALPENPEAK** (Nacht) | Dunkel, dramatisch, poppig — Glassmorphism, Neon |

### 5.2 Bedienung

- **Auto-Modus** (Standard): Systemzeit-gesteuert
- **Manuell**: Toggle-Button (Sonne/Mond) in der Navigation
- **Speicherung**: `localStorage.getItem('tirol_theme')`

### 5.3 Umschalt-Mechanismus

```css
[data-theme="alpenpeak"] {
  --bg: #0A0A12;
  --text: #F0EDEE;
  --glass: rgba(255,255,255,.06);
  /* ... */
}
```

Alle Komponenten referenzieren CSS-Variablen — kein Hardcoding. Ein `data-theme`-Attribut auf `<html>` schaltet das gesamte Design.

---

## 6. Layout & Komponenten

### 6.1 Seitenstruktur

```
TOP BAR (Sprachen, Merkliste, Für Betriebe)
├── main-nav (Glassmorph, sticky, 66px → 6px bei Scroll)
├── MOBILE MENU (Overlay bei Hamburger)
├── HERO (Gipfellinie-BG + "TIROL ANDERS")
├── STATS (4 Counter: Gipfel, Unterkünfte, Wander-km, Liftanlagen)
├── 6 SEELEN TIROLS (Logo-Galerie, 6 Cards)
├── WARUM TIROL? (3 Columns)
├── REGIONEN (6 Karten)
├── QUOTE
├── UNTERKÜNFTE (Tabs + Katalog)
├── AKTIVITÄTEN (6 Cards)
├── EVENTS (4 Cards)
├── MAGAZIN (3 Artikel)
├── NEWSLETTER
├── PARTNER
└── FOOTER
```

### 6.2 Nav-Verhalten

- **Initial:** `top: 66px` (unter der Topbar)
- **Bei Scroll:** `top: 6px!important` + stärkerer Glass-Effekt
- **Trigger:** `window.scrollY > 0` (sofort bei Scrollbeginn)
- **Radius:** 100px (Pillenform)

### 6.3 Abstände

- Container max-width: `1200px`
- Section padding: `80px 0`
- Card radius: `12px` (Standard) / `20px` (Large)
- Button radius: `50px` (Pillen)

---

## 7. Dateistruktur (Produktiv)

```
F:\tiroltourismus\
├── index.html              → Splash-Screen (Logo-Übersicht)
├── CONVENTIONS.md           → Projekt-Konventionen
├── auftrag-fuer-llm-mockup.md → Ursprungs-Briefing
├── app/                     → Hauptportal (17 Seiten)
│   ├── index.html           → Startseite (Hero, Stats, 6 Seelen, ...)
│   ├── assets/
│   │   ├── css/tirol.css    → Shared Styles (Design System)
│   │   ├── js/tirol.js      → Shared JS (Theme, Reveal, Nav, ...)
│   │   └── _template.html   → Bauplan für Subpages
│   ├── regionen/ (7 Seiten)
│   ├── unterkuenfte/ (2 Seiten)
│   ├── erlebnisse/ (1 Seite)
│   ├── events/ (2 Seiten)
│   ├── magazin/ (2 Seiten)
│   ├── ueber-uns/ (1 Seite)
│   ├── kontakt/ (1 Seite)
│   ├── impressum/ (1 Seite)
│   ├── datenschutz/ (1 Seite)
│   ├── agb/ (1 Seite)
│   └── fuer-betriebe/ (1 Seite)
├── brand/
│   ├── BRAND-GUIDE.md       → ← DU BIST HIER
│   ├── hero-logos/
│   │   └── konzept1_gipfellinie_...png → GEWINNER
│   ├── logos/
│   │   └── tirol-zacken-lockup.svg     → Nav-Logo
│   └── index.html           → Brand Hub Page
└── _archive/                → Historische Entwürfe
    ├── mockups/             → 8 alte Design-Studien
    ├── hero-logos/          → Konzepte 2–6
    ├── logos/               → Alte SVG/PNG-Entwürfe
    ├── scripts/             → Build-/Fix-Skripte
    └── misc/                → PDF-Viewer, Test-Dateien
```

---

## 8. Hero-Spezifikation

| Eigenschaft | Wert |
|---|---|
| **Background** | `konzept1_gipfellinie` als `object-fit:cover` |
| **Overlay** | Pink→transparent (oben→unten) + seitlicher Gold-Anteil |
| **Glow** | 800px radialer Halo (Pink→Gold→transparent) |
| **Animation** | Langsames Zoomen `scale(1.05→1.15)` über 20s |
| **Heading** | "TIROL" in Weiß, "ANDERS" in Pink→Gold Gradient |
| **Text** | "Zwei Seelen, ein Land..." in Weiß 70% Opazität |
| **CTAs** | "6 Seelen entdecken" (Pink) + "Regionen erkunden" (Glass) |

---

## 9. Responsive Breakpoints

| Gerät | Max-Breite | Anpassungen |
|---|---|---|
| Desktop | >968px | 3er/4er Grids, volles Hero |
| Tablet | 768–968px | 2er Grids, kleinere Fonts |
| Mobil | <768px | 1er Grids, Stacked Nav, Hero-Logo unsichtbar |
| Reduced Motion | prefers-reduced-motion | Animationen deaktiviert |

---

## 10. Technische Entscheidungen

- **Statisches HTML** — Kein Framework, keine Build-Tools
- **GitHub Pages** ready — CNAME, SSL über Cloudflare
- **Passwort-Gate** — Code `2205`, sessionStorage (deaktiviert für Live)
- **Keine API-Keys** im Frontend
- **Kein CDN** außer Google Fonts (Bebas Neue + Montserrat)
- **WebP-Konvention** für echte Bilder (noch nicht deployt)
- **FLUX-Bilder** sind PNG (kein Alpha-Kanal) — Hintergrund-Removal via PIL möglich

---

*Brand Guide v1.0 · Erstellt am 17. Mai 2026 · Dominik Rainer / Tirol Tourismus*
