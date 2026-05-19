// Cloudflare Function: User Dashboard API
// GET /api/user/dashboard

export async function onRequest(context) {
  const { request, env, data } = context;
  const user = data?.user;

  if (!user?.isLoggedIn) {
    return new Response(JSON.stringify({ error: 'Not authenticated' }), {
      status: 401, headers: { 'Content-Type': 'application/json' }
    });
  }

  try {
    const { results: favorites } = await env.DB.prepare(
      'SELECT collection, slug, created_at FROM favorites WHERE user_id = ? ORDER BY created_at DESC LIMIT 50'
    ).bind(user.id).all();

    return new Response(JSON.stringify({
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        tier: user.tier,
        subscription_status: user.subscription_status
      },
      favorites: favorites || []
    }), {
      status: 200, headers: { 'Content-Type': 'application/json' }
    });

  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), {
      status: 500, headers: { 'Content-Type': 'application/json' }
    });
  }
}