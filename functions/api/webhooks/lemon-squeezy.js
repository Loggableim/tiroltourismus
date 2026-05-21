// Cloudflare Function: LemonSqueezy Webhook Handler
// POST /api/webhooks/lemon-squeezy

export async function onRequest(context) {
  const { request, env } = context;

  if (request.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }

  try {
    const payload = await request.json();
    const eventName = payload.meta?.event_name || '';
    const attributes = payload.data?.attributes || {};

    console.log('LemonSqueezy Event:', eventName);

    switch (eventName) {
      case 'subscription_created':
      case 'subscription_updated': {
        const customerEmail = attributes.user_email || '';
        const status = attributes.status || '';
        const subscriptionId = payload.data?.id || '';

        const { results } = await env.DB.prepare(
          'SELECT tier FROM users WHERE email = ?'
        ).bind(customerEmail).all();

        await env.DB.prepare(
          'UPDATE users SET subscription_id = ?, subscription_status = ?, lemon_squeezy_customer_id = ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?'
        ).bind(subscriptionId, status, customerEmail, customerEmail).run();

        await env.DB.prepare(
          'INSERT INTO subscriptions (id, user_id, lemon_squeezy_event, status, tier) VALUES (?, ?, ?, ?, ?)'
        ).bind(subscriptionId, customerEmail, eventName, status, results[0]?.tier || 'basic').run();
        break;
      }

      case 'subscription_cancelled':
      case 'subscription_expired': {
        const subId = payload.data?.id || '';
        const email = attributes.user_email || '';

        await env.DB.prepare(
          "UPDATE users SET tier = 'basic', subscription_status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE email = ?"
        ).bind(email).run();

        await env.DB.prepare(
          'INSERT INTO subscriptions (id, user_id, lemon_squeezy_event, status) VALUES (?, ?, ?, ?)'
        ).bind(subId, email, eventName, 'cancelled').run();
        break;
      }
    }

    return new Response(JSON.stringify({ received: true }), {
      status: 200, headers: { 'Content-Type': 'application/json' }
    });

  } catch (e) {
    console.error('Webhook error:', e);
    return new Response(JSON.stringify({ error: e.message }), {
      status: 500, headers: { 'Content-Type': 'application/json' }
    });
  }
}