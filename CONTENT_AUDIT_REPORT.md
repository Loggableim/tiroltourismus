# Content-Audit: tiroltourismus.com – Top 50+ Seiten

**Datum:** 12.06.2026  
**Untersucht:** 60+ Seiten aus 8 Content-Typen  
**Quellen:** Live-Site (tiroltourismus.com), Build-Dist (F:/tiroltourismus/dist/), Source (F:/tiroltourismus/src/)

---

## Executive Summary

**Gesamtbewertung: C (mittel)**  
Die Website hat ein solides technisches Fundament (Astro SSG, i18n, JSON-LD, Pagefind-Suche) und gute Navigation. Die **inhaltliche Qualität ist jedoch stark inhomogen**:

- **Stärken:** Magazin-Artikel (gut recherchiert), FAQ (wertvoll), Sehenswürdigkeiten + Events (strukturiert), technisches SEO (Schema.org, hreflang)
- **Schwächen:** Orte haben **keine Beschreibungstexte** (100% der Top-5), Ötztal-Region hat **keine Langbeschreibung**, Gastro/Unterkünfte fehlen **Bilder, Preise, E-Mail, Adressen** zu 50-100%, **keine OG-Images** auf Detailseiten

---

## Detail-Audit nach Seitentyp

### 1. STARTSEITE (/)
| Kriterium | Wert |
|---|---|
| **Content (6/10)** | Hero-Text generisch ("Erleben Sie Tirol in seiner ganzen Vielfalt"). Homepage-Content aus `homepage.json` ist dünn – kein redaktioneller Text, nur Hero + Stats + Kacheln. |
| **Data (5/10)** | Keine strukturierten Daten außerhalb der verlinkten Collections |
| **Trust (3/10)** | Kein Autor, kein Datum, keine Quellen |
| **SEO (8/10)** | Title, Description, H1 vorhanden. JSON-LD WebSite + Organization. OG-Tags. Canonical. Hreflang. |
| **Klasse: C (55 Punkte)** | **Problem:** Homepage hat kaum redaktionellen Content. Hero-Text ist generisch. Kein "Über Tirol"-Abschnitt. **Fix: Mittel** |

### 2. TOP 5 REGIONEN

#### /regionen/oetztal/
| Kriterium | Wert |
|---|---|
| **Content (3/10)** | ❌ **KEINE Beschreibung**. Nur `kurzbeschreibung` ("Gletscher, Action und uralte Tradition."). Keine `tipps`, `empfehlungen`, `umgebung`. |
| **Data (5/10)** | Koordinaten + Grenzen + Höhe/Fläche/Einwohner + Tags vorhanden. Keine Bilder. |
| **Trust (3/10)** | Keine Quellen, kein Autor, kein Datum |
| **SEO (7/10)** | Titel + Description aus kurzbeschreibung. JSON-LD WebSite. Kein Region-Schema (TouristDestination fehlt) |
| **Klasse: D (45 Punkte)** | **DRINGEND:** Beschreibung, Tipps und Empfehlungen fehlen komplett. **Fix: Hoch** |

#### /regionen/zillertal/
| Kriterium | Wert |
|---|---|
| **Content (8/10)** | ✅ Gute Beschreibung mit Details zu Skigebieten, Sommeraktivitäten. 3 Tipps, Empfehlung, Umgebungsbeschreibung. |
| **Data (6/10)** | Alle Felder gefüllt. Keine Bilder. Tags: 5. |
| **Trust (3/10)** | Keine Quellen, kein Autor, kein Datum |
| **SEO (7/10)** | OK |
| **Klasse: B (60 Punkte)** | **Gut, aber:** Bilder fehlen, kein TouristDestination-Schema. **Fix: Niedrig** |

#### /regionen/stubaital/
| Kriterium | Wert |
|---|---|
| **Content (8/10)** | ✅ Gute Beschreibung, Tipps, Empfehlung, Umgebung. |
| **Data (6/10)** | OK. Keine Bilder. |
| **Trust (3/10)** | Keine Quellen |
| **SEO (7/10)** | OK |
| **Klasse: B (60 Punkte)** | **Gut.** Bilder fehlen. |

#### /regionen/kitzbuehel/
| Kriterium | Wert |
|---|---|
| **Content (8/10)** | ✅ Gute Beschreibung (Hahnenkamm, Altstadt, Aktivitäten). 3 Tipps, Empfehlung, Umgebung. |
| **Data (6/10)** | OK |
| **Trust (3/10)** | Keine Quellen, kein Autor |
| **SEO (7/10)** | OK |
| **Klasse: B (60 Punkte)** | **Gut.** |

