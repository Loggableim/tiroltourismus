# Gastro – Einträge außerhalb Tirols (Stand 17.10.2026)

Mechanismus analog **fakt-02** (`docs/fakt-02-nicht-tirol.md`) für die Collections
`unterkuenfte`/`camping`, jetzt auf die Collection **`gastro`** angewandt.

## Vorgehen

Kriterien (konservativ, identisch zu fakt-02):

- **Immer Tirol (nie ausblenden):** PLZ **6000–6699** bzw. **9900–9999**.
- **Ausblenden nur bei klarem Beleg außerhalb Tirols:**
  - deutsche 5-stellige PLZ (Ausland, z. B. bayerisches Allgäu / Werdenfelser Land),
  - österreichische PLZ außerhalb Tirols (5xxx Salzburg, 67xx–69xx Vorarlberg,
    9xxx außer 99xx Kärnten),
  - `tel +49` **ohne** Tirol-Region,
  - gleicher Betrieb liegt in einer anderen Collection sicher außerhalb Tirols.
- **Unklar (bleibt sichtbar):** keine Ort-/PLZ-/Telefonangabe, widersprüchliche
  Angaben, italienische PLZ (Südtirol) u. ä. – siehe unten.

Datenbasis: `src/data/gastro/` (Collection `gastro`). Die Einträge selbst bleiben im
Repo erhalten; sie werden über `src/data/_hidden-nicht-tirol.json` (Schlüssel
`gastro`) sprachübergreifend per Slug ausgeblendet (keine Seite, nicht in Listen /
Sitemap / Suche / Related-Links) und über `public/_redirects` per 301 auf die
Gastro-Übersicht umgeleitet.

Umfang dieses PRs: **eine Collection (gastro), 20 Slugs**. Die vollständige
Gastro-Datenbasis enthält weitere klare Nicht-Tirol-Fälle (siehe „Backlog“); diese
werden bewusst in Folge-PRs abgearbeitet, um die Task-Größe (10–20 Slugs) zu wahren.

## Ausgeblendet in diesem PR (20 Slugs)

Alle Einträge liegen in Bayern (Allgäu / Werdenfelser Land / Ammergauer Alpen) und
haben eine deutsche 5-stellige PLZ sowie eine passende deutsche Adresse. Beleg ist
jeweils die eigene Website des Betriebs (Stand 17.10.2026 erreichbar, Ort/PLZ im
Auftritt bestätigt) plus PLZ/Ort/Adresse aus dem Datensatz.

| Slug | Name | PLZ / Ort | Adresse | Beleg (eigene Website) |
|---|---|---|---|---|
| `4eck` | 4eck | 82467 Garmisch-Partenkirchen | Klammstraße 8 | https://www.4-eck.com/ |
| `alpe-dornach` | Alpe Dornach | 87561 Oberstdorf | Sesselweg 16 | https://www.alpe-dornach.de/ |
| `alte-druckerei` | Alte Druckerei | 82467 Garmisch-Partenkirchen | Fürstenstraße 3 | https://www.restaurant-altedruckerei.de/ |
| `alte-post` | Alte Post | 82487 Oberammergau | Dorfstraße 19 | https://altepost.com/ |
| `amrut` | Amrut | 87629 Füssen | Tiroler Straße 55 | https://amrut-fuessen.de/ |
| `antica-roma` | Antica Roma | 82467 Garmisch-Partenkirchen | Hauptstraße 44 | https://www.antica-roma-pizzeria.de |
| `b-ckerei-lipp` | Bäckerei Lipp | 87459 Pfronten | Meilinger Straße 2 | https://lipp-baeckerei.de/standorte/pfronten/ |
| `bellini-il-ristorantino` | Bellini - il ristorantino | 82481 Mittenwald | Malerweg 4 | https://www.ristorantino-bellini.de |
| `berggasthaus-bleckenau` | Berggasthaus Bleckenau | 87645 Schwangau | Bleckenau 2 | https://www.berggasthaus-bleckenau.de |
| `berggasthof-riefenkopf` | Berggasthof Riefenkopf | 87561 Oberstdorf | Riefenkopf 8 | https://www.gasthof-riefenkopf.de |
| `bungalow-7` | Bungalow 7 | 82467 Garmisch-Partenkirchen | Alpspitzstraße 7 | https://www.bungalow-7.de/ |
| `caf-restaurant-waidmannsheil` | Café Restaurant Waidmannsheil | 87541 Bad Hindelang | Talstraße 35 | https://www.waidmannsheil-hinterstein.de |
| `cafe-restaurant-karatsbichl` | Cafe Restaurant Karatsbichl | 87561 Oberstdorf | Karatsbichl 1 | https://www.karatsbichl.de/ |
| `das-lokal` | Das Lokal | 82481 Mittenwald | Bahnhofplatz 10 | https://www.daslokal-mittenwald.de |
| `gasthaus-ferchensee` | Gasthaus Ferchensee | 82481 Mittenwald | Am Ferchensee 1 | https://www.ferchensee.eu/ |
| `gasthof-adler` | Gasthof Adler | 87459 Pfronten | Tiroler Straße 7 | https://www.adlerpfronten.de/ |
| `gasthof-fraundorfer` | Gasthof Fraundorfer | 82467 Garmisch-Partenkirchen | Ludwigstraße 24 | https://www.gasthof-fraundorfer.de/ |
| `gasthof-sonnenhof` | Gasthof Sonnenhof | 82493 Krün | Hauptstraße 28 | https://www.sonnenhof-klais.de |
| `gasthof-und-hotel-zur-post` | Gasthof und Hotel "Zur Post" | 82499 Wallgau | Dorfplatz 6 | https://www.posthotel-wallgau.com/ |
| `maronis` | Maronis | 82467 Garmisch-Partenkirchen | Mohrenplatz 10 | https://www.maronis-gap.de/ |

