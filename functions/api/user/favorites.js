// Cloudflare Function: Favoriten Toggle
// POST /api/user/favorites — Body: { collection, slug }

export async function onRequest(context) {
  const { request, env, data } = context;
  const user = data?.user;

  if (!user?.isLoggedIn) {
    return new Response(JSON.stringify({ error: 'Not authenticated' }), {
      status: 401, headers: { 'Content-Type': 'application/json' }
    });
  }

  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405, headers: { 'Content-Type': 'application/json' }
    });
  }

  try {
    const { collection, slug } = await request.json();

    const existing = await env.DB.prepare(
      'SELECT id FROM favorites WHERE user_id = ? AND collection = ? AND slug = ?'
    ).bind(user.id, collection, slug).all();

    if (existing.results.length > 0) {
      await env.DB.prepare(
        'DELETE FROM favorites WHERE user_id = ? AND collection = ? AND slug = ?'
      ).bind(user.id, collection, slug).run();

      return new Response(JSON.stringify({ favorited: false }), {
        status: 200, headers: { 'Content-Type': 'application/json' }
      });
    } else {
      await env.DB.prepare(
        'INSERT INTO favorites (user_id, collection, slug) VALUES (?, ?, ?)'
      ).bind(user.id, collection, slug).run();

      return new Response(JSON.stringify({ favorited: true }), {
        status: 200, headers: { 'Content-Type': 'application/json' }
      });
    }
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), {
      status: 500, headers: { 'Content-Type': 'application/json' }
    });
  }
}