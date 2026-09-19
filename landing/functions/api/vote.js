/**
 * POST /api/vote — Vote für eine soon-Sprache (it/es/zh)
 * GET  /api/votes — Aktuelle Vote-Counts
 *
 * Anti-Collusion:
 * - IP wird gehasht (SHA-256 mit Salt) — nie im Klartext gespeichert
 * - 1 Vote pro Sprache pro IP-Hash (KV-TTL 90 Tage)
 * - Rate-Limit: max 10 Votes/Stunde pro IP-Hash (global über alle Sprachen)
 * - Nur erlaubte Sprachen (it/es/zh)
 */

const ALLOWED_LANGS = ['it', 'es', 'zh'];
const VOTE_TTL = 90 * 24 * 60 * 60;       // 90 Tage: "hat für Sprache X gestimmt"
const RATE_TTL = 60 * 60;                  // 1 Stunde Rate-Limit-Fenster
const RATE_MAX = 10;                       // max Votes/Stunde/IP

async function sha256(text) {
  const data = new TextEncoder().encode(text);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return [...new Uint8Array(hash)].map(b => b.toString(16).padStart(2, '0')).join('');
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}

export async function onRequest(context) {
  const { request, env } = context;

  if (request.method === 'OPTIONS') {
    return json({}, 204);
  }

  const kv = env.VOTE_KV;
  if (!kv) {
    return json({ success: false, error: 'kv_not_configured' }, 500);
  }

  // ── GET: Counts ──
  if (request.method === 'GET') {
    const counts = {};
    for (const lang of ALLOWED_LANGS) {
      const v = await kv.get(`count:${lang}`);
      counts[lang] = v ? parseInt(v, 10) : 0;
    }
    return json({ success: true, counts });
  }

  // ── POST: Vote ──
  if (request.method === 'POST') {
    let body;
    try {
      body = await request.json();
    } catch (e) {
      return json({ success: false, error: 'invalid_json' }, 400);
    }

    const lang = String(body?.lang || '').toLowerCase();
    if (!ALLOWED_LANGS.includes(lang)) {
      return json({ success: false, error: 'invalid_lang' }, 400);
    }

    // IP-Hash (Salt aus Env oder Fallback)
    const ip = request.headers.get('CF-Connecting-IP') || request.headers.get('X-Forwarded-For') || 'unknown';
    const salt = env.VOTE_SALT || 'tirol-vote-2026';
    const ipHash = await sha256(`${salt}:${ip}`);

    // Rate-Limit (global pro IP)
    const rateKey = `rate:${ipHash}`;
    const rateRaw = await kv.get(rateKey);
    const rateCount = rateRaw ? parseInt(rateRaw, 10) : 0;
    if (rateCount >= RATE_MAX) {
      return json({ success: false, error: 'rate_limited' }, 429);
    }

    // Bereits gestimmt?
    const voteKey = `vote:${lang}:${ipHash}`;
    const existing = await kv.get(voteKey);
    if (existing) {
      const count = parseInt((await kv.get(`count:${lang}`)) || '0', 10);
      return json({ success: false, error: 'already_voted', count }, 409);
    }

    // Vote zählen
    const currentRaw = await kv.get(`count:${lang}`);
    const current = currentRaw ? parseInt(currentRaw, 10) : 0;
    const next = current + 1;

    await kv.put(`count:${lang}`, String(next));
    await kv.put(voteKey, '1', { expirationTtl: VOTE_TTL });
    await kv.put(rateKey, String(rateCount + 1), { expirationTtl: RATE_TTL });

    return json({ success: true, count: next, lang });
  }

  return json({ success: false, error: 'method_not_allowed' }, 405);
}