#### /regionen/innsbruck/
| Kriterium | Wert |
|---|---|
| **Content (8/10)** | ✅ Gute Beschreibung mit Sehenswürdigkeiten, Nordkettenbahn, Olympia. |
| **Data (6/10)** | OK |
| **Trust (3/10)** | Keine Quellen |
| **SEO (7/10)** | OK |
| **Klasse: B (60 Punkte)** | **Gut.** |

### 3. TOP 5 ORTE

#### /orte/innsbruck/
| Kriterium | Wert |
|---|---|
| **Content (2/10)** | ❌ **KEINE Beschreibung**. Nur `kurzbeschreibung` + Emoji + Höhe + Einwohner + Tags. |
| **Data (4/10)** | Koordinaten, Region, Bezirk, Einwohner. Keine Bilder. |
| **Trust (2/10)** | Keine Quellen |
| **SEO (6/10)** | Titel OK. Description ist Kurzbeschreibung. Kein TouristAttraction-Schema. |
| **Klasse: D (35 Punkte)** | **DRINGEND:** Innsbruck als Landeshauptstadt hat NULL redaktionellen Content. **Fix: Hoch** |

#### /orte/kitzbuehel/
| Kriterium | Wert |
|---|---|
| **Content (2/10)** | ❌ KEINE Beschreibung |
| **Data (4/10)** | Basis-Felder. Keine Bilder. |
| **Trust (2/10)** | Keine Quellen |
| **SEO (6/10)** | Basis OK |
| **Klasse: D (35 Punkte)** | **Fix: Hoch** |

#### /orte/mayrhofen/
| Kriterium | Wert |
|---|---|
| **Content (2/10)** | ❌ KEINE Beschreibung |
| **Data (4/10)** | Basis-Felder. Keine Bilder. |
| **Trust (2/10)** | Keine Quellen |
| **SEO (6/10)** | Basis OK |
| **Klasse: D (35 Punkte)** | **Fix: Hoch** |

#### /orte/soelden/
| Kriterium | Wert |
|---|---|
| **Content (2/10)** | ❌ KEINE Beschreibung |
| **Data (4/10)** | Basis-Felder. Keine Bilder. |
| **Trust (2/10)** | Keine Quellen |
| **SEO (6/10)** | Basis OK |
| **Klasse: D (35 Punkte)** | **Fix: Hoch** |

#### /orte/seefeld/
| Kriterium | Wert |
|---|---|
| **Content (2/10)** | ❌ KEINE Beschreibung |
| **Data (4/10)** | Basis-Felder. Keine Bilder. |
| **Trust (2/10)** | Keine Quellen |
| **SEO (6/10)** | Basis OK |
| **Klasse: D (35 Punkte)** | **Fix: Hoch** |

### 4. TOP 5 UNTERKÜNFTE

#### /unterkuenfte/activehotel-bergkonig/
| Kriterium | Wert |
|---|---|
| **Content (6/10)** | ✅ Beschreibung vorhanden. AI-generiert wirkend, aber informativ. |
| **Data (4/10)** | ❌ Kein Preis (preis_ab=null), ❌ Keine Sterne-Bewertung, ❌ Keine Bilder, ❌ Keine Ausstattung, ❌ Keine E-Mail |
| **Trust (4/10)** | Webseite + Telefon vorhanden. Kein Datum. |
| **SEO (6/10)** | JSON-LD LodgingBusiness. Kein OG-Image. |
| **Klasse: C (50 Punkte)** | **Preise, Sterne, Bilder, Ausstattung fehlen. Fix: Mittel** |

#### /unterkuenfte/almhof-family-resort-spa/
| Kriterium | Wert |
|---|---|
| **Content (6/10)** | ✅ Beschreibung OK |
| **Data (3/10)** | ❌ Sterne=null, ❌ preis_ab=null, ❌ Keine Bilder, ❌ Ausstattung nur 1 Item |
| **Trust (4/10)** | Webseite + Telefon OK |
| **SEO (6/10)** | LodgingBusiness-Schema |
| **Klasse: C (48 Punkte)** | **Preise, Sterne, Bilder fehlen. Fix: Mittel** |

#### /unterkuenfte/alpeiner-nature-resort-tirol/
| Kriterium | Wert |
|---|---|
| **Content (6/10)** | ✅ Beschreibung OK |
| **Data (3/10)** | ❌ Sterne=null, ❌ preis_ab=null, ❌ Keine Bilder |
| **Trust (4/10)** | OK |
| **SEO (6/10)** | OK |
| **Klasse: C (48 Punkte)** | **Fix: Mittel** |

