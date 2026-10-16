# tiroltourismus — Apex Sprachauswahl-Startseite

Statische Astro-5-Startseite für die Sprachauswahl in 8 Sprachen (`de`, `en`, `fr`, `cs`, `nl`, `it`, `es`, `cn`).

## Demo-Pfade (noindex)

| Pfad | Zweck |
|------|--------|
| [`/demofrontpage`](https://tiroltourismus.com/demofrontpage) | Worker-Demo der Apex-Startseite (`robots: noindex, nofollow`) |
| [`/demofrontpage-v2`](https://tiroltourismus.com/demofrontpage-v2) | Reserviert für Design-Iteration v2 (Platzhalter, noindex) |
| `landing/frontpage-demo.html` | Offline-Single-File-Demo (Doppelklick im Browser) |

Die **Live-Startseite** [`index.astro`](src/pages/index.astro) bleibt unverändert, bis die Demo abgenommen ist.

## Design („Alpin-Monolith“)

- Selbst gehostete WOFF2: **Space Grotesk** 700 (Display), **Plus Jakarta Sans** 400/600 (UI/Tagline)
- Markenführung durchgehend **tiroltourismus** (klein); Hero-Headline **TIROL.** mit goldenem Punkt
- Mineralische Sprach-Akzente (kein Neon/Magenta)
- Tageszeit-Lichtgrading (`dawn` / `day` / `dusk` / `night`) über `data-light` am Stage
- Split-Flap-Tagline bei Hover/Fokus (60 fps, `prefers-reduced-motion` → Crossfade)

## Sprache & Footer

- `navigator.languages` → Hervorhebung der passenden Kachel, Tagline in dieser Sprache; sonst **Englisch**
- Impressum/Datenschutz-Links wechseln mit Sprache (Subdomain + lokalisierte Labels)

## Performance

- Zero client dependencies; Inline-JS &lt; 3,5 KB
- Feste `min-height` auf `.tt-flap-wrap` → **CLS ≈ 0**
- Hero: `<picture>` mit AVIF/WebP (`/images/hero-tirol-*` optional) und Fallback **`/hero-tirol.jpg`**

## Assets

- **Hero:** `public/hero-tirol.jpg`, `hero-tirol.avif`, `hero-tirol.webp`; optional responsive Derivate unter `public/images/hero-tirol-{640,1280,1920}.{avif,webp}`
- **Fonts:** `public/fonts/` (OFL, siehe `LICENSE-*.txt`)

## Bekannte Grenzen

- Fehlen die `/images/hero-tirol-*`-Derivate, greifen die Root-Fallbacks in `srcset` (`/hero-tirol.avif`, `/hero-tirol.webp`, `/hero-tirol.jpg`).
- Chinesisch nutzt System-CJK-Stack in Kacheln/Tagline (Font-Budget).
- Demo-Routen sind **nicht** in der produktiven Sitemap; nur über direkte URL testbar.
