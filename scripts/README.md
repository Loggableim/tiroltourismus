# scripts/ — Hilfs-Skripte

## add_image_fields.py

Initialisiert die Bild-Infrastruktur für alle Collections. Einmalig nach dem Hinzufügen neuer Collections ausführen.

```bash
python scripts/add_image_fields.py
```

**Was passiert:**

1. Fügt `"bilder": []` und `"hero_bild": null` zu allen `index.json`-Einträgen hinzu (falls nicht vorhanden)
2. Erstellt `public/images/{collection}/{slug}/`-Verzeichnisse mit `.gitkeep` und `slug.json`

## Bilder hinzufügen (Workflow)

### 1. Bild-Dateien ablegen

Lege `.webp`-Dateien in das passende Verzeichnis unter `public/images/`:

```
public/images/
  unterkuenfte/
    hotel-modlinger/
      hero.webp        ← Hero-Hintergrundbild
      zimmer.webp      ← weiteres Bild
      aussenansicht.webp
  regionen/
    innsbruck/
      hero.webp
  gastro/
    cafe-central-innsbruck/
      hero.webp
  ...
```

> **Empfehlung:** `.webp`-Format verwenden (klein, modern, von Browsern nativ unterstützt).

### 2. hero_bild setzen

In der `index.json` des Eintrags das `hero_bild` auf den Pfad setzen:

```json
{
  "name": "Hotel Mödlinger",
  "hero_bild": "/images/unterkuenfte/hotel-modlinger/hero.webp",
  "bilder": [
    "/images/unterkuenfte/hotel-modlinger/zimmer.webp",
    "/images/unterkuenfte/hotel-modlinger/aussenansicht.webp"
  ]
}
```

> Der Pfad ist ein URL-Pfad (startet mit `/images/...`), **nicht** ein Dateisystem-Pfad. Astro serviert Dateien aus `public/` automatisch unter diesem Pfad.

### 3. Hero-Bild wird automatisch angezeigt

Wenn `hero_bild` gesetzt ist, zeigt die Detailseite das Bild als Hero-Hintergrund mit einer dunklen Verlaufs-Overlay (für Lesbarkeit) an.

- **`type: 'hero'`** (regionen, unterkuenfte, orte, gastro, events) → Bild über SectionHero-Komponente
- **`type: 'custom-hero'`** (sehenswuerdigkeiten, erlebnisse) → Bild über inline custom-hero

### 4. Effekt prüfen

```bash
npm run dev
# http://127.0.0.1:4321/unterkuenfte/hotel-modlinger/
```

## Verzeichnisstruktur

```
public/images/{collection}/{slug}/
├── .gitkeep          # Leerer Ordner bleibt in git
├── slug.json         # Metadaten (wird vom Script angelegt)
├── hero.webp         # Hero-Hintergrundbild
└── *.webp            # Weitere Bilder
```

## Collections

| Collection | Einträge | Image-Pfad                     |
|------------|----------|--------------------------------|
| regionen   | 13       | /images/regionen/{slug}/       |
| unterkuenfte | 1037  | /images/unterkuenfte/{slug}/   |
| gastro     | 46       | /images/gastro/{slug}/         |
| orte       | 258      | /images/orte/{slug}/           |
| sehenswuerdigkeiten | 40 | /images/sehenswuerdigkeiten/{slug}/ |
| magazin    | 13       | /images/magazin/{slug}/        |
| erlebnisse | 6        | /images/erlebnisse/{slug}/     |
| events     | 4        | /images/events/{slug}/         |

## Schema

Die Felder `bilder` und `hero_bild` sind in `src/lib/content-schema.js` für alle Collections dokumentiert.
