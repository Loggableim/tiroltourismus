# S1 - Meta Descriptions Audit

**Datum:** 2026-05-18
**Quelle:** Analyse aller `[slug].astro` Seiten unter `src/pages/`
**Geprüft:** 9 Collection-Seiten + 1 Locale-Variante + BaseLayout.astro Fallback

---

## Fallback-Mechanismus

**BaseLayout.astro (Zeile 35):**
```js
const siteDesc = description || 'Das offizielle Tourismusportal für Tirol – Berge, Seen, Wanderwege, Skigebiete und Unterkünfte.';
```
✅ Es gibt einen generischen Site-Fallback (~120 Zeichen). Dieser greift, wenn `description` `undefined` oder `null` ist.

**DetailPage.astro (Zeile 25):**
```ts
description?: string;
```
`description` ist optional und wird direkt an BaseLayout durchgereicht.

---

## Prüfung der Einzelseiten

### 1. regionen/[slug].astro
| | |
|---|---|
| **Datei** | `src/pages/regionen/[slug].astro` |
| **Status** | ✅ OK |
| **description** | `{kurzbeschreibung}` (Zeile 23) |
| **Typ** | Dynamisch aus Entry-Daten |
| **Fallback** | BaseLayout-Fallback bei undefined/null |
| **Beispiel** | `"Der Achensee ist Tirols größter See – türkisblaues Wasser umrahmt von steilen Bergflanken, bekannt als das „Meer der Alpen“."` (~150 Zeichen ✅) |
| **Empfehlung** | Keine Änderung nötig |

### 2. [locale]/regionen/[slug].astro
| | |
|---|---|
| **Datei** | `src/pages/[locale]/regionen/[slug].astro` |
| **Status** | ✅ OK |
| **description** | `{kurzbeschreibung}` (Zeile 94) |
| **Typ** | Dynamisch aus Entry-Daten (locale-aware) |
| **Empfehlung** | Keine Änderung nötig |

### 3. orte/[slug].astro
| | |
|---|---|
| **Datei** | `src/pages/orte/[slug].astro` |
| **Status** | ✅ OK |
| **description** | `{kurzbeschreibung}` (Zeile 41) |
| **Typ** | Dynamisch aus Entry-Daten |
| **Beispiel** | `"Landeshauptstadt Tirols, umgeben von 2.500m hohen Bergen. Altstadt mit Goldenem Dachl, Hofburg und moderner Architektur."` (~130 Zeichen ✅) |
| **Empfehlung** | Keine Änderung nötig |

### 4. sehenswuerdigkeiten/[slug].astro
| | |
|---|---|
| **Datei** | `src/pages/sehenswuerdigkeiten/[slug].astro` |
| **Status** | ✅ OK |
| **description** | `{entry.kurzbeschreibung}` (Zeile 55) |
| **Typ** | Dynamisch aus Entry-Daten |
| **Empfehlung** | Keine Änderung nötig |

### 5. gastro/[slug].astro
| | |
|---|---|
| **Datei** | `src/pages/gastro/[slug].astro` |
| **Status** | ✅ OK |
| **description** | `{entry.kurzbeschreibung || \`${entry.name} – ${entry.ort || 'Tirol'}. ${entry.kategorie || 'Kulinarik'}\`}` (Zeile 44) |
| **Typ** | Dynamisch + Fallback-Template |
| **Beispiel Fallback** | `"Almwirtschaft Achensee – Pertisau. Almwirtschaft"` (~50 Zeichen ⚠️ kurz, aber nur als Fallback) |
| **Empfehlung** | Fallback ist knapp, aber akzeptabel da er nur bei fehlender kurzbeschreibung greift. Optional: Fallback auf `entry.beschreibung` ausweiten. |

