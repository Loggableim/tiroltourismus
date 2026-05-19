// Cloudflare Function: Auth Middleware
// Läuft on the Edge — prüft Session-Cookie und injected User-Context

export async function onRequest(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);

  // Öffentliche Routen — kein Auth nötig
  const publicPaths = ['/', '/api/auth/login', '/api/auth/register', '/api/auth/callback'];
  if (publicPaths.some(p => url.pathname === p) || url.pathname.match(/\.(js|css|png|jpg|webp|svg|ico)$/)) {
    return await next();
  }

  // Session aus Cookie lesen
  const cookie = request.headers.get('Cookie') || '';
  const sessionMatch = cookie.match(/session=([^;]+)/);
  const sessionToken = sessionMatch ? sessionMatch[1] : null;

  if (!sessionToken) {
    context.data.user = { tier: 'basic', isLoggedIn: false };
    return await next();
  }

  // Session in D1 validieren
  try {
    const { results } = await env.DB.prepare(
      'SELECT id, email, name, tier, subscription_status FROM users WHERE id = ?'
    ).bind(sessionToken).all();

    if (results.length > 0) {
      context.data.user = { ...results[0], isLoggedIn: true };
    } else {
      context.data.user = { tier: 'basic', isLoggedIn: false };
    }
  } catch (e) {
    console.error('Auth error:', e);
    context.data.user = { tier: 'basic', isLoggedIn: false };
  }

  return await next();
}