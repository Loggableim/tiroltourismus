# Plan: Produkte für Unternehmer – Vollständige Integration

**Erstellt:** 18.05.2026
**Status:** ✅ Phase A+B+C abgeschlossen (LemonSqueezy eingerichtet, Preise konfiguriert, Paywall vorhanden)

---

## 1. Aktuelle Situation (Zusammenfassung)

| Bereich | Status | Details |
|---|---|---|
| `/fuer-betriebe/` Layout | ✅ Fertig | Buttons verlinken, Dodo-Hinweis ersetzt |
| `/fuer-betriebe/registrierung/` | ⚠️ Nur Frontend | Speichert in localStorage – API-Endpoint fehlt |
| `/preise/` Pricing-Seite | ✅ Fertig | Checkout-Buttons funktionieren |
| `src/config/pricing.js` | ✅ Fertig | `storeId: 379815`, `silver: 1671559`, `gold: 1671576` |
| `PaywallOverlay.astro` | ✅ Fertig | Existiert, wird von Unterkunfts/Camping-Seiten genutzt |
| `webhook/server.js` | ✅ Fertig | VARIANT_TIER_MAP befüllt |
| LemonSqueezy Account | ✅ Fertig | Store "Tirol Tourismus" aktiv, Silver 19€/Monat, Gold 49€/Monat |
| Betriebsregistrierung Backend | ❌ Fehlt | API-Endpoint für Server-Persistenz nötig |
| Server-Deployment | ❌ Fehlt | Webhook + Server müssen auf VPS |

---

## 2. Aufgaben & Reihenfolge

### Phase A: LemonSqueezy Account & Konfiguration
*(Voraussetzung für alles andere – du musst die IDs besorgen)*

1. **LemonSqueezy Store anlegen**
   - Account unter https://lemonsqueezy.com erstellen (du)
   - Store "Tirol Tourismus" anlegen (du)
   - Produkt "Mitgliedschaft" mit 2 Varianten (du):
     - **Silver** – 19€/Monat
     - **Gold** – 49€/Monat
   - Store-ID + Variant-IDs an mich weitergeben

2. **`src/config/pricing.js` aktualisieren**
   - `storeId` → echte ID
   - `variants.silver` / `variants.gold` → echte Variant-IDs
   - ✅ Checkout-Buttons auf `/preise/` funktionieren dann

3. **`webhook/server.js` – VARIANT_TIER_MAP befüllen**
   - Gleiche IDs wie in `pricing.js` eintragen
   - ✅ Webhook kann Subscriptions verarbeiten

### Phase B: Frontend-Fixes (kein Account nötig)

4. **Dodo Payments → LemonSqueezy Hinweis fixen**
   - Datei: `src/pages/fuer-betriebe/index.astro` Zeile 116
   - Alt: `"ℹ️ Preise in Vorbereitung. Zahlungsabwicklung über Dodo Payments."`
   - Neu: `"✅ Sichere Zahlungsabwicklung über LemonSqueezy. 14 Tage Geld-zurück-Garantie."`
   - Entfernt Verwirrung und signalisiert Seriosität

5. **Silver/Gold Buttons auf `/fuer-betriebe/` verdrahten**
   - Datei: `src/pages/fuer-betriebe/index.astro` Zeilen 94, 110
   - `<button>` → `<a href="/preise/">Jetzt starten →</a>`
   - ✅ Nutzer gelangen zur funktionierenden Pricing-Seite

### Phase C: Fehlende Komponenten bauen

6. **`PaywallOverlay.astro` erstellen**
   - Wird in `camping/[slug].astro` bereits importiert – Datei fehlt
   - Props: `{name: string, slug: string}`
   - Design: Glas-Paywall mit CTA zu `/preise/`
   - Liest `localStorage.getItem('tirol_user_tier')` für client-seitige Freischaltung
   - Zeigt: "Dieser Inhalt ist Silver/Gold-Mitgliedern vorbehalten"

7. **Paywall in Unterkunfts-Seite ergänzen**
   - `src/pages/unterkuenfte/[slug].astro` hat bereits premiumSections-Logik
   - Aber kein `<PaywallOverlay>` für Basic-User → einbauen
   - Gleiches Blur/Teaser-Muster wie bei Camping-Seite

### Phase D: Backend für Betriebsregistrierung

8. **API-Endpoint `/api/betrieb-register` im Webhook-Server**
   - Neue POST-Route in `webhook/server.js`
   - Nimmt Formulardaten entgegen
   - Validiert (wie im Frontend)
   - Speichert als JSON in `src/data/pending/{slug}/index.json`
   - Sendet Benachrichtigungs-E-Mail an Admin (optional, via MailerLite oder SMTP)
   - ✅ Betriebsregistrierung wird persistent