## Unklar – bleibt sichtbar

Diese Fälle sind **nicht** ausgeblendet. Sie sind bewusst separat gelistet, damit Vali
entscheiden kann.

### Italienische PLZ / Südtirol (8)

Südtirol (Italien) ist nicht österreichisches Tirol; die Kriterien von fakt-02 deckten
nur deutsche und österreichische PLZ ab. **Konservativ: bleibt vorerst sichtbar.**

| Slug | Name | PLZ / Ort | Region |
|---|---|---|---|
| `cafe-zum-turm` | Cafe zum Turm | 39027 Graun im Vinschgau – Curon Venosta | landeck |
| `hofschank-waldlechn` | Hofschank Waldlechn | 39030 Ahrntal – Valle Aurina | – |
| `karl-s-imbiss-w-rstelstand` | Karl's Imbiss – Würstelstand | 39041 Brenner – Brennero | innsbruck-land |
| `kegelgasslalm` | Kegelgasslalm | 39030 Ahrntal – Valle Aurina | – |
| `kreuzwirt` | Kreuzwirt | 39030 Ahrntal – Valle Aurina | – |
| `pizzeria-hans` | Pizzeria Hans | 39027 Graun im Vinschgau – Curon Venosta | landeck |
| `waldneralm` | Waldneralm | 39030 Prettau | – |
| `wollbachalm-malga-rio-di-valle` | Wollbachalm – Malga Rio di Valle | 39030 Ahrntal – Valle Aurina | – |

### Weitere Auffälligkeiten (kein sicherer Beleg)

- `waldimbiss` – PLZ 87629 Füssen (DE) **und** `tel +49`, aber Region `ausserfern`
  gesetzt. PLZ ist eindeutig deutsch → klarer Fall, aber noch nicht in diesem PR
  (Backlog).
- `alpengasthof-stillupperhaus` – PLZ „2690" bei Ort Mayrhofen; Mayrhofen (Tirol) hat
  eigentlich PLZ 6290. Wahrscheinlich fehlerhaftes Feld → **nicht ausblenden**, Daten
  prüfen.
- Einträge ganz ohne Ort, PLZ und Telefon (kein Beleg möglich) → bleiben sichtbar.

## Redirects / Spracharchitektur

- Ziel: die je Sprache existierende Gastro-Übersichtsroute `/gastro/`.
- Jede Sprache wird als **Single-Lang-Build** auf ihre eigene Subdomain deployt
  (`BUILD_LANGS=<lang>`, siehe `.github/workflows/deploy.yml`); dort liegt die Übersicht
  jeweils unter `/gastro/`. Die Hauptdomain leitet die Sprach-Prefixe (`/en/*`, `/fr/*`
  …) bereits per Splat-Regel auf die jeweilige Subdomain um.
- Daher genügt – wie bei den bestehenden fakt-02-Regeln – **eine sprachunabhängige
  Regel pro Slug** (mit und ohne Trailing Slash), jeweils **vor** den Splat-Regeln.
  Die Regeln stehen in `public/_redirects` im Gastro-Block.
- Alle neuen Regeln sind **statisch** (kein `*`, kein `:splat`) und zählen nicht gegen
  das Cloudflare-Limit von 100 dynamischen Regeln.

## Backlog (nächste Gastro-PRs)

Aus der Datenbasis ergeben sich weitere **klare** Nicht-Tirol-Fälle, die aus
Größengründen nicht in diesem PR sind:

- deutsche 5-stellige PLZ: **296** Einträge gesamt, davon hier 20 ausgeblendet →
  **276 offen**.
- österreichische PLZ außerhalb Tirols (Salzburg/Vorarlberg/Kärnten): **74 offen**.
- italienische PLZ / Südtirol: **8** (siehe „Unklar", Entscheidung Vali ausstehend).

Vorschlag: Folge-Tasks je Bundesland/PLZ-Bereich (z. B. „Gastro DE 82xxx",
„Gastro DE 87xxx", „Gastro AT außerhalb Tirols").

## Gates

- `npm run test:content`
- `npm run check:content -- --no-network`
- `npm run build`
- `npm run check:content` (Netzwerk, beratend)
