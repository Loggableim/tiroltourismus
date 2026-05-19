// Cloudflare Function: Premium-Gating
// Stellt sicher dass Premium-Inhalte NUR für Gold/Silver-User ausgeliefert werden

export function checkPremiumAccess(user, requestedTier = 'silver') {
  const tierOrder = ['basic', 'silver', 'gold'];
  const userTierIndex = tierOrder.indexOf(user?.tier || 'basic');
  const requiredTierIndex = tierOrder.indexOf(requestedTier);

  if (userTierIndex >= requiredTierIndex && user?.subscription_status === 'active') {
    return { allowed: true };
  }

  return {
    allowed: false,
    redirect: '/login?redirect=' + encodeURIComponent(self.location?.pathname || '')
  };
}