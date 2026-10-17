# tiroltourismus — Apex Sprachauswahl-Startseite

Statische Astro-5-Startseite für die Sprachauswahl in 8 Sprachen (`de`, `en`, `fr`, `cs`, `nl`, `it`, `es`, `cn`).

## Demo-Pfade (noindex, sofern nicht Produktion)

| Version | Beschreibung | Route | Offline |
|--------|--------------|-------|---------|
| **v2 — Berglicht & Firn** | Instrument Serif, Lichtkegel, Grat-SVG | [`/demofrontpage-v2`](https://tiroltourismus.com/demofrontpage-v2) | `frontpage-demo-v2.html` + `station-flap-board.js` (Doppelklick) |
| **v3 — Apex Hub** | Bebas/Montserrat, Kompakt-Kacheln (Live-Hub) | [`/`](https://tiroltourismus.com/) (index) | — |
| ~~v1~~ | Abgelöst | `/demofrontpage` → Redirect v2 | entfernt |

Styles: v2 → `apex-berglicht.css`; v3 → Inline in `index.astro`.

## Bahnhofs-Anzeige (Split-Flap)

Tagline **v2 + v3** nutzen eine **feste Zellenanzahl** (2×52 bzw. 2×48 Zeichen) wie eine Abfahrtstafel:

- Ruhezustand und nach der Animation: gleiche Kacheln mit Hintergrund/Rahmen (`.tt-ch` / `.df-ch`)
- Kürzerer Text → **leere Felder** (`.tt-ch-empty` / `.df-ch-empty`) bleiben sichtbar
- Logik: `src/lib/station-flap-board.js` (wird in v2 eingebunden; v3 auf `/` ebenfalls)

## v2 — Berglicht & Firn

- Typografie: Instrument Serif, Space Grotesk 600, Inter
- Berglicht, Lichtkegel, Grat-Silhouette, 700 ms Flap
- `demofrontpage-v2.astro` + `apex-berglicht.css`

## v3 — Apex Hub (Produktion)

- Hero-Foto-Rotation (Commons), kompakte Sprachkacheln
- `index.astro` — indexierbar, Sitemap

## Sprache & Footer

- Browser-Sprache → Kachel + Tagline; Fallback EN (v2) / DE-Basis beim Verlassen (v3)
- Impressum/Datenschutz pro Subdomain

## Performance

- Kein Client-Framework; feste Board-Höhe → CLS ≈ 0

## Assets

- Hero v2: `/hero-tirol.*`, `/images/hero-tirol-*`
- Fonts v2: `/fonts/instrument-serif-400.woff2`, `space-grotesk-600`, `inter-400/500`
