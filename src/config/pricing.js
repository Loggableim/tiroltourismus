/**
 * Tirol Tourismus — Pricing & LemonSqueezy Configuration
 *
 * HOW TO SET UP LEMONSQUEEZY:
 * 1. Create account at https://lemonsqueezy.com
 * 2. Create your store (e.g. "Tirol Tourismus")
 * 3. Create a product "Mitgliedschaft" with two variants:
 *    - "Silver" — 19€/month
 *    - "Gold" — 49€/month
 * 4. Copy the Store ID and Variant IDs below
 * 5. Set up webhook in LemonSqueezy Dashboard → Webhooks → Add endpoint
 *    URL: https://your-server.com/webhook/lemon-squeezy
 *    Events: order_created, subscription_created, subscription_updated, subscription_cancelled
 *
 * For the static site, Lemon.js handles client-side checkout verification.
 * The webhook server (webhook/server.js) syncs subscriptions server-side.
 */

export const LEMONSQUEEZY = {
  // ── REPLACE WITH YOUR REAL IDs ──
  storeId: 0,             // Your LemonSqueezy Store ID
  variants: {
    silver: 0,            // Your Silver variant ID (19€/month)
    gold: 0,              // Your Gold variant ID (49€/month)
  },
  // Lemon.js script URL
  scriptUrl: 'https://lmsqueezy.com/lemon.js',
};

/**
 * Tier definitions used across the site.
 * Controls access levels, pricing, and feature display.
 */
export const TIERS = {
  basic: {
    id: 'basic',
    label: 'Basic',
    emoji: '🌲',
    price: 0,
    period: 'Kostenlos',
    color: 'var(--text3)',
    badgeCls: 'badge-basic',
    description: 'Kostenloser Einstieg – entdecke Tirol.',
    features: [
      { text: 'Suchfunktion & Kartenansicht', included: true },
      { text: 'Kurzbeschreibung + Kontaktdaten', included: true },
      { text: 'Merkliste (Favoriten)', included: true },
      { text: 'Newsletter', included: true },
      { text: 'Vollständige Beschreibung & Bilder', included: false },
      { text: 'Erweiterte Filter & Sortierung', included: false },
      { text: 'Bessere Listenplatzierung', included: false },
      { text: 'Top-Listing (Gold-Badge)', included: false },
      { text: 'Analytics & Statistiken', included: false },
      { text: 'Keine Werbung', included: false },
    ],
  },
  silver: {
    id: 'silver',
    label: 'Silber',
    emoji: '🥈',
    price: 19,
    period: '/ Monat',
    color: 'var(--green)',
    badgeCls: 'badge-silver',
    description: 'Erweiterte Suche + bessere Sichtbarkeit.',
    cta: 'Jetzt Silber buchen',
    popular: false,
    features: [
      { text: 'Suchfunktion & Kartenansicht', included: true },
      { text: 'Kurzbeschreibung + Kontaktdaten', included: true },
      { text: 'Merkliste (Favoriten)', included: true },
      { text: 'Newsletter', included: true },
      { text: 'Vollständige Beschreibung & Bilder', included: true },
      { text: 'Erweiterte Filter & Sortierung', included: true },
      { text: 'Bessere Listenplatzierung', included: true },
      { text: 'Top-Listing (Gold-Badge)', included: false },
      { text: 'Analytics & Statistiken', included: false },
      { text: 'Keine Werbung', included: false },
    ],
  },
  gold: {
    id: 'gold',
    label: 'Gold',
    emoji: '⭐',
    price: 49,
    period: '/ Monat',
    color: 'var(--gold)',
    badgeCls: 'badge-gold',
    description: 'Full Access – Alles sehen. Alles wissen.',
    cta: 'Jetzt Gold buchen',
    popular: true,
    features: [
      { text: 'Suchfunktion & Kartenansicht', included: true },
      { text: 'Kurzbeschreibung + Kontaktdaten', included: true },
      { text: 'Merkliste (Favoriten)', included: true },
      { text: 'Newsletter', included: true },
      { text: 'Vollständige Beschreibung & Bilder', included: true },
      { text: 'Erweiterte Filter & Sortierung', included: true },
      { text: 'Bessere Listenplatzierung', included: true },
      { text: 'Top-Listing (Gold-Badge)', included: true },
      { text: 'Analytics & Statistiken', included: true },
      { text: 'Keine Werbung', included: true },
    ],
  },
};

/** LemonSqueezy checkout URL builder (hosted checkout page) */
export function getCheckoutUrl(tierId) {
  const variantId = LEMONSQUEEZY.variants[tierId];
  if (!variantId || !LEMONSQUEEZY.storeId) {
    // Return a placeholder URL when not configured
    const base = LEMONSQUEEZY.storeId > 0
      ? `https://tiroltourismus.lemonsqueezy.com/checkout/buy/${variantId}`
      : '/preise/';
    return base;
  }
  return `https://tiroltourismus.lemonsqueezy.com/checkout/buy/${variantId}`;
}

/** Get the Lemon.js createCheckout config for a given tier */
export function getCheckoutConfig(tierId) {
  return {
    store: LEMONSQUEEZY.storeId,
    variant: LEMONSQUEEZY.variants[tierId],
  };
}
