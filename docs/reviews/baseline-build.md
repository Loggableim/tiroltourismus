# Baseline Build Report

**Datum:** 2026-05-19 02:27
**Profil:** qa-release-agent

## Build-Ergebnis: ✅ PASS

| Metrik | Wert |
|---|---|
| Seiten | 5.393 |
| Build-Zeit | 67.04s |
| Kompilierung | 58.63s |
| Sitemap | ✅ `sitemap-index.xml` generiert |
| Exit-Code | 0 |
| Warnings | 0 |

## Git-Status

- **Branch:** master
- **Letzter Commit:** `e65ed8e3 [images] FLUX.1-schnell Hero-WebP für alle 43 Magazin-Artikel`
- **Dirty Files:** 2 (src/pages/admin/pending/index.astro, src/pages/events/index.astro)
- **Untracked:** scripts/translate*.py/sh, AdminEventDashboard, EventCard, EventSubmissionForm, src/data/fr/
- **Backup-Branch:** `backup/pre-production-upgrade-20260519-0226` ✅
- **Backup-Patch:** `_backup_pre_upgrade_dirty.patch` (207 Zeilen) ✅
- **Secrets im Diff:** KEINE ✅

## node_modules
- Vorhanden ✅
- Dependencies installiert ✅

## Datenqualität (Details: docs/reviews/data-quality-audit.md)

| Metrik | Wert |
|---|---|
| Gastro ohne Lang-Beschreibung | 3.415 (100%) 🔴 |
| Orte ohne Lang-Beschreibung | 258 (100%) 🔴 |
| Sehenswürdigkeiten ohne Status | 106/154 🔴 |
| Bilder (hero_bild) außer Magazin | 0% 🔴 |
| Build | ✅ Grün |

## Fazit
Build ist stabil, Git ist gesichert, keine Secrets. Die größten Baustellen sind Content-Lücken (Gastro, Orte) und Bilder.