### 6. unterkuenfte/[slug].astro
| | |
|---|---|
| **Datei** | `src/pages/unterkuenfte/[slug].astro` |
| **Status** | ❌ **ZU KURZ / GENERISCH** |
| **description** | `` {`${entry.name} – ${entry.ort || 'Tirol'}. ${(entry.typ && typLabel[entry.typ]) || 'Unterkunft'}`} `` (Zeile 157) |
| **Typ** | Hartcodiertes Template — **ignoriert `entry.kurzbeschreibung` und `entry.beschreibung`** |
| **Beispiel** | `"Activehotel Bergkönig – Neustift im Stubaital. Hotel"` (~50 Zeichen ❌) |
| **Problem** | Die Entry-Daten haben ein `beschreibung`-Feld (~200-400 Zeichen), das ignoriert wird. Die current description ist viel zu kurz und generisch für SEO. |
| **Empfehlung** | `entry.beschreibung` nutzen, z.B.: `{entry.beschreibung ? entry.beschreibung.replace(/<[^>]*>/g, '').substring(0, 160) : \`${entry.name} – ${entry.ort || 'Tirol'}. ${(entry.typ && typLabel[entry.typ]) || 'Unterkunft'}\`}` |

### 7. camping/[slug].astro
| | |
|---|---|
| **Datei** | `src/pages/camping/[slug].astro` |
| **Status** | ❌ **ZU KURZ / GENERISCH** |
| **description** | `` {`${entry.name} – ${entry.ort || 'Tirol'}. Campingplatz in Tirol.`} `` (Zeile 186) |
| **Typ** | Hartcodiertes Template — **ignoriert `entry.beschreibung`** |
| **Beispiel** | `"Campingplatz XYZ – Neustift im Stubaital. Campingplatz in Tirol."` (~55 Zeichen ❌) |
| **Problem** | Noch kürzer und generischer als Unterkünfte. Beschreibung komplett ignoriert. |
| **Empfehlung** | `entry.beschreibung` nutzen, z.B.: `{entry.beschreibung ? entry.beschreibung.replace(/<[^>]*>/g, '').substring(0, 160) : \`${entry.name} – ${entry.ort || 'Tirol'}. Campingplatz in Tirol.\`}` |

### 8. erlebnisse/[slug].astro
| | |
|---|---|
| **Datei** | `src/pages/erlebnisse/[slug].astro` |
| **Status** | ✅ OK |
| **description** | `{entry.beschreibung || \`${entry.name} – ${entry.ort || 'Tirol'}. ${kategorieLabel[entry.kategorie] || ''}\`}` (Zeile 65) |
| **Typ** | Dynamisch aus Entry-Daten + Fallback |
| **Beispiel** | `"Schweben Sie über die Landeshauptstadt und genießen Sie einen atemberaubenden Blick..."` (~200 Zeichen ✅) |
| **Anmerkung** | Nutzt `beschreibung` statt `kurzbeschreibung` — Erlebnisse haben kein kurzbeschreibung-Feld. Länge ist gut. |
| **Empfehlung** | Keine Änderung nötig |

### 9. events/[slug].astro
| | |
|---|---|
| **Datei** | `src/pages/events/[slug].astro` |
| **Status** | ✅ OK |
| **description** | `` {`${entry.name || entry.titel} – ${entry.ort || 'Tirol'}. ${entry.kurzbeschreibung || entry.beschreibung || ''}`} `` (Zeile 74) |
| **Typ** | Konstruiertes Template mit Entry-Inhalten |
| **Beispiel** | `"Tiroler Bergsommer Festival – Innsbruck. Das größte Musikfestival der Alpen mit internationalen Acts..."` (~120 Zeichen ✅) |
| **Empfehlung** | Keine Änderung nötig |

