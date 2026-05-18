# Tirol Tourismus Portal

Statische Astro 5-Webseite für Tirol Tourismus — JSON-getrieben, statisch generiert und über GitHub Pages deployed.

## Entwicklung

```bash
# Dependencies installieren
npm ci

# Lokaler Dev-Server (http://127.0.0.1:4321)
npm run dev

# Produktions-Build + Pagefind-Index
npm run build

# Vorschau des Builds
npm run preview
```

## Build-Reihenfolge

`npm run build` führt aus:
1. `astro build` — generiert statisches HTML/CSS/JS nach `dist/`
2. `npx pagefind --site dist` — erstellt den Suchindex aus dem Build-Output

## Deployment

Der Deploy erfolgt automatisch über **GitHub Actions** bei jedem Push auf `master`.

## Backup

Wöchentliches Backup aller JSON-Daten in `src/data/` über **GitHub Actions** (`backup.yml`):
- **Zeitplan**: Jeden Montag 03:00 UTC
- **Zielbranch**: `backups` (wird automatisch angelegt)
- **Format**: `backups/tirol-content-<timestamp>.zip`
- **Aufbewahrung**: Die letzten 24 Snapshots, ältere werden automatisch gelöscht
- **Manuell starten**: GitHub → Actions → "Weekly JSON Data Backup" → "Run workflow"
- **Lokales Backup**: `bash scripts/backup-now.sh` (erzeugt zip im `backups/`-Ordner)

### Workflow: `.github/workflows/deploy.yml`

1. **Checkout** — Repository auschecken
2. **Node 20 + npm cache** — Node.js mit Caching für schnelle Wiedereinrichtung
3. **npm ci** — deterministische Dependency-Installation
4. **Build** — `npm run build` (Astro + Pagefind) mit `SKIP_KEYSTATIC=true`
5. **Artifact upload** — `dist/` wird als Pages-Artefakt hochgeladen
6. **Deploy** — `actions/deploy-pages` published auf GitHub Pages

### Umgebungsvariablen

| Variable | Wert | Zweck |
|---|---|---|
| `SKIP_KEYSTATIC` | `true` | Überspringt Keystatic-Integration im CI-Kontext |

### Manuelles Deployment

Zum manuellen Neustarten des Deployments:
1. Auf GitHub ins Repository navigieren
2. **Actions** → **Deploy to GitHub Pages** → **Run workflow**

## Domain

Die Seite ist unter **https://tiroltourismus.com** erreichbar (via CNAME).