9. **BetriebRegistrationForm.tsx – API-Integration**
   - Nach localStorage-Speicherung → zusätzlich POST an `https://webhook.tiroltourismus.com/api/betrieb-register`
   - Fallback bei Netzwerkfehler: nur localStorage (wie bisher)
   - Admin sieht Einträge dann auch auf dem Server

### Phase E: Server-Deployment & Launch

10. **Webhook-Server auf VPS deployen**
    - VPS `root@136.175.83.177`
    - `webhook/` auf Server kopieren
    - `npm install` ausführen
    - `.env` mit echten Keys befüllen
    - systemd Service installieren (tirol-webhook.service existiert bereits)
    - Nginx-Reverse-Proxy für Port 3456 → Port 80/443
    - SSL via Let's Encrypt

11. **LemonSqueezy Webhook im Dashboard einrichten**
    - URL: `https://webhook.tiroltourismus.com/webhook/lemon-squeezy`
    - Events: `order_created`, `subscription_created`, `subscription_updated`, `subscription_cancelled`
    - ✅ Subscriptions werden serverseitig persistiert

12. **Newsletter-Webhook prüfen**
    - `POST /api/newsletter` funktioniert bereits (MailerLite konfiguriert)
    - Newsletter-Produktionsnahme im Frontend prüfen (aktuell sendet an MailerLite)

---

## 3. Abhängigkeiten

```
Phase A (LemonSqueezy Account)
  ├── Blockiert: Phase A2 (pricing.js) — deine Store/Variant-IDs nötig
  ├── Blockiert: Phase A3 (VARIANT_TIER_MAP) — selbe IDs
  └── Blockiert: Phase E11 (Webhook im Lemon-Dashboard)
  
Phase B (Frontend-Fixes)
  └── Keine Abhängigkeiten → kann sofort loslegen

Phase C (Paywall + Komponenten)
  └── Blockiert nicht, aber Paywall bringt erst Wert wenn Checkout funktioniert

Phase D (Betriebs-Backend)
  └── Blockiert: Phase E10 (Server-Deployment) für Live-Schaltung

Phase E (Server-Deployment)
  └── Blockiert: Phase A2 (pricing.js IDs) vor Lemon-Dashboard-Setup
```

**Umsetzbar ohne LemonSqueezy-Account sofort:** Phase B + Phase C + Phase D (lokal)

---

## 4. Dateien & Änderungen

| Datei | Aktion | Phase |
|---|---|---|
| `src/config/pricing.js` | `storeId` + `variants` befüllen | A2 |
| `webhook/server.js` (Zeile 94-98) | `VARIANT_TIER_MAP` befüllen | A3 |
| `src/pages/fuer-betriebe/index.astro` (Z. 116) | Dodo → LemonSqueezy Text | B4 |
| `src/pages/fuer-betriebe/index.astro` (Z. 94,110) | Button → Link zu /preise/ | B5 |
| `src/components/PaywallOverlay.astro` | **Neu erstellen** | C6 |
| `src/pages/unterkuenfte/[slug].astro` | Paywall einbauen | C7 |
| `webhook/server.js` (neue Route) | `POST /api/betrieb-register` | D8 |
| `src/components/BetriebRegistrationForm.tsx` | API-POST ergänzen | D9 |
| VPS: `/var/www/webhook/` | Server deployen | E10 |
| LemonSqueezy Dashboard | Webhook-URL eintragen | E11 |

---

## 5. Geschätzter Aufwand

| Phase | Aufwand | Wer |
|---|---|---|
| **A** – LemonSqueezy Account | 15 min (du) | Du |
| **A2/A3** – IDs eintragen | 5 min | Ich |
| **B** – Frontend-Fixes | 20 min | Ich |
| **C** – Paywall-Komponente | 45 min | Ich |
| **D** – Betriebs-Backend | 1 h | Ich |
| **E** – Server-Deployment | 1 h | Ich |

**Gesamt:** ~3-4 h Arbeit (nach deiner LemonSqueezy-Registrierung)

---

## 6. Fragen

1. Hast du bereits einen LemonSqueezy-Account oder soll ich dir die Schritte dafür erklären?
2. Soll der Webhook-Server auf dem bestehenden VPS (`root@136.175.83.177`) laufen oder ein neuer?
3. Soll ich mit Phase B + C (kein Account nötig) sofort starten, während du das LemonSqueezy-Setup machst?