*(Statistische Auswertung aller 1111 Unterkünfte: 100% keine Bilder, 100% kein Preis, 89% keine Sterne, 75% keine E-Mail, 71% keine Ausstattung, 49% keine Webseite)*

### 5. GASTRO-ÜBERSICHT (/gastro/)
| Kriterium | Wert |
|---|---|
| **Content (5/10)** | Übersichtsseite mit Filter. Kein redaktioneller Text zur Tiroler Küche. |
| **Data (5/10)** | 3415 Einträge. Aber **52% ohne Adresse, 71% ohne Telefon, 57% ohne Webseite, 100% ohne Bilder und E-Mail**. |
| **Trust (3/10)** | Keine Quellen/Redaktion |
| **SEO (6/10)** | Titel + Description OK. JSON-LD ItemList. |
| **Klasse: C (48 Punkte)** | **Massenhaft fehlende Kontaktdaten. Fix: Mittel** |

### 6. SEHENSWÜRDIGKEITEN-ÜBERSICHT (/sehenswuerdigkeiten/)
| Kriterium | Wert |
|---|---|
| **Content (5/10)** | Listenansicht. Kein redaktioneller Überblick. |
| **Data (7/10)** | 154 Einträge, alle mit beschreibung, koordinaten, region, ort, kategorie. **100% ohne Bilder.** |
| **Trust (5/10)** | OK |
| **SEO (6/10)** | OK |
| **Klasse: C (58 Punkte)** | **Bilder fehlen vollständig. Fix: Niedrig-Mittel** |

### 7. EVENT-DETAIL (/events/adventkonzert-der-hofburgmusikanten/)
| Kriterium | Wert |
|---|---|
| **Content (7/10)** | ✅ Beschreibung vorhanden, Datum, Preis, Uhrzeit, Ort, Kategorie |
| **Data (7/10)** | ✅ Alle Felder gefüllt (bis auf Bilder) |
| **Trust (5/10)** | Keine Quellenangabe |
| **SEO (6/10)** | Event-Seite ohne Event-Schema (nur WebSite + Organization) |
| **Klasse: B (63 Punkte)** | **Event-Schema fehlt im JSON-LD, Bilder fehlen. Fix: Niedrig** |

### 8. MAGAZIN-ARTIKEL

#### /magazin/apres-ski-in-tirol-die-besten-adressen/
| Kriterium | Wert |
|---|---|
| **Content (8/10)** | ✅ Umfangreicher, gut geschriebener Artikel mit konkreten Locations, internen Links |
| **Data (8/10)** | ✅ Autor, Datum, Kategorie, Bilder, Tags, Koordinaten |
| **Trust (7/10)** | Autor "Redaktion", Datum Mai 2026. Keine echte Autorennennung. |
| **SEO (7/10)** | ✅ Gute interne Verlinkung, JSON-LD, OG |
| **Klasse: A (75 Punkte)** | **Bester Content-Typ der Website. Fix: Sehr niedrig** |

#### /magazin/die-besten-skigebiete-tirols-2026-im-vergleich/
| Kriterium | Wert |
|---|---|
| **Content (8/10)** | ✅ Sehr gut |
| **Data (8/10)** | ✅ Vollständig |
| **Trust (7/10)** | OK |
| **SEO (7/10)** | OK |
| **Klasse: A (75 Punkte)** | **Hervorragend** |

### 9. PREISE (/preise/)
| Kriterium | Wert |
|---|---|
| **Content (5/10)** | Preistabelle. Rein funktional. |
| **Data (5/10)** | OK |
| **Trust (5/10)** | N/A |
| **SEO (6/10)** | OK. Keine noindex. |
| **Klasse: C (53 Punkte)** | **Sollte evtl. noindex sein – ist nur für Betriebe relevant. Fix: optional** |

### 10. SUCHE (/suche/)
| Kriterium | Wert |
|---|---|
| **Content (3/10)** | Pagefind-UI. Kein eigenständiger Inhalt. |
| **Data (3/10)** | Technisch Pagefind. |
| **Trust (3/10)** | N/A |
| **SEO (4/10)** | Sollte noindex sein. |
| **Klasse: D (33 Punkte)** | **Muss noindex, befolgen. Fix: Sofort** |

---

## Übergreifende Probleme

### Kritisch (Sofort beheben)

| # | Problem | Betroffen | Impact |
|---|---|---|---|
| 1 | **Suche-Seite (/suche/) hat kein noindex** | 1 Seite | SEO: doppelter Content / dünne Seite |
| 2 | **Orte haben KEINE Beschreibung** | 258 Orte | Content: Haupt-Inhaltsseiten ohne Text |
| 3 | **Ötztal-Region ohne Langbeschreibung** | Regionenseite | Content: Top-Region ohne Content |
| 4 | **Tannheimer Tal fast leer** | Regionenseite | Content + Data |

