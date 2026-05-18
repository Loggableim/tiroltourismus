/**
 * Tirol Tourismus — LemonSqueezy Checkout Integration (Client-Side)
 *
 * Handles:
 * 1. Loading Lemon.js SDK
 * 2. Creating checkout sessions (overlay + hosted fallback)
 * 3. Verifying successful checkouts on return
 * 4. Storing subscription data in localStorage
 *
 * DEPENDENCY: lemon-tier-store.js (must be loaded first)
 *
 * USAGE:
 *   <script type="module">
 *     import { initLemonSqueezy, openCheckout } from '/scripts/lemon-squeezy.js';
 *     initLemonSqueezy();
 *     document.getElementById('checkoutBtn').onclick = () => openCheckout('silver');
 *   </script>
 */

// ── Config ──
// These are populated from the server-rendered pricing config
// or fall back to the values in src/config/pricing.js

let LEMON_CONFIG = {
  storeId: 0,
  variants: { silver: 0, gold: 0 },
};
let lemonLoaded = false;
let lemonQueue = [];

// ── Lemon.js SDK loader ──

/** Load the Lemon.js SDK from CDN */
function loadLemonScript() {
  return new Promise((resolve, reject) => {
    if (typeof window.createLemonSqueezy === 'function') {
      lemonLoaded = true;
      resolve();
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://lmsqueezy.com/lemon.js';
    script.async = true;
    script.onload = () => {
      lemonLoaded = true;
      // Process queued actions
      lemonQueue.forEach(fn => fn());
      lemonQueue = [];
      resolve();
    };
    script.onerror = () => {
      console.error('[Tirol] Failed to load Lemon.js SDK');
      reject(new Error('Failed to load Lemon.js'));
    };
    document.head.appendChild(script);
  });
}

// ── Public API ──

/**
 * Initialize the LemonSqueezy integration.
 * Call once on page load. Pass the server-side config.
 */
export function initLemonSqueezy(config) {
  if (config) {
    LEMON_CONFIG = config;
  }

  // Load Lemon.js
  loadLemonScript().catch(e => console.warn('[Tirol] Lemon.js init:', e.message));

  // Check for successful checkout on return (URL params)
  checkReturningCheckout();
}

/**
 * Wait for Lemon.js to be ready, then call the callback.
 */
function whenLemonReady(fn) {
  if (lemonLoaded && typeof window.createLemonSqueezy === 'function') {
    fn();
  } else {
    lemonQueue.push(fn);
    // Ensure loading started
    if (!lemonLoaded) loadLemonScript().catch(() => {});
  }
}

/**
 * Open a LemonSqueezy checkout overlay for the given tier.
 * Falls back to hosted checkout page if Lemon.js fails.
 */
export function openCheckout(tierId) {
  const variantId = LEMON_CONFIG.variants[tierId];
  if (!variantId || !LEMON_CONFIG.storeId) {
    // Not configured — redirect to pricing page
    window.location.href = '/preise/';
    return;
  }

  whenLemonReady(() => {
    try {
      window.createLemonSqueezy().then((lemonsqueezy) => {
        lemonsqueezy.CreateCheckout({
          store: LEMON_CONFIG.storeId,
          variant: variantId,
          // Redirect back here after payment
          redirectUrl: window.location.origin + window.location.pathname,
        });
      });
    } catch (e) {
      console.error('[Tirol] Checkout error:', e);
      // Fallback: redirect to hosted checkout
      window.location.href = `https://tiroltourismus.lemonsqueezy.com/checkout/buy/${variantId}`;
    }
  });
}

/**
 * Returns the hosted checkout URL for direct linking.
 */
export function getCheckoutUrl(tierId) {
  const variantId = LEMON_CONFIG.variants[tierId];
  if (!variantId || !LEMON_CONFIG.storeId) return '/preise/';
  return `https://tiroltourismus.lemonsqueezy.com/checkout/buy/${variantId}`;
}

// ── Checkout Completion Handling ──

/**
 * Check if we just returned from a successful LemonSqueezy checkout.
 * LemonSqueezy appends ?checkout_id=... to the redirect URL.
 */
function checkReturningCheckout() {
  const params = new URLSearchParams(window.location.search);
  const checkoutId = params.get('checkout_id');

  if (!checkoutId) return;

  console.log('[Tirol] Returning from checkout:', checkoutId);

  // We came back from a checkout — Lemon.js can verify the purchase
  // For now, determine tier from the variant ID in the URL or session
  // In production, the webhook handles this server-side

  whenLemonReady(async () => {
    try {
      const lemonsqueezy = await window.createLemonSqueezy();

      // Lemon.js provides a way to get checkout data
      // If we can verify the checkout, store the tier
      if (lemonsqueezy && lemonsqueezy.GetCheckoutData) {
        const data = await lemonsqueezy.GetCheckoutData({ checkoutId });
        if (data && data.variant_id) {
          const variantId = parseInt(data.variant_id);
          // Map variant ID to tier
          let tier = 'basic';
          if (variantId === LEMON_CONFIG.variants.silver) tier = 'silver';
          else if (variantId === LEMON_CONFIG.variants.gold) tier = 'gold';

          if (tier !== 'basic') {
            // Store the tier + subscription data
            const { getUserTier, setUserTier } = await import('./lemon-tier-store.js');
            setUserTier(tier, {
              checkoutId,
              variantId,
              verifiedAt: Date.now(),
            });
            console.log(`[Tirol] Tier set to ${tier} after checkout!`);
            // Reload to apply tier
            window.location.reload();
          }
        }
      }
    } catch (e) {
      console.warn('[Tirol] Checkout verification:', e.message);
    }
  });
}

// Auto-init on page load if script loaded as module
const scriptConfig = window.__TIROL_LEMON_CONFIG;
if (scriptConfig) {
  initLemonSqueezy(scriptConfig);
}
