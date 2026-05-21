// Cloudflare Function: Betriebe-Registrierung
// POST /api/betriebe/register — speichert neue Betriebsanmeldung in D1
// GET /api/betriebe/pending — Admin: listet ausstehende Anmeldungen (nur mit Admin-Key)

export async function onRequest(context) {
  const { request, env } = context;
  
  // CORS
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, GET, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, Authorization' }
    });
  }

  try {
    // POST: Neue Registrierung
    if (request.method === 'POST') {
      const data = await request.json();
      const { name, typ, ort, beschreibung, telefon, email, webseite } = data;

      if (!name || !ort) {
        return new Response(JSON.stringify({ error: 'Name und Ort sind erforderlich' }), {
          status: 400, headers: { 'Content-Type': 'application/json' }
        });
      }

      const id = crypto.randomUUID();
      
      await env.DB.prepare(
        `INSERT INTO pending_betriebe (id, name, typ, ort, beschreibung, telefon, email, webseite, status)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')`
      ).bind(id, name, typ || '', ort, beschreibung || '', telefon || '', email || '', webseite || '').run();

      return new Response(JSON.stringify({
        success: true,
        id: id,
        message: 'Registrierung erfolgreich. Nach Freigabe durch unser Team ist Ihr Eintrag live.'
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
      });
    }

    // GET: Ausstehende Anmeldungen (Admin)
    if (request.method === 'GET') {
      const auth = request.headers.get('Authorization');
      if (auth !== 'Bearer admin-secret-token') {
        return new Response(JSON.stringify({ error: 'Unauthorized' }), {
          status: 401, headers: { 'Content-Type': 'application/json' }
        });
      }

      const { results } = await env.DB.prepare(
        'SELECT * FROM pending_betriebe WHERE status = ? ORDER BY created_at DESC LIMIT 50'
      ).bind('pending').all();

      return new Response(JSON.stringify({ betriebe: results || [] }), {
        status: 200, headers: { 'Content-Type': 'application/json' }
      });
    }

    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405, headers: { 'Content-Type': 'application/json' }
    });

  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), {
      status: 500, headers: { 'Content-Type': 'application/json' }
    });
  }
}
