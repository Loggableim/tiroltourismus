/**
 * Tirol Tourismus — LemonSqueezy Webhook Handler
 *
 * Standalone Express server that processes LemonSqueezy webhooks.
 * Updates the subscription data JSON file used by the static site.
 *
 * SETUP:
 * 1. npm install
 * 2. Create .env file with LEMONSQUEEZY_WEBHOOK_SECRET
 * 3. Set up webhook in LemonSqueezy Dashboard:
 *    - URL: https://your-server.com/webhook/lemon-squeezy
 *    - Events: order_created, subscription_created, subscription_updated, subscription_cancelled
 * 4. npm start
 *
 * The webhook writes to ../src/data/subscriptions/ which the Astro site
 * reads during build to pre-render tier-specific content.
 *
 * NOTE: For a static site, this is optional. The client-side Lemon.js
 * integration handles tier storage in localStorage without a server.
 * This server adds server-side verification and persistence.
 */

import express from 'express';
import cors from 'cors';
import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.resolve(__dirname, '..', 'src', 'data', 'subscriptions');
const PORT = process.env.PORT || 3456;
const WEBHOOK_SECRET = process.env.LEMONSQUEEZY_WEBHOOK_SECRET || '';

// Ensure data directory exists
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

const app = express();

// ── CORS — allow tiroltourismus.com ──
app.use(cors({
  origin: ['https://tiroltourismus.com', 'https://www.tiroltourismus.com', 'http://localhost:4321', 'http://localhost:3000'],
  methods: ['GET', 'POST'],
}));

// ── LemonSqueezy Webhook Signature Verification ──

function verifySignature(req, secret) {
  if (!secret) return true; // Skip verification if no secret configured

  const signature = req.headers['x-signature'];
  if (!signature) return false;

  // LemonSqueezy signs the raw body with HMAC-SHA256
  const payload = JSON.stringify(req.body);
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');

  // Constant-time comparison to prevent timing attacks
  if (signature.length !== expected.length) return false;

  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}

// ── Data Management ──

function getSubscriptionsPath() {
  return path.join(DATA_DIR, 'subscriptions.json');
}

function readSubscriptions() {
  const filePath = getSubscriptionsPath();
  try {
    if (fs.existsSync(filePath)) {
      return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    }
  } catch (e) {
    console.error('Error reading subscriptions:', e.message);
  }
  return {};
}

function writeSubscriptions(data) {
  const filePath = getSubscriptionsPath();
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
  console.log(`Subscriptions saved (${Object.keys(data).length} active)`);
}

// Map LemonSqueezy variant IDs to tier names (update these!)
const VARIANT_TIER_MAP = {
  // Example: 123456: 'silver',
  // Example: 123457: 'gold',
  // SET THESE to match your LemonSqueezy product variants
};

function getTierFromVariant(variantId) {
  const id = parseInt(variantId);
  return VARIANT_TIER_MAP[id] || 'basic';
}

// ── Webhook Endpoint ──