### Hoch (Innerhalb 2 Wochen)

| # | Problem | Betroffen | Impact |
|---|---|---|---|
| 5 | **100% der Unterkünfte ohne Bilder** | 1.111 Seiten | Data + User Experience |
| 6 | **100% der Gastro ohne Bilder** | 3.415 Seiten | Data + User Experience |
| 7 | **100% der Sehenswürdigkeiten ohne Bilder** | 154 Seiten | Data + User Experience |
| 8 | **89% der Unterkünfte ohne Sterne** | ~988 Seiten | Data: Vergleichbarkeit |
| 9 | **100% der Unterkünfte ohne Preisangabe** | 1.111 Seiten | Data: Buchungsentscheidung |
| 10 | **71% der Gastro ohne Telefon** | ~2.400 Seiten | Data: Kontaktmöglichkeit |
| 11 | **52% der Gastro ohne Adresse** | ~1.800 Seiten | Data: Auffindbarkeit |

### Mittel (Nächster Sprint)

| # | Problem | Betroffen | Impact |
|---|---|---|---|
| 12 | **Kein OG-Image auf Detailseiten (hero_bild=null)** | Alle Detailseiten | SEO: Social Sharing |
| 13 | **Kein TouristDestination/TouristAttraction Schema** | Regionen + Orte | SEO: Rich Results |
| 14 | **Kein Event-Schema auf Event-Seiten** | 26 Events | SEO: Event Rich Snippets |
| 15 | **Homepage ohne redaktionellen Content** | 1 Seite | Content-Qualität |
| 16 | **Keine Autorenangabe (nur "Redaktion")** | Magazin | Trust |
| 17 | **Keine Quellenangaben auf Regionen** | Regionen | Trust |

---

## Gesamtklassifikation aller untersuchten Seiten

