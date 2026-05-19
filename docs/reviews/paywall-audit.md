# 🍋 Paywall-Audit — Tirol Tourismus

> **Datum:** 19.05.2026  
> **Auditor:** Hermes Agent (DeepSeek v4)  
> **Projekt:** F:/tiroltourismus — Astro 5 SSG  
> **Zahlungsprovider:** LemonSqueezy (Store #379815)

---

## 1. Executive Summary

Das Paywall-/Tier-System ist **architektonisch solide, aber operativ noch nicht umsatzbereit**. Es gibt drei Tiers (Basic/Silver/Gold), eine vollständige Checkout-Integration über LemonSqueezy (Lemon.js Overlay + Hosted Checkout Fallback), client-seitige localStorage-Freischaltung, eine Preise-Seite mit Feature-Vergleich und Webhook-Server. Jedoch fehlen **essenzielle Komponenten für echten Umsatz**: Keine mehrsprachigen Preise-Seiten (nur `/preise/`, keine `/en/preise/`), keine [locale]-Routen für `/fuer-betriebe/*`, und die Betriebsregistrierung trennt nicht zwischen Business (Zahler) und Endnutzer (Konsument).

---

## 2. Pricing-Konfiguration (`src/config/pricing.js`)

### ✅ Bewertung: GUT — sauber strukturiert

| Aspekt | Zustand |
|--------|---------|
| Tier-Definitionen (Basic/Silver/Gold) | ✅ Vollständig mit Preisen, Features, Badges, Farben |
| LemonSqueezy Store ID | ✅ `379815` |
| Silver Variant ID | ✅ `1671559` |
| Gold Variant ID | ✅ `1671576` |
| `getCheckoutUrl(tierId)` | ✅ Baut korrekte LemonSqueezy Hosted Checkout URL |
| `getCheckoutConfig(tierId)` | ✅ Für Lemon.js Overlay |
| Feature-Listen | ✅ Alle 10 Features pro Tier definiert |

### ⚠️ Kritikpunkte

1. **Feature-Listen sind identisch strukturiert, aber inkonsistent getestet** — Die `features`-Arrays in `TIERS` haben alle 10 Einträge. Die Vergleichstabelle auf `/preise/` iteriert über `TIERS.basic.features`, was funktioniert, solange alle Tiers gleich viele Features haben. Fügt man später Features nur für Gold hinzu, bricht die Tabelle.

2. **Kein Annual/Monthly Toggle** — Es gibt nur Monatspreis (`/ Monat`). Kein Jahresrabatt (z.B. 190€/Jahr statt 228€), was die Conversion verbessern würde.

3. **Hartkodierte Variant-IDs** — Die IDs `1671559` und `1671576` sind im Webhook-Server dupliziert (`VARIANT_TIER_MAP`). Bei Änderung müssten beide Stellen aktualisiert werden.

---

## 3. PaywallOverlay (`src/components/PaywallOverlay.astro`)

### ✅ Bewertung: FUNKTIONIERT — gute UX

- Glassmorphism-Layout mit Blur-Effekt
- Tier-Vergleichs-Visualisierung (Basic → Silver → Gold)
- CTA-Buttons verlinken zur `/preise/`-Seite
- Client-seitige Logik liest `localStorage` (`tirol_user_tier`)

### 🔍 Wie wird der Overlay getriggert?

**Der Overlay ist IMMER sichtbar für Basic-Tier.** Die Logik funktioniert so:

1. **Server-seitig (Build-Zeit):** Auf der Detailseite (`src/pages/unterkuenfte/[slug].astro`, Zeile 17) wird `const tier = entry.tier || 'basic'` ermittelt. Für `isBasic` wird die komplette Detailseite hinter einen Blur-Overlay gelegt.

2. **Client-seitig:** Das `is:inline` Script in `PaywallOverlay.astro` (Zeilen 59-98) liest `localStorage.getItem('tirol_user_tier')`. Ist der Wert `silver` oder `gold`, wird der Overlay per `display: none` ausgeblendet.

3. **Wichtig:** Der Overlay blendet den Content nicht aus — er überlagert ihn nur visuell. Der Content ist im DOM vorhanden (für SEO), aber mit `opacity: 0.3; filter: blur(4px); pointer-events: none`.

### ⚠️ Kritikpunkte

1. **Nur für Unterkünfte & Camping implementiert** — Andere Content-Typen (Gastro, Erlebnisse, Sehenswürdigkeiten, Events) haben KEINEN Overlay, obwohl sie ebenfalls Tier-Daten haben könnten.

2. **Overlay-Links sind hartkodiert auf `/preise/`** — Nicht auf die jeweiligen LemonSqueezy-Checkout-URLs. Der Nutzer muss erst zur Preise-Seite navigieren, dann dort auf "Jetzt buchen" klicken. **Ein direkter Checkout-Link im Overlay würde Conversions erhöhen.**

3. **Kein "Schon Kunde?"-Link** — Es gibt keine Möglichkeit für zahlende Kunden, ihren Tier-Status wiederherzustellen (z.B. per E-Mail/Code), falls der localStorage gelöscht wird.

---

## 4. Unterkunftsdetailseiten (`src/pages/unterkuenfte/[slug].astro`)

### ✅ Bewertung: SOLIDE

| Aspekt | Zustand |
|--------|---------|
| Tier aus `entry.tier` ausgelesen | ✅ |
| Badge-Visualisierung (Gold/Silver/Basic) | ✅ |
| Gold-Highlighting (goldener Hero-Hintergrund) | ✅ |
| Basic: gedämpfter Stil, reduzierter Content | ✅ |
| Premium-Sektionen nur für Silver/Gold | ✅ |
| Paywall-Overlay nur bei Basic | ✅ |
| Sortierung nach Tier auf Listing-Seite (Gold → Silver → Basic) | ✅ |
| Tier-Filter auf Listing-Seite | ✅ |

### 🔍 Wie wird Tier angezeigt?

- **Badge** im Hero: `⭐ Gold` (gold-gradient), `Silber` (grün), `Basic` (grau)
- **Gold-Styling:** Hero bekommt `background: var(--gold-soft)`, Badge bekommt Gold-Gradient
- **Listing-Karten:** `AccommodationCard.astro` zeigt Badge-Badge für Gold/Silver
- **Sortierung:** Auf `/unterkuenfte/` werden Gold zuerst, dann Silver, dann Basic gelistet
- **Tier-Filter:** Tab-Switcher "Alle Stufen | ⭐ Gold | Silber | Basic"

### ⚠️ Kritikpunkte

1. **Tier wird NUR für Unterkünfte & Camping visuell dargestellt** — Gastro, Erlebnisse, Events, Sehenswürdigkeiten haben keine Tier-Logik, obwohl sie im Content-Modell ein `tier`-Feld haben könnten.

2. **Kein "Upgrade"-Button auf der Detailseite** — Wenn ein Basic-Nutzer eine Gold-Unterkunft sieht, gibt es keinen direkten "Zu Gold upgraden"-CTA. Der Overlay verlinkt nur generisch auf `/preise/`.

---

## 5. Checkout-Flow

### ✅ Bewertung: GUT — zwei Wege, mit Fallback

**Weg 1: Lemon.js Overlay (bevorzugt)**
```
/preise/ → Klick "Jetzt buchen" → Lemon.js Overlay → Bezahlung → Redirect zurück → localStorage wird gesetzt
```

**Weg 2: Hosted Checkout (Fallback)**
```
/preise/ → Klick → LemonSqueezy Hosted Page → Bezahlung → Redirect zurück → localStorage wird gesetzt
```

**Details zur Freischaltung nach Checkout:**

1. LemonSqueezy redirected zurück mit `?checkout_id=...`
2. `handleCheckoutSuccess()` versucht via `Lemon.js GetCheckoutData()` die Variant-ID zu verifizieren
3. Bei Erfolg: `localStorage.setItem('tirol_user_tier', 'silver'|'gold')` + Subscription-Daten
4. Erfolgs-Banner wird 5 Sekunden angezeigt
5. PaywallOverlay liest localStorage und blendet Content ein

**Fallback:** Wenn Lemon.js nicht geladen werden kann, wird ein Pending-Flag gesetzt (`tirol_checkout_pending_${checkoutId}`). Beim nächsten Seitenbesuch auf `/preise/` wird dieser innerhalb von 24h als "Silver" interpretiert.

### ⚠️ Kritikpunkte

1. **Kein Cross-Device-Sync** — localStorage ist gerätegebunden. Ein User, der auf dem Handy kauft, hat auf dem Desktop keine Freischaltung. Der Webhook-Server existiert, aber es gibt keine client-seitige Abfrage der Subscription-Daten.

2. **Pending-Fallback setzt IMMER Silver** — Zeile 285-288: Wenn ein Pending-Checkout existiert und der User noch `basic` ist, wird `silver` gesetzt — auch wenn es ein Gold-Kauf war. Der Variant wird nicht gespeichert/geprüft.

3. **Keine Subscription-Validierung** — Es gibt keine Überprüfung, ob die Subscription noch aktiv ist (z.B. gekündigt). Einmal gesetzt, bleibt der Tier-Status im localStorage bis zur manuellen Löschung.

4. **Redirect URL ist `/preise/`** (Zeile 209) — Nach erfolgreichem Kauf landet der Nutzer wieder auf der Preise-Seite, nicht auf der zuletzt besuchten Detailseite.

---

## 6. localStorage-Freischaltung

### ✅ Existiert: JA — Client-seitig

| Komponente | Pfad |
|------------|------|
| Tier Store | `src/scripts/lemon-tier-store.js` |
| Lemon.js Integration | `src/scripts/lemon-squeezy.js` |
| PaywallOverlay Script (inline) | `src/components/PaywallOverlay.astro` (Zeilen 59-98) |

**Speicherschlüssel:**
- `tirol_user_tier` — `'basic'` | `'silver'` | `'gold'`
- `tirol_subscription_data` — JSON mit `{ checkoutId, variantId, tier, verifiedAt }`
- `tirol_checkout_pending_${id}` — Timestamp

### ⚠️ Kritikpunkte

1. **Keine serverseitige Persistenz** — localStorage ist flüchtig (Cache-Leerung, anderer Browser = Tier weg). Der Webhook-Server speichert Subscriptions in `src/data/subscriptions/subscriptions.json`, aber **diese Datei wird vom Astro-Build NICHT eingelesen** (keine Import-Referenz gefunden).

2. **Keine Login/Auth-Integration** — Es gibt kein User-System. Die Tier-Freischaltung ist rein gerätebasiert. Für ein Abo-Modell ist das **nicht produktionsreif**.

3. **`lemon-tier-store.js` wird nirgends importiert** — Das Modul existiert, ist aber nicht in den Astro-Komponenten eingebunden. Der PaywallOverlay nutzt ein eigenes inline Script (Zeilen 59-98), das direkt auf `localStorage` zugreift — **Code-Duplizierung**.

---

## 7. Visuelle Tier-Erkennbarkeit

### ✅ Bewertung: GUT — klar erkennbar

| Ort | Basic | Silver | Gold |
|-----|-------|--------|------|
| Listing-Karten (`AccommodationCard`) | Kein Badge | 🟢 "Silber" Badge (grün) | 🟡 "⭐ Gold" Badge (gold-gradient) |
| Detailseite Hero | Tag "Basic" (grau) | Tag "Silber" (blau) | Tag "⭐ Gold" (gold) |
| Detailseite Hero-Hintergrund | normal, 85% opacity | normal | gold-soft Hintergrund |
| Preise-Seite | 🌲 Emoji, grauer Text | 🥈 Emoji, grün | ⭐ Emoji, gold |
| PaywallOverlay | Grauer Badge | Grüner Badge | Gold-Badge |

### ⚠️ Kritikpunkte

1. **Inkonsistente Badge-Farben** — Silver hat auf der Detailseite `tag-blue` (blau), aber im Overlay und auf der Preise-Seite ist Silver grün. Die `pricing.js` definiert `color: 'var(--green)'` für Silver, aber `[slug].astro` Zeile 24 nutzt `tag-blue`.

2. **Basic ist kaum sichtbar** — Basic-Einträge haben keinen Badge auf Listing-Karten. Das ist beabsichtigt (Basic ist der Default), aber Nutzer können nicht erkennen, dass ein Eintrag Basic ist (nur beim Hovern/Inspizieren des data-tier Attributs).

---

## 8. `/preise/` Seite (`src/pages/preise/index.astro`)

### ✅ Bewertung: GUT — vollständig und gut gestaltet

| Sektion | Zustand |
|---------|---------|
| Hero mit Titel "Wähle Dein Paket" | ✅ |
| 3 Pricing Cards (Basic/Silver/Gold) | ✅ |
| Gold als "Beliebteste Wahl" hervorgehoben | ✅ |
| Feature-Vergleichstabelle | ✅ |
| FAQ (6 Fragen) | ✅ |
| CTA-Banner "Noch unentschlossen?" | ✅ |
| Lemon.js Client-Integration | ✅ |
| Checkout-Success-Handling | ✅ |
| Pending-Checkout-Recovery | ✅ |

### ⚠️ Kritikpunkte

1. **Nur auf Deutsch verfügbar** — Es gibt **keine** `/en/preise/`-Route. Die Seite ist unter `src/pages/preise/index.astro`, nicht unter `src/pages/[locale]/preise/index.astro`. Für englischsprachige Nutzer existiert die Pricing-Seite nicht.

2. **Checkout-Buttons nutzen `onclick` mit inline `window.__openCheckout`** — nicht das modulare `lemon-squeezy.js`. Das ist technisch okay, aber inkonsistent.

3. **Keine Testimonials / Social Proof** — Keine Kundenstimmen oder Vertrauens-Elemente.

4. **Features-Array-Abhängigkeit** — Die Vergleichstabelle iteriert `features.map()` basierend auf `TIERS.basic.features.length`. Bei unterschiedlich langen Feature-Arrays würde sie brechen.

---

## 9. `/fuer-betriebe/registrierung/` (`src/pages/fuer-betriebe/registrierung/index.astro`)

### ✅ Existiert: JA

- Betriebs-Eigenregistrierung mit React-Formular (`BetriebRegistrationForm.tsx`)
- Speichert in `src/data/pending/` via Webhook-API `/api/betrieb-register`
- Admin kann Einträge approven/publishen/rejecten
- Erfolgsmeldung nach Absenden

### ⚠️ Kritikpunkte

1. **KEIN Upgrade-Flow für Betriebe** — Die Registrierungsseite erwähnt "🚀 Upgrade auf Silver/Gold für mehr Reichweite" in der Sidebar, aber es gibt:
   - Keinen "Gleich upgraden"-Button im Formular
   - Keinen Checkout-Link nach erfolgreicher Registrierung
   - Keine Logik, die beim Approven ein Tier setzt
   - Der Betrieb wird immer mit `"tier": "basic"` angelegt (webhook/server.js Zeile 360)

2. **Keine [locale]-Route** — Nur `/fuer-betriebe/registrierung/`, kein `/en/fuer-betriebe/registrierung/`

3. **Kein "Premium"-Onboarding** — Betriebe, die direkt mit Silver/Gold starten wollen, haben keinen eigenen Flow. Sie müssten erst Basic registrieren, dann auf `/preise/` upgraden — zwei separate Schritte.

4. **Keine Verbindung zum Paywall-System** — Die Betriebsregistrierung speichert in `src/data/pending/`, aber es gibt keine Logik, die einen Betrieb nach Zahlung automatisch auf Silver/Gold setzt.

---

## 10. Was fehlt / Blockiert Umsatz

### 🔴 KRITISCH (blockiert echten Umsatz)

| Problem | Impact | Fix-Aufwand |
|---------|--------|-------------|
| **Keine User-Authentifizierung** | localStorage ist nicht ausreichend für Abo-Modell. User verlieren Tier-Status bei Browser-Wechsel/Cache-Leerung. | Hoch — OAuth/Email-Login nötig |
| **Webhook-Server-Daten werden nicht genutzt** | `subscriptions.json` wird geschrieben, aber nie vom Astro-Build gelesen. Keine serverseitige Tier-Validierung. | Mittel |
| **Keine Subscription-Status-Prüfung** | Gekündigte Abos bleiben im localStorage aktiv. Kein Expiry-Check. | Mittel |
| **Keine mehrsprachige Preise-Seite** | Englische Nutzer können keine Preise sehen/keinen Checkout durchführen. | Gering |

### 🟡 MITTEL (erschwert Conversion)

| Problem | Impact | Fix-Aufwand |
|---------|--------|-------------|
| **Kein direkter Checkout aus PaywallOverlay** | Overlay verlinkt nur auf `/preise/`, nicht auf LemonSqueezy-Checkout. 2 Klicks statt 1. | Gering |
| **Betriebe haben keinen Upgrade-Pfad** | Registrierung → Basic. Kein Weg zu Silver/Gold ohne zweite Aktion. | Mittel |
| **Kein Cross-Device-Sync** | Kauf auf Handy ≠ Freischaltung auf Desktop. | Mittel |
| **Pending-Fallback setzt immer Silver** | Gold-Käufer bekommen möglicherweise nur Silver-Freischaltung. | Gering |
| **Keine Testimonials/Social Proof** | Preise-Seite hat keine Kundenstimmen. | Gering |

### 🟢 NIEDRIG (Qualität/UX)

| Problem | Impact | Fix-Aufwand |
|---------|--------|-------------|
| **Inkonsistente Silver-Farbe** (blau vs. grün) | Verwirrung, aber kein funktionales Problem. | Gering |
| **PaywallOverlay nur für Unterkünfte/Camping** | Andere Content-Typen haben keine Paywall. | Mittel |
| **Code-Duplizierung** (lemon-tier-store.js ungenutzt) | Wartbarkeit. | Gering |
| **Keine Jahresabos** | Verpasste Conversion-Chance. | Mittel |
| **Hartkodierte Variant-IDs** (dupliziert) | Wartungsproblem bei ID-Änderung. | Gering |

---

## 11. Architektur-Diagramm

```
┌─────────────────────────────────────────────────────────┐
│                   NUTZER (Browser)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ PaywallOverlay│  │ /preise/     │  │ /fuer-betriebe│  │
│  │ liest:        │  │ Lemon.js     │  │ /registrierung│  │
│  │ localStorage  │  │ Checkout     │  │ React Form    │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                 │                   │          │
│  ┌──────▼─────────────────▼───────────────────▼───────┐  │
│  │              localStorage                           │  │
│  │  tirol_user_tier: 'basic'|'silver'|'gold'          │  │
│  │  tirol_subscription_data: {...}                    │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                 LEMONSQUEEZY (extern)                     │
│  Store #379815                                           │
│  ├── Silver: Variant #1671559 (19€/Monat)                │
│  └── Gold:   Variant #1671576 (49€/Monat)                │
│                                                          │
│  Checkout → Redirect zu /preise/?checkout_id=...         │
│  Webhook  → POST /webhook/lemon-squeezy                  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              WEBHOOK SERVER (webhook/server.js)          │
│  Port 3456                                               │
│  ├── /webhook/lemon-squeezy  → subscriptions.json       │
│  └── /api/betrieb-register   → src/data/pending/        │
│                                                          │
│  ⚠ subscriptions.json wird NICHT vom Astro-Build        │
│    eingelesen — reine Datensenke!                        │
└─────────────────────────────────────────────────────────┘
```

---

## 12. Empfehlungen (nach Priorität)

### Sofort (vor Launch)
1. **Mehrsprachige `/en/preise/`-Route** erstellen
2. **Direkten Checkout-Link im PaywallOverlay** einbauen (statt nur `/preise/`)
3. **Subscription-Status-Validierung** im localStorage (Expiry-Datum speichern)
4. **Variant-ID-Mapping zentralisieren** (eine Single Source of Truth)

### Kurzfristig (erster Monat nach Launch)
5. **Einfaches Login-System** (Email + Magic Link) für Cross-Device-Sync
6. **Betriebe-Upgrade-Flow** in Registrierung integrieren
7. **Webhook-Daten im Build nutzen** (subscriptions.json einlesen)
8. **Silver-Farbkonsistenz** herstellen (grün statt blau)

### Mittelfristig
9. **PaywallOverlay auf alle Content-Typen** ausweiten
10. **Jahresabos** mit Rabatt anbieten
11. **Testimonials/Social Proof** auf Preise-Seite
12. **Email-Benachrichtigung nach Kauf** mit Wiederherstellungs-Link

---

## 13. Fazit

Das Paywall-System ist **technisch durchdacht und gut strukturiert**, aber **operativ noch nicht umsatzbereit**. Die größte Schwachstelle ist die **rein client-seitige Tier-Speicherung** ohne Authentifizierung — das funktioniert für ein statisches Demo, aber nicht für ein echtes Abo-Geschäft. Der Webhook-Server existiert und verarbeitet Zahlungen korrekt, aber seine Daten werden nicht genutzt.

**Positiv hervorzuheben:**
- Saubere Trennung von Pricing-Konfiguration und UI
- LemonSqueezy-Integration mit Overlay + Fallback
- Gute visuelle Tier-Erkennbarkeit
- Feature-Vergleichstabelle
- Betriebsregistrierung mit Admin-Review-Prozess

**Gesamteindruck:** ~65% umsatzbereit. Mit den o.g. Sofort-Maßnahmen erreichbar: ~80%.