app.post('/webhook/lemon-squeezy', express.json(), (req, res) => {
  // Verify signature
  if (!verifySignature(req, WEBHOOK_SECRET)) {
    console.warn('Invalid webhook signature received');
    return res.status(401).json({ error: 'Invalid signature' });
  }

  const eventName = req.headers['x-event-name'] || 'unknown';
  const body = req.body;
  const { data } = body;

  console.log(`Webhook received: ${eventName}`, data?.id ? `(ID: ${data.id})` : '');

  try {
    switch (eventName) {
      case 'order_created':
      case 'subscription_created':
      case 'subscription_updated': {
        if (!data) break;

        const subscriptionId = data.id || data.attributes?.id || `sub_${Date.now()}`;
        const customerId = data.attributes?.customer_id || data.relationships?.customer?.data?.id || '';
        const variantId = data.attributes?.variant_id ||
          data.relationships?.variant?.data?.id ||
          data.variant_id ||
          '';

        // Get customer email if available (from included resources)
        let customerEmail = '';
        if (body.included) {
          for (const inc of body.included) {
            if (inc.type === 'customers' && inc.id === customerId?.toString()) {
              customerEmail = inc.attributes?.email || '';
            }
          }
        }

        const tier = getTierFromVariant(variantId);
        if (tier === 'basic') {
          console.log(`  → Unknown variant ${variantId}, defaulting to basic`);
        }

        // Status
        const status = data.attributes?.status || 'active';

        // Store subscription
        const subs = readSubscriptions();
        subs[subscriptionId] = {
          subscriptionId,
          customerId,
          customerEmail,
          variantId,
          tier,
          status,
          createdAt: data.attributes?.created_at || data.attributes?.createdAt || new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          cancelledAt: data.attributes?.cancelled_at || data.attributes?.cancelledAt || null,
        };
        writeSubscriptions(subs);

        console.log(`  → ${customerEmail || '(no email)'} → ${tier} (${status})`);
        break;
      }

      case 'subscription_cancelled': {
        if (!data || !data.id) break;

        const subs = readSubscriptions();
        const subId = data.id;

        if (subs[subId]) {
          subs[subId].status = 'cancelled';
          subs[subId].cancelledAt = data.attributes?.cancelled_at || new Date().toISOString();
          subs[subId].updatedAt = new Date().toISOString();
          writeSubscriptions(subs);
          console.log(`  → Subscription ${subId} cancelled`);
        }
        break;
      }

      default:
        console.log(`  → Unhandled event type: ${eventName}`);
    }

    res.json({ received: true });
  } catch (e) {
    console.error('Error processing webhook:', e);
    res.status(500).json({ error: 'Internal error' });
  }
});

// ── MailerLite Newsletter API ──

const MAILERLITE_API_KEY = process.env.MAILERLITE_API_KEY || '';
const MAILERLITE_GROUP_ID = process.env.MAILERLITE_GROUP_ID || '187803135383700493';

app.post('/api/newsletter', express.json(), async (req, res) => {
  const { email, name } = req.body;

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return res.status(400).json({ error: 'Valid email is required' });
  }

  if (!MAILERLITE_API_KEY) {
    return res.status(500).json({ error: 'MailerLite not configured' });
  }

  try {
    const mlRes = await fetch('https://connect.mailerlite.com/api/subscribers', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${MAILERLITE_API_KEY}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        email,
        fields: { name: name || '' },
        groups: [MAILERLITE_GROUP_ID],
      }),
    });

    const data = await mlRes.json();

    if (mlRes.ok) {
      console.log(`📬 Newsletter: ${email} subscribed`);
      res.json({ subscribed: true, id: data.data?.id });
    } else {
      console.error(`📬 MailerLite error:`, data);
      res.status(mlRes.status).json({ error: data.message || 'Subscription failed' });
    }
  } catch (e) {
    console.error('📬 Newsletter error:', e.message);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/subscriptions — list all subscriptions (for debugging)
app.get('/api/subscriptions', (req, res) => {
  const subs = readSubscriptions();
  // Filter out sensitive data for the public endpoint
  const publicSubs = {};
  for (const [id, sub] of Object.entries(subs)) {
    publicSubs[id] = {
      tier: sub.tier,
      status: sub.status,
      createdAt: sub.createdAt,
      updatedAt: sub.updatedAt,
    };
  }
  res.json(publicSubs);
});

// GET /health — health check
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    subscriptionsFile: getSubscriptionsPath(),
  });
});

// ── Start ──

app.listen(PORT, () => {
  console.log(`🍋 Tirol LemonSqueezy Webhook Server running on port ${PORT}`);
  console.log(`   Webhook URL: http://localhost:${PORT}/webhook/lemon-squeezy`);
  console.log(`   Newsletter API: http://localhost:${PORT}/api/newsletter`);
  console.log(`   Data directory: ${DATA_DIR}`);
  console.log(`   Webhook secret configured: ${WEBHOOK_SECRET ? '✅ Yes' : '❌ No (insecure — set LEMONSQUEEZY_WEBHOOK_SECRET env var)'}`);
  console.log(`   MailerLite configured: ${MAILERLITE_API_KEY ? '✅ Yes' : '❌ No (set MAILERLITE_API_KEY env var)'}`);
  console.log('');
  console.log('   REMEMBER: Update VARIANT_TIER_MAP in server.js with your');
  console.log('   LemonSqueezy product variant IDs before going live!');
});