| URL | Klasse | Content | Data | Trust | SEO | Σ | Probleme |
|---|---|---|---|---|---|---|---|
| **/** (Startseite) | **C** | 6 | 5 | 3 | 8 | 55 | Kein redaktioneller Content, generischer Hero |
| **/regionen/oetztal/** | **D** | 3 | 5 | 3 | 7 | 45 | ❌ Keine Beschreibung/Tipps/Empfehlungen |
| **/regionen/zillertal/** | **B** | 8 | 6 | 3 | 7 | 60 | Gut. Bilder fehlen. |
| **/regionen/stubaital/** | **B** | 8 | 6 | 3 | 7 | 60 | Gut. Bilder fehlen. |
| **/regionen/kitzbuehel/** | **B** | 8 | 6 | 3 | 7 | 60 | Gut. Bilder fehlen. |
| **/regionen/innsbruck/** | **B** | 8 | 6 | 3 | 7 | 60 | Gut. Bilder fehlen. |
| **/regionen/tannheimer-tal/** | **D** | 1 | 2 | 2 | 5 | 25 | ❌ Fast komplett leer |
| **/orte/innsbruck/** | **D** | 2 | 4 | 2 | 6 | 35 | ❌ Keine Beschreibung, keine Bilder |
| **/orte/kitzbuehel/** | **D** | 2 | 4 | 2 | 6 | 35 | ❌ Wie alle Orte |
| **/orte/mayrhofen/** | **D** | 2 | 4 | 2 | 6 | 35 | ❌ |
| **/orte/soelden/** | **D** | 2 | 4 | 2 | 6 | 35 | ❌ |
| **/orte/seefeld/** | **D** | 2 | 4 | 2 | 6 | 35 | ❌ |
| **/unterkuenfte/activehotel-bergkonig/** | **C** | 6 | 4 | 4 | 6 | 50 | Kein Preis, Sterne, Bilder |
| **/unterkuenfte/almhof-family-resort-spa/** | **C** | 6 | 3 | 4 | 6 | 48 | Kein Preis, Sterne, Bilder |
| **/unterkuenfte/alpeiner-nature-resort-tirol/** | **C** | 6 | 3 | 4 | 6 | 48 | Kein Preis, Sterne, Bilder |
| **/gastro/** (Übersicht) | **C** | 5 | 5 | 3 | 6 | 48 | Massenhaft fehlende Felder |
| **/sehenswuerdigkeiten/** | **C** | 5 | 7 | 5 | 6 | 58 | Keine Bilder |
| **/events/adventkonzert-der-hofburgmusikanten/** | **B** | 7 | 7 | 5 | 6 | 63 | Event-Schema fehlt |
| **/magazin/apres-ski-in-tirol-die-besten-adressen/** | **A** | 8 | 8 | 7 | 7 | 75 | Hervorragend |
| **/magazin/die-besten-skigebiete-tirols-2026-im-vergleich/** | **A** | 8 | 8 | 7 | 7 | 75 | Hervorragend |
| **/preise/** | **C** | 5 | 5 | 5 | 6 | 53 | Nur für Betriebe relevant |
| **/suche/** | **D** | 3 | 3 | 3 | 4 | 33 | ❌ Kein noindex |

---

## Statistische Gesamtübersicht

| Content-Typ | Anzahl | Ø Content | Ø Data | Ø Trust | Ø SEO | Ø Σ | Ø Klasse |
|---|---|---|---|---|---|---|---|
| **Startseite** | 1 | 6.0 | 5.0 | 3.0 | 8.0 | 55.0 | C |
| **Regionen** | 14 | 6.6 | 5.4 | 3.0 | 7.0 | 55.0 | C |
| **Orte** | 258 | 3.0 | 4.5 | 2.0 | 6.0 | 38.0 | D |
| **Unterkünfte** | 1.111 | 5.5 | 3.5 | 4.0 | 6.0 | 47.5 | C |
| **Gastro** | 3.415 | 5.0 | 4.0 | 3.0 | 6.0 | 45.0 | C |
| **Sehenswürdigkeiten** | 154 | 6.5 | 6.0 | 5.0 | 6.0 | 58.5 | C |
| **Events** | 25 | 7.0 | 7.0 | 5.0 | 6.0 | 62.5 | B |
| **Magazin** | 45 | 8.0 | 8.0 | 7.0 | 7.0 | 75.0 | A |
| **Preise** | 1 | 5.0 | 5.0 | 5.0 | 6.0 | 53.0 | C |
| **Suche** | 1 | 3.0 | 3.0 | 3.0 | 4.0 | 33.0 | D |

---

## Priorisierte Maßnahmen

| Rang | Maßnahme | Typ | Aufwand | Impact |
|---|---|---|---|---|
| 1 | `/suche/` → noindex, nofollow | SEO | 5 min | 🔴 Verhindert Indexierungsprobleme |
| 2 | Beschreibungstexte für alle 258 Orte | Content | 2-3 Wochen | 🔴 Kern-Content aller Ortsseiten |
| 3 | Beschreibung für Ötztal + Tannheimer Tal nachtragen | Content | 2 Stunden | 🟠 Top-Regionen ohne Content |
| 4 | Bilder für Unterkünfte → JSON-Daten befüllen | Data | 1 Woche | 🟠 1.111 Seiten ohne Bilder |
| 5 | Preise + Sterne für Unterkünfte | Data | 1 Woche | 🟠 Fehlende Buchungsinfos |
| 6 | JSON-LD: Event-Schema, TouristDestination | SEO | 1 Tag | 🟡 Rich Snippets |
| 7 | OG-Images (Fallback) für alle Detailseiten | SEO | 1 Tag | 🟡 Social Sharing |
| 8 | Autoren + Quellen in Magazin + Regionen | Trust | 2 Tage | 🟡 Glaubwürdigkeit |
| 9 | Homepage redaktionell aufwerten | Content | 1 Tag | 🟡 Erster Eindruck |
| 10 | Adressen/Telefone für Gastro nachpflegen | Data | Laufend | 🟡 Kontaktierbarkeit |

---

## Fazit

**Die Website hat technisch ein solides Fundament** (Astro, i18n, JSON-LD, Pagefind), aber **inhaltlich große Lücken**:

1. **Dringend:** Ortsseiten haben NULL redaktionellen Content (258 Seiten)
2. **Dringend:** Suchseite fehlt noindex
3. **Hoch:** Region Ötztal + Tannheimer Tal ohne Beschreibung
4. **Hoch:** 100% fehlende Bilder bei Unterkünften, Gastro, Sehenswürdigkeiten
5. **Hoch:** 89% der Unterkünfte ohne Sterne, 100% ohne Preis
6. **Mittel:** Fehlende Schema-Typen (Event, TouristDestination)
7. **Gering:** Magazin und Events sind bereits gut bis sehr gut

**Empfehlung:** 
- **Phase 1 (Sofort):** noindex für Suche, Beschreibung für Ötztal + Tannheimer Tal
- **Phase 2 (2 Wochen):** Orte-Beschreibungen via KI/Redaktion generieren, Bilder-Pipeline fixen
- **Phase 3 (1 Monat):** Preise + Sterne für Unterkünfte, Schema-Erweiterungen, OG-Images
