# tiroltourismus — Apex Sprachauswahl-Startseite

Statische Astro-5-Startseite für die Sprachauswahl in 8 Sprachen (`de`, `en`, `fr`, `cs`, `nl`, `it`, `es`, `cn`).

## Demo-Pfade (noindex)

| Version | Worker-Route | Stylesheet | Offline-Single-File |
|--------|--------------|------------|---------------------|
| **v1 — Alpin-Monolith** | [`/demofrontpage`](https://tiroltourismus.com/demofrontpage) | `landing/src/styles/apex.css` | `landing/frontpage-demo.html` → [`/frontpage-demo.html`](https://tiroltourismus.com/frontpage-demo.html) |
| **v2 — Berglicht & Firn** | [`/demofrontpage-v2`](https://tiroltourismus.com/demofrontpage-v2) | `landing/src/styles/apex-berglicht.css` | `landing/frontpage-demo-v2.html` → [`/frontpage-demo-v2.html`](https://tiroltourismus.com/frontpage-demo-v2.html) |

Alle Demo-Routen: `robots: noindex, nofollow`. Die **Live-Startseite** [`index.astro`](src/pages/index.astro) bleibt unverändert, bis eine Variante abgenommen ist.

## v1 — Alpin-Monolith (Referenz)

- Selbst gehostete WOFF2: **Space Grotesk** 700 (Display), **Plus Jakarta Sans** 400/600 (UI/Tagline)
- Markenführung **tiroltourismus** (klein); Hero-Headline **TIROL.** mit goldenem Punkt
- Mineralische Sprach-Akzente, Tageszeit-Lichtgrading (`data-light`), Split-Flap-Tagline (~680 ms)
- Implementierung: `demofrontpage.astro` + `apex.css`

## v2 — Berglicht & Firn (+ Einflüsse Alpin-Monolith)

- **Typografie:** **Instrument Serif** (Claim `TIROL.`), **Space Grotesk** 600 (Kacheln, Wortmarke), **Inter** 400/500 (Tagline, Footer)
- **Berglicht:** Tageszeit-Scrim (`dawn` / `day` / `dusk` / `night`) + interaktiver Lichtkegel (`.tt-light-cone`, `color-mix` + `--spot-x` pro Sprache)
- **Grat-Silhouette:** `.tt-ridge-bar` / `.tt-ridge-peak` (8 Gipfel-Punkte synchron zur Hover-Sprache)
- **Split-Flap:** 700 ms, Halbkarten-Hinge (`.tt-flap .tt-ch::after`)
- **Hero:** `<picture>` mit `/images/hero-tirol-*` und Root-Fallbacks `/hero-tirol.avif`, `/hero-tirol.webp`, `/hero-tirol.jpg`
- Implementierung: `demofrontpage-v2.astro` + `apex-berglicht.css`

## Sprache & Footer (beide Demos)

- `navigator.languages` → Hervorhebung der passenden Kachel, Tagline in dieser Sprache; sonst **Englisch**
- Impressum/Datenschutz-Links wechseln mit Sprache (Subdomain + lokalisierte Labels)

## Performance

- Zero client dependencies; Inline-JS &lt; 4 KB
- Feste `min-height` auf `.tt-flap-wrap` → **CLS ≈ 0**

## Assets

- **Hero:** `public/hero-tirol.jpg`, `hero-tirol.avif`, `hero-tirol.webp`; optional responsive Derivate unter `public/images/hero-tirol-{640,1280,1920}.{avif,webp}`
- **Fonts v1:** `public/fonts/` (Plus Jakarta Sans, Space Grotesk — siehe `LICENSE-*.txt`)
- **Fonts v2:** zusätzlich `instrument-serif-400.woff2`, `space-grotesk-600.woff2`, `inter-400.woff2`, `inter-500.woff2`

## Bekannte Grenzen

- Fehlen die `/images/hero-tirol-*`-Derivate, greifen die Root-Fallbacks in `srcset`.
- Chinesisch nutzt System-CJK-Stack in Kacheln/Tagline (Font-Budget).
- Demo-Routen sind **nicht** in der produktiven Sitemap.
