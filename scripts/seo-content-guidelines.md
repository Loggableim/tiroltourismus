# SEO & Content Guidelines — Tirol Tourismus

## 1. Content-Architektur

### URL-Struktur
- `/magazin/{slug}/` – Blog-Artikel
- `/magazin/tag/{tag}/` – Tag-Übersicht (automatisch generiert)
- `/magazin/tags/` – Tag-Cloud
- `/orte/{slug}/` – Orte
- `/sehenswuerdigkeiten/{slug}/` – Sehenswürdigkeiten
- `/gastro/{slug}/` – Gastro
- `/unterkuenfte/{slug}/` – Unterkünfte
- `/camping/{slug}/` – Camping
- `/erlebnisse/{slug}/` – Erlebnisse
- `/events/{slug}/` – Events
- `/regionen/{slug}/` – Regionen

### Interne Verlinkung (Anchor-Text-Regeln)
- Jeder Blog-Artikel enthält 3-5 interne Links zu:
  - 1 Ort (`/orte/{slug}/`)
  - 1 Region (`/regionen/{slug}/`)
  - 1-2 passende Erlebnisse/Gastro/Unterkünfte
  - 1 weiteren Blog-Artikel (mit Tag-Overlap)
- Verwende KI-generierte, kontextuelle Anchor-Texte (kein "hier klicken")

### Cross-Linking via Tags
- Jeder Content-Eintrag bekommt 3-5 Tags
- Tags verbinden thematisch verwandte Seiten
- Beispiel: "wandern" taucht in → Blog, Erlebnisse, Sehenswürdigkeiten, Orten auf
- Kein Over-Tagging: nur Tags setzen die wirklich passen

## 2. SEO-Felder pro Page-Type

| Page-Type | title (max 60) | description (max 160) | H1 | canonical |
|---|---|---|---|---|
| Blog | "{titel} – Tirol Tourismus" | "{teaser}" (max 155) | titel | auto |
| Ort | "{name} in Tirol – Infos & Tipps" | "{kurzbeschreibung} (max 155)" | {name} | auto |
| Region | "{titel} in Tirol – Urlaub & Aktivitäten" | "{kurzbeschreibung}" | {titel} | auto |
| Gastro | "{name} – Restaurant/Gasthof in {ort}" | "{kurzbeschreibung}" | {name} | auto |
| Unterkunft | "{name} – Übernachten in {ort}" | "{name} / Ort Beschreibung" | {name} | auto |
| Sehenswürdigkeit | "{name} in Tirol – Infos & Anfahrt" | "{kurzbeschreibung}" | {name} | auto |
| FAQ | "Häufige Fragen zu {thema} – Tirol Tourismus" | "Antworten auf die häufigsten..." | "FAQ" | auto |

## 3. Artikel-Typen & Längen

### Standard-Artikel (500-800 Wörter)
- Ziel: Long-Tail-Keywords abdecken
- Struktur: Einleitung (80-100 Wörter) → 3-4 Sub-Überschriften → Fazit/CTA
- 2-3 interne Links
- 1 FLUX-WebP-Bild (hero)
- Tags: 3-5 relevante

### In-Depth-Artikel (2500-3500 Wörter)
- Ziel: Pillar-Content, Authority
- Struktur: Einleitung → 6-8 Sub-Überschriften (H2+H3) → Tabellen/Listen → FAQ-Abschnitt → Fazit
- 5-8 interne Links
- 3-5 FLUX-WebP-Bilder (Hero + Zwischenbilder)
- Tags: 4-6 relevante
- Meta: Erweiterte Beschreibung, strukturierte Daten wo sinnvoll

### FAQ (50-100 Wörter pro Antwort)
- Frage/Antwort-Paar im JSON
- Max 2 interne Links pro Antwort
- Tags: 2-3 pro Frage

## 4. FLUX-Bild-Guidelines

### Bild-Specs
- Format: WebP (mit Squoosh/imagemin komprimieren)
- Größe: 1200×675px (16:9)
- Max: 150KB
- Prompt-Struktur: "Travel photography, [location/activity], Alps, Austria, (natural lighting:1.2), (cinematic:1.1), high quality, 8k"
- Negative Prompt: "text, watermark, logo, signature, person facing away, blurry, low quality"

### Einbettung
- JSON-Feld: `bilder: [{ url: "/images/magazin/{slug}-1.webp", alt: "..." }]`
- hero_bild: `/images/magazin/{slug}-hero.webp`
- Im Text: via Markdown `![alt](/images/magazin/{slug}-1.webp)`

## 5. Keyword-Pläne pro Kategorie

### Ziel-Keywords (nach Relevanz)

| Category | Primary KW | Secondary KW | Long-Tail |
|---|---|---|---|
| Familie & Aktivurlaub | familienurlaub tirol | kinderhotel tirol, familienprogramm | "mit kindern in tirol" |
| Wandern & Bergsport | wandern tirol | beste wanderwege, bergtouren | "leichte wanderung tirol" |
| Ski & Winterurlaub | skifahren tirol | skigebiete, pistenguide | "skiurlaub mit kindern" |
| Kulinarik & Genuss | tiroler küche | wirtshaus, kulinarik | "tiroler spezialitäten" |
| Kultur & Events | sehenswürdigkeiten tirol | kultur, events | "innsbruck sehenswürdigkeiten" |
| Wellness & Erholung | wellness tirol | thermen, spa | "wellnesshotel tirol" |
| Reiseberichte | tirol reiseführer | tipps, itinerar | "5 tage tirol reise" |
| Hintergrund | geschichte tirol | tradition, brauchtum | "tiroler geschichte" |

## 6. Querverlinkungs-Matrix

Jeder Blog-Artikel MUSS mindestens 2 der folgenden Link-Typen enthalten:

```
→ /orte/{slug}/           (konkreter Ort)
→ /regionen/{slug}/       (übergeordnete Region)
→ /gastro/{slug}/         (Lokal in der Nähe)
→ /erlebnisse/{slug}/     (passendes Erlebnis)
→ /unterkuenfte/{slug}/   (Unterkunft in der Nähe)
→ /sehenswuerdigkeiten/{slug}/ (Attraktion)
→ /magazin/{slug}/        (anderer Artikel mit Tag-Overlap)
```

## 7. Qualitäts-Checkliste vor Abnahme
- [ ] Mindest-Wortanzahl eingehalten
- [ ] Primäres Keyword in H1, erster Absatz, 1x H2
- [ ] 3-5 interne Links gesetzt (verschiedene Domains)
- [ ] 1+ Bild(er) mit alt-Text
- [ ] Meta-Description (max 155 Zeichen)
- [ ] Tags gesetzt (3-5)
- [ ] Kein Platzhalter/Demo-Text
- [ ] Rechtschreibung geprüft (Deutsch)
- [ ] Build erfolgreich
