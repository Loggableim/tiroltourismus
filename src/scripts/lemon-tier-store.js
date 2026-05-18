/**
 * Tirol Tourismus — LemonSqueezy Tier Store (Client-Side)
 *
 * Manages user subscription tier in localStorage.
 * Works alongside Lemon.js to verify and store tier after checkout.
 *
 * USAGE:
 *   import { getUserTier, setUserTier, TIER_STORAGE_KEY } from '../scripts/lemon-tier-store.js';
 *
 * This replaces the inline demo-mode in PaywallOverlay with real
 * LemonSqueezy-verified subscription data stored client-side.
 *
 * NOTE: For a static GitHub Pages site, localStorage is the primary tier store.
 * In production with a backend, this would be replaced by server-side auth.
 */

export const TIER_STORAGE_KEY = 'tirol_user_tier';
export const SUBSCRIPTION_STORAGE_KEY = 'tirol_subscription_data';

/** Get the current user's tier from localStorage */
export function getUserTier() {
  try {
    return localStorage.getItem(TIER_STORAGE_KEY) || 'basic';
  } catch {
    return 'basic';
  }
}

/** Set the user's tier in localStorage */
export function setUserTier(tier, subscriptionData = null) {
  try {
    localStorage.setItem(TIER_STORAGE_KEY, tier);
    if (subscriptionData) {
      localStorage.setItem(SUBSCRIPTION_STORAGE_KEY, JSON.stringify(subscriptionData));
    }
  } catch (e) {
    console.warn('[Tirol] Could not save tier to localStorage:', e.message);
  }
}

/** Clear subscription data (logout / cancel) */
export function clearUserTier() {
  try {
    localStorage.removeItem(TIER_STORAGE_KEY);
    localStorage.removeItem(SUBSCRIPTION_STORAGE_KEY);
  } catch (e) {
    console.warn('[Tirol] Could not clear tier:', e.message);
  }
}

/** Get stored subscription details */
export function getSubscriptionData() {
  try {
    const raw = localStorage.getItem(SUBSCRIPTION_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function isSilverOrAbove() {
  const tier = getUserTier();
  return tier === 'silver' || tier === 'gold';
}

export function isGold() {
  return getUserTier() === 'gold';
}
