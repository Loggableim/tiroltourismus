# tiroltourismus.com – Projekt-Conventions

Agent-Regeln (Rollen, Hard Rules, Gates, Hand-off) stehen in [`AGENTS.md`](./AGENTS.md).
Diese Datei beschreibt nur den technischen Rahmen des Projekts.

## Hosting & Stack
- Hosting: **Cloudflare Pages**, Multi-Sprachen-Deploy über die Matrix in
  `.github/workflows/deploy.yml` (je Sprache ein Pages-Projekt).
- Build: **Astro 5** (statischer Output), Content JSON-getrieben in `src/data/`.
- Sprachen: `de`, `en`, `it`, `fr`, `nl`, `es`, `cs`, `zh` — Inhalte immer in
  allen 8 Sprachen pflegen.
- Build-Ausgabe: `dist/`, konfiguriert in `wrangler.toml`.
  `wrangler.toml` und `deploy.yml` werden von der Deployment-Pipeline gepflegt
  und nicht manuell geändert.

## Bilder
- **Keine Bilder ohne Rechte** – jeder Upload muss lizenzgeklärt sein
- Quellen: Eigene KI-Generierung, Stock-Plattformen (Adobe Stock/Shutterstock), Presseportale mit schriftlicher Genehmigung
- Jedes Bild im Repo hat einen Lizenzvermerk in `images/LICENSES.md`
- **Optimierungspflicht** vor Commit:
  - Format: **WebP** (mit JPEG-Fallback via `<picture>`)
  - Max-Breite: 1920px (Hero), 800px (Content), 400px (Thumbnails)
  - Qualität: 80% (lossy, visuell verlustfrei)
  - Keine Raw-Fotos > 500 KB im Repo
- Empfohlenes Tool: `cwebp` oder Squoosh (CLI)
  ```bash
  # Beispiel Konvertierung
  cwebp -q 80 -resize 1920 0 input.jpg -o output.webp
  ```

## Code & Struktur
- Astro-Komponenten in `src/`, Inhalte in `src/data/` (JSON pro Sprache)
- SEO: Meta-Tags, Alt-Texte an Bildern, strukturierte Daten (JSON-LD)

## Git
- Hauptbranch: `master` (Deploy-Quelle; nur Vali mergt dorthin)
- Feature-Branches für größere Änderungen, PR-only
- Commit-Nachrichten im Conventional-Commit-Stil, z. B.
  `feat(content): …`, `fix(…)`, `chore(…)`
- Keine Binärdateien außer optimierte WebP-Bilder

## Hermes-Automation (später)
- Cron-Jobs erzeugen Content lokal → Commit + Push → automatisches Deploy
- Bilder-Management via Script (Upload → Optimierung → Lizenzvermerk)
