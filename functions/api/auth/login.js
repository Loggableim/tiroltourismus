// Cloudflare Function: Login Endpoint (POST /api/auth/login)
// Akzeptiert E-Mail, gibt Session zurück

export async function onRequest(context) {
  const { request, env } = context;

  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405, headers: { 'Content-Type': 'application/json' }
    });
  }

  try {
    const { email } = await request.json();

    const { results } = await env.DB.prepare(
      'SELECT id, email, name, tier, subscription_status FROM users WHERE email = ?'
    ).bind(email).all();

    if (results.length === 0) {
      const userId = crypto.randomUUID();
      await env.DB.prepare(
        'INSERT INTO users (id, email, name, tier) VALUES (?, ?, ?, ?)'
      ).bind(userId, email, email.split('@')[0], 'basic').run();

      const cookie = `session=${userId}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${7 * 24 * 60 * 60}`;

      return new Response(JSON.stringify({
        success: true,
        user: { id: userId, email, tier: 'basic', isNewUser: true }
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json', 'Set-Cookie': cookie }
      });
    }

    const user = results[0];
    const cookie = `session=${user.id}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${7 * 24 * 60 * 60}`;

    return new Response(JSON.stringify({
      success: true,
      user: { id: user.id, email: user.email, name: user.name, tier: user.tier, subscription_status: user.subscription_status }
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json', 'Set-Cookie': cookie }
    });

  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), {
      status: 500, headers: { 'Content-Type': 'application/json' }
    });
  }
}