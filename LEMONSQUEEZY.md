# 🍋 Tirol Tourismus — LemonSqueezy Integration

## Übersicht

Integration von LemonSqueezy für das Tirol Tourismus Abo-System:

- **Silver (19€/Monat):** Erweiterte Suche, bessere Listenplatzierung
- **Gold (49€/Monat):** Full Access, Top-Listing, Analytics, Werbefrei

## Komponenten

### 1. Pricing-Seite (`/preise/`)
Vergleichstabelle mit 3 Tiers (Basic, Silver, Gold) + Lemon.js Checkout-Buttons.
- Datei: `src/pages/preise/index.astro`
- Konfiguration: `src/config/pricing.js`

### 2. Client-Side Tier-Store
Speichert den Tier-Status im localStorage nach erfolgreichem LemonSqueezy-Checkout.
- `src/scripts/lemon-tier-store.js` — localStorage Utilities
- `src/scripts/lemon-squeezy.js` — Lemon.js SDK Integration

### 3. PaywallOverlay
Zeigt Premium-Inhalte hinter einer Glas-Effekt-Paywall für Basic-User.
- `src/components/PaywallOverlay.astro`
- Liest Tier aus localStorage (gesetzt nach Checkout)

### 4. Webhook-Server (optional)
Node.js/Express Server für serverseitige Webhook-Verarbeitung.
- `webhook/server.js`
- `webhook/package.json`

## Setup

### LemonSqueezy Account
1. Account erstellen: https://lemonsqueezy.com
2. Store anlegen (z.B. "Tirol Tourismus")
3. Produkt "Mitgliedschaft" mit zwei Varianten:
   - **Silver** — 19€/Monat
   - **Gold** — 49€/Monat
4. Store-ID und Variant-IDs in `src/config/pricing.js` eintragen

### Webhook (für Produktion)
```bash
cd webhook
npm install
export LEMONSQUEEZY_WEBHOOK_SECRET="dein-secret-aus-lemon-dashboard"
npm start
```

### Webhook in LemonSqueezy Dashboard einrichten
- **URL:** `https://dein-server.com/webhook/lemon-squeezy`
- **Events:** `order_created`, `subscription_created`, `subscription_updated`, `subscription_cancelled`

### Navigation
Der "/preise/" Link ist automatisch in der Hauptnavigation, im Mobile-Menü und im Footer eingebunden.

## Architecture

```
User → /preise/ (Vergleichstabelle)
     → Klick "Jetzt buchen"
     → Lemon.js Overlay / Hosted Checkout
     → Bezahlung bei LemonSqueezy
     → Redirect zurück zur Seite mit ?checkout_id=
     → JavaScript speichert Tier in localStorage
     → PaywallOverlay liest localStorage → Content freigeschaltet

Optional:
     → LemonSqueezy Webhook → webhook/server.js
     → Schreibt subscriptions.json
     → Astro Build liest subscriptions.json für SSR
```

## Hinweise

- Für reines Static Hosting (GitHub Pages) reicht die client-seitige localStorage-Lösung
- Der Webhook-Server ist optional und wird für serverseitige Persistenz benötigt
- Bei Neustart / Clear localStorage ist der Tier-Status zurückgesetzt (bis zum nächsten Checkout)
- In einer Produktionsumgebung mit Backend sollte localStorage durch einen echten Auth-Flow ersetzt werden
