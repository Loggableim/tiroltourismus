# Tirol Tourismus Portal

Statische Astro 5-Webseite für Tirol Tourismus — JSON-getrieben, statisch
generiert und über **Cloudflare Pages** deployed.

## Entwicklung

```bash
# Dependencies installieren
npm ci

# Lokaler Dev-Server (http://127.0.0.1:4321)
npm run dev

# Produktions-Build (Suchindex + Astro)
npm run build

# Vorschau des Builds
npm run preview
```

## Build

`npm run build` führt aus:

1. `npm run build:search-index` — erzeugt den Suchindex aus `src/data/`
2. `npm run build:astro` — generiert das statische HTML/CSS/JS nach `dist/`

## Deployment

Das Deployment läuft über **Cloudflare Pages**. Bei jedem Push auf `master`
baut `.github/workflows/deploy.yml` die Seite pro Sprache und lädt sie in das
jeweilige Cloudflare-Projekt hoch. Konfiguration und Projektnamen stehen in
`deploy.yml`, die Build-Ausgabe in `wrangler.toml` — beide werden von der
Deployment-Pipeline gepflegt und nicht manuell geändert.

## Inhalt & Sprachen

Die Inhalte liegen als JSON in `src/data/` und müssen in allen 8 Sprachen
(`de`, `en`, `it`, `fr`, `nl`, `es`, `cs`, `zh`) gepflegt werden. Agent-Regeln,
Gates und der Hand-off-Ablauf stehen in [`AGENTS.md`](./AGENTS.md).

## Backup

Lokales Backup der Inhalte:

```bash
bash scripts/backup-now.sh
```

Erzeugt ein timestamped ZIP der JSON-Daten in `backups/`.