### 10. magazin/[slug].astro
| | |
|---|---|
| **Datei** | `src/pages/magazin/[slug].astro` |
| **Status** | ✅ OK |
| **description** | `{entry.teaser}` (Zeile 39) |
| **Typ** | Dynamisch aus Entry-Daten |
| **Beispiel** | `"Sanfte Bergseen, rauschende Wasserfälle und grandiose Aussichten – Tirol hat unzählige leichte Wanderwege für Einsteiger. Wir zeigen die zehn schönsten Routen."` (~175 Zeichen ✅) |
| **Empfehlung** | Keine Änderung nötig |

---

## Zusammenfassung

| Collection | Status | description-Quelle | Länge (ca.) |
|---|---|---|---|
| regionen/[slug].astro | ✅ OK | `kurzbeschreibung` | 80–160 |
| [locale]/regionen/[slug].astro | ✅ OK | `kurzbeschreibung` | 80–160 |
| orte/[slug].astro | ✅ OK | `kurzbeschreibung` | 80–160 |
| sehenswuerdigkeiten/[slug].astro | ✅ OK | `entry.kurzbeschreibung` | 80–160 |
| gastro/[slug].astro | ✅ OK | `entry.kurzbeschreibung` + Fallback | 50–160 |
| **unterkuenfte/[slug].astro** | ❌ **ZU KURZ** | Hartcodiertes Template | **~40–60** |
| **camping/[slug].astro** | ❌ **ZU KURZ** | Hartcodiertes Template | **~40–60** |
| erlebnisse/[slug].astro | ✅ OK | `entry.beschreibung` + Fallback | 100–250 |
| events/[slug].astro | ✅ OK | Konstruiert aus Entry-Daten | 80–200 |
| magazin/[slug].astro | ✅ OK | `entry.teaser` | 120–200 |
| BaseLayout-Fallback | ✅ OK | Generischer Site-Text | ~120 |

### Kritische Funde (Handlungsbedarf)

| # | Datei | Problem | Priorität |
|---|---|---|---|
| 1 | `unterkuenfte/[slug].astro` | Meta description ignoriert `entry.beschreibung` — stattdessen nur kurzes Template (Name + Ort + Typ). Ergibt ~40-60 Zeichen, SEO-technisch deutlich zu kurz. | 🔴 Hoch |
| 2 | `camping/[slug].astro` | Gleiches Problem wie unterkuenfte — hartcodiertes Template ohne Bezug zu Entry-Texten. Mit `"Campingplatz in Tirol."` besonders generisch. | 🔴 Hoch |

### Optionaler Verbesserungsvorschlag

- **gastro/[slug].astro**: Fallback könnte auf `entry.beschreibung` ausgeweitet werden, falls `kurzbeschreibung` fehlt. Aktuell ist der Fallback mit ~50 Zeichen recht knapp.
- Allgemein: Bei allen Collections, die HTML in `beschreibung` enthalten (unterkuenfte, camping), muss HTML gestripped werden (`replace(/<[^>]*>/g, '')`) + auf 160 Zeichen begrenzt werden.

---

## Empfohlene Änderungen

### unterkuenfte/[slug].astro (Zeile 157)
Aktuell:
```astro
  description={`${entry.name} – ${entry.ort || 'Tirol'}. ${(entry.typ && typLabel[entry.typ]) || 'Unterkunft'}`}
```
Empfohlen:
```astro
  description={entry.beschreibung
    ? entry.beschreibung.replace(/<[^>]*>/g, '').substring(0, 160)
    : `${entry.name} – ${entry.ort || 'Tirol'}. ${(entry.typ && typLabel[entry.typ]) || 'Unterkunft'}`}
```

### camping/[slug].astro (Zeile 186)
Aktuell:
```astro
  description={`${entry.name} – ${entry.ort || 'Tirol'}. Campingplatz in Tirol.`}
```
Empfohlen:
```astro
  description={entry.beschreibung
    ? entry.beschreibung.replace(/<[^>]*>/g, '').substring(0, 160)
    : `${entry.name} – ${entry.ort || 'Tirol'}. Campingplatz in Tirol.`}
```
