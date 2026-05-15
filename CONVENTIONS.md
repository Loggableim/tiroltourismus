# tiroltourismus.com – Projekt-Conventions

## Hosting
- Hosting: **GitHub Pages** (Free Account, Custom Domain via CNAME)
- Kein Backend, keine Datenbank – rein statisch
- Deploy via `git push main` → GitHub Actions → Live

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
- `web/` = Root für GitHub Pages
- Statisches HTML (kein Build-Tool nötig in Phase 1)
- CSS/JS inline oder in `web/assets/`
- SEO: Meta-Tags, Alt-Texte an Bildern, strukturierte Daten (JSON-LD)

## Git
- Hauptbranch: `main` (wird deployed)
- Feature-Branches für größere Änderungen
- Commit-Nachrichten: `[tirol] kurz beschreibung`
- Keine Binärdateien außer optimierte WebP-Bilder

## Hermes-Automation (später)
- Cron-Jobs erzeugen Content lokal → Commit + Push → automatisches Deploy
- Bilder-Management via Script (Upload → Optimierung → Lizenzvermerk)
