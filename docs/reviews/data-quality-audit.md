# Datenqualitäts-Audit — Baseline

**Datum:** 2026-05-19
**Profil:** content-schema-engineer
**Build-Status:** läuft

## Zusammenfassung

| Collection | Total | Beschreibung | Kurz | Koordinaten | Hero-Bild | Tags | Status-Issues |
|---|---|---|---|---|---|---|---|
| gastro | 3.415 | **0 (0%)** 🔴 | 2.325 (68%) | 3.415 (100%) | 0 (0%) | 3.415 | 3 no_status |
| unterkuenfte | 1.111 | 1.111 (100%) | 0 | 1.079 (97%) | 0 (0%) | 1.111 | 55 draft, 5 no_status |
| orte | 258 | **0 (0%)** 🔴 | 258 (100%) | 256 (99%) | 0 (0%) | 258 | — |
| camping | 236 | 236 (100%) | 0 | 236 (100%) | 0 (0%) | 236 | — |
| sehenswuerdigkeiten | 154 | 51 (33%) 🟡 | 154 (100%) | 154 (100%) | 0 (0%) | 154 | **106 no_status** 🔴 |
| magazin | 43 | 0* | 0 | 43 (100%) | 43 (100%) | 43 | bad_slugs (-- in names) |
| regionen | 13 | 12 (92%) | 13 (100%) | **0 (0%)** 🔴 | 0 (0%) | 13 | — |
| erlebnisse | 6 | 6 (100%) | 0 | 6 (100%) | 0 (0%) | 6 | — |
| events | 4 | 4 (100%) | 4 (100%) | 4 (100%) | 0 (0%) | 4 | — |

*Magazin verwendet `inhalt` statt `beschreibung` — siehe Detailanalyse.

## 🔴 Kritische Lücken (P1)

### 1. Gastro: 0% Lang-Beschreibungen
- 3.415 Einträge haben NUR kurzbeschreibung (max ~80 Zeichen)
- 1.090 Einträge haben GAR KEINE kurzbeschreibung
- Das ist die größte Content-Lücke — SEO-Desaster

### 2. Orte: 0% Lang-Beschreibungen
- 258 Ortsseiten ohne ausführliche Beschreibung
- Nur kurzbeschreibung vorhanden

### 3. Bilder fehlen flächendeckend
- Nur Magazin (43/43) hat hero_bild
- Alle anderen Collections: 0%

### 4. Sehenswürdigkeiten: 106 ohne Status
- 106/154 Einträge haben keinen Status (weder published noch draft)
- Nur 51/154 haben Lang-Beschreibung
- Unklar ob diese Einträge im Build erscheinen

## 🟡 Moderate Lücken (P2)

### 5. Regionen: keine Koordinaten
- Alle 13 Regionen ohne lat/lng
- Benötigt für Karten-Darstellung

### 6. Unterkünfte: 55 draft + 5 no_status
- 60/1.111 Einträge nicht published
- 32 fehlende Koordinaten

## Nächste Schritte
1. B1: Enrichment-Pipeline sicher machen
2. B2: Gastro 25er Sample
3. B4: Sehenswürdigkeiten Status + Beschreibungen
4. E1: Bildstrategie definieren
