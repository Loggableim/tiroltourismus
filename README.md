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

## Domain & Custom Domain (tiroltourismus.com)

### Aktueller Status (18.05.2026)

| Aspekt | Status | Details |
|--------|--------|---------|
| **CNAME-Dateien** | ✅ Aktiv | `/CNAME` und `/public/CNAME` → `tiroltourismus.com` |
| **Astro-Konfig** | ✅ Aktiv | `site: 'https://tiroltourismus.com'` in `astro.config.mjs` |
| **DNS-Apex (A-Records)** | ✅ Aktiv | A-Records zeigen auf GitHub Pages IPs (185.199.108.153, .109, .110, .111) |
| **DNS-IPv6 (AAAA)** | ✅ Aktiv | IPv6-Records zeigen auf GitHub Pages IPv6-Adressen |
| **GitHub Pages Source** | ✅ Aktiv | `build_type: workflow` — Deployment via GitHub Actions |
| **Workflow-Deploy** | ✅ Erfolgreich | Letzter Deploy: f98bcb6, Site auf HTTP live |
| **HTTPS/SSL** | ⏳ Ausstehend | GitHub stellt Let's Encrypt-Zertifikat bereit (asynchron, typisch Minuten–Stunden) |
| **HTTPS-Enforcement** | ⏳ Ausstehend | Kann aktiviert werden, sobald das Zertifikat provisioniert ist |

### Konfiguration

#### CNAME-Datei (bereits eingerichtet)

Zwei CNAME-Dateien zeigen auf den Apex:

- **`/CNAME`** — root level, von Astro ignoriert, dient als Fallback
- **`/public/CNAME`** — wird von Astro in `dist/` kopiert und von GitHub Pages ausgewertet

Beide enthalten: `tiroltourismus.com`

#### DNS-Einträge (beim Domain-Provider)

Domain-Registrar: **Porkbun**, DNS via Cloudflare (Nameserver: `curitiba.ns.porkbun.com`).

Bereits gesetzte Einträge:

| Typ | Name | Wert |
|-----|------|------|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| AAAA | `@` | `2606:50c0:8000::153` |
| AAAA | `@` | `2606:50c0:8001::153` |
| AAAA | `@` | `2606:50c0:8002::153` |
| AAAA | `@` | `2606:50c0:8003::153` |

Entscheidung: **Apex-Domain** (`tiroltourismus.com` ohne `www.`). Der Apex ist für GitHub Pages mit den o.g. A-Records voll unterstützt. Ein `www.`-Subdomain-Weiterleitung kann später via CNAME `www → loggableim.github.io` ergänzt werden, ist aber nicht erforderlich.

#### GitHub Pages Settings (API)

- **Build-Quelle**: GitHub Actions (`build_type: workflow`) ✅
- **Custom Domain**: `tiroltourismus.com` ✅
- **SSL**: automatische Zertifikatsausstellung durch GitHub pending ⏳

### HTTPS/SSL — noch ausstehend

GitHub Pages stellt automatisch ein **Let's Encrypt-Zertifikat** für die Custom Domain aus, sobald:
1. Die CNAME-Datei im Repository liegt ✅
2. Die DNS-Einträge auf GitHub Pages IPs zeigen ✅
3. GitHub die Domain-Konfiguration verarbeitet hat (async, läuft)

Dieser Prozess kann **einige Minuten bis zu einer Stunde** dauern. Danach kann HTTPS Enforcement aktiviert werden:

```bash
gh api -X PUT repos/Loggableim/tiroltourismus/pages \
  --input - <<'EOF'
{ "https_enforced": true }
EOF
```

**Status prüfen**:
```bash
gh api repos/Loggableim/tiroltourismus/pages | jq .https_enforced
# true = HTTPS aktiv, false = noch nicht bereit
```

**Site aufrufen**:
- `http://tiroltourismus.com/` ✅ — läuft bereits
- `https://tiroltourismus.com/` ⏳ — sobald Zertifikat da

### Beschleunigung der Zertifikatsausstellung (falls nötig)

Sollte das Zertifikat nach mehreren Stunden nicht automatisch ausgestellt werden, kann ein DNS-TXT-Eintrag nachgeholfen werden:

```
github-pages-challenge-Loggableim.tiroltourismus.com → (wird von GitHub angezeigt)
```

Diesen TXT-Eintrag im DNS-Provider setzen, dann unter GitHub → Settings → Pages → Custom Domain → Save erneut speichern, um die Verifikation zu triggern.
