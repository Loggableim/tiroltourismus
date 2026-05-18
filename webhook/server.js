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

// ── E-Mail Benachrichtigung ──
let transporter = null;
try {
  const nodemailer = await import('nodemailer');
  // Use MailerLite SMTP or fallback to local sendmail
  const smtpHost = process.env.SMTP_HOST || 'smtp.gmail.com';
  const smtpPort = parseInt(process.env.SMTP_PORT || '587');
  const smtpUser = process.env.SMTP_USER || '';
  const smtpPass = process.env.SMTP_PASS || '';
  
  if (smtpUser && smtpPass) {
    transporter = nodemailer.default.createTransport({
      host: smtpHost,
      port: smtpPort,
      secure: smtpPort === 465,
      auth: { user: smtpUser, pass: smtpPass },
    });
    console.log(`📧 E-Mail-Benachrichtigung konfiguriert (${smtpUser})`);
  } else {
    console.log('📧 Keine SMTP-Zugangsdaten – E-Mail-Benachrichtigung deaktiviert');
  }
} catch (e) {
  console.log('📧 nodemailer nicht verfügbar:', e.message);
}

async function sendBenachrichtigung(betrieb) {
  if (!transporter) return;
  try {
    const html = `
      <h2>🏪 Neue Betriebs-Registrierung</h2>
      <table style="border-collapse:collapse;width:100%;max-width:500px">
        <tr><td style="padding:8px;border:1px solid #ddd;font-weight:700">Name</td><td style="padding:8px;border:1px solid #ddd">${betrieb.name}</td></tr>
        <tr><td style="padding:8px;border:1px solid #ddd;font-weight:700">Typ</td><td style="padding:8px;border:1px solid #ddd">${betrieb.typ}</td></tr>
        <tr><td style="padding:8px;border:1px solid #ddd;font-weight:700">Ort</td><td style="padding:8px;border:1px solid #ddd">${betrieb.ort}</td></tr>
        <tr><td style="padding:8px;border:1px solid #ddd;font-weight:700">E-Mail</td><td style="padding:8px;border:1px solid #ddd">${betrieb.email || '-'}</td></tr>
        <tr><td style="padding:8px;border:1px solid #ddd;font-weight:700">Beschreibung</td><td style="padding:8px;border:1px solid #ddd">${(betrieb.beschreibung || '-').substring(0, 200)}</td></tr>
      </table>
      <p><a href="https://webhook.tiroltourismus.com/api/betriebe/pending/${betrieb.slug}" style="background:#FF1493;color:#fff;padding:10px 20px;border-radius:4px;text-decoration:none">Eintrag prüfen</a></p>
    `;
    await transporter.sendMail({
      from: process.env.SMTP_FROM || '"Tirol Tourismus" <noreply@tiroltourismus.com>',
      to: process.env.NOTIFY_EMAIL || 'office@tiroltourismus.com',
      subject: `🏪 Neue Betriebs-Registrierung: ${betrieb.name}`,
      html,
    });
    console.log(`📧 Benachrichtigung gesendet für: ${betrieb.name}`);
  } catch (e) {
    console.error('📧 Fehler beim Senden der Benachrichtigung:', e.message);
  }
}

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

// Map LemonSqueezy variant IDs to tier names
const VARIANT_TIER_MAP = {
  1671559: 'silver',     // Silver — 19€/month
  1671576: 'gold',       // Gold — 49€/month
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

// ── Betrieb-Registrierung API ──

const BETRIEB_DIR = path.resolve(__dirname, '..', 'src', 'data', 'pending');
if (!fs.existsSync(BETRIEB_DIR)) {
  fs.mkdirSync(BETRIEB_DIR, { recursive: true });
}

// Category mapping: typ → data directory
const CATEGORY_MAP = {
  'Unterkunft (Hotel, Pension, Ferienwohnung)': 'unterkuenfte',
  'Gastronomie (Restaurant, Café, Bar)': 'gastro',
  'Erlebnisanbieter': 'erlebnisse',
  'Sport & Aktiv': 'erlebnisse',
  'Kultur & Sehenswürdigkeit': 'sehenswuerdigkeiten',
};
const FALLBACK_CATEGORY = 'diverses'; // für Einzelhandel, Dienstleistung, Sonstiges

/** Slug aus Namen generieren */
function makeBetriebSlug(name) {
  return name
    .toLowerCase()
    .replace(/[ä]/g, 'ae').replace(/[ö]/g, 'oe').replace(/[ü]/g, 'ue').replace(/[ß]/g, 'ss')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60) || `betrieb-${Date.now()}`;
}

app.post('/api/betrieb-register', express.json(), (req, res) => {
  const { name, typ, ort, beschreibung, email, telefon, bildUrl } = req.body;

  // Validation
  const errors = {};
  if (!name || name.trim().length < 2) errors.name = 'Name muss mindestens 2 Zeichen lang sein.';
  if (!typ) errors.typ = 'Bitte wähle eine Kategorie.';
  if (!ort || ort.trim().length < 2) errors.ort = 'Bitte gib den Ort an.';
  if (!beschreibung || beschreibung.trim().length < 10) errors.beschreibung = 'Beschreibung muss mindestens 10 Zeichen lang sein.';
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = 'Bitte gib eine gültige E-Mail-Adresse ein.';

  if (Object.keys(errors).length > 0) {
    return res.status(422).json({ error: 'Validierung fehlgeschlagen', errors });
  }

  try {
    const slug = makeBetriebSlug(name);
    const entryDir = path.join(BETRIEB_DIR, slug);

    // Avoid overwriting an existing slug
    let finalSlug = slug;
    let counter = 0;
    while (fs.existsSync(path.join(BETRIEB_DIR, finalSlug))) {
      counter++;
      finalSlug = `${slug}-${counter}`;
    }

    const entryData = {
      slug: finalSlug,
      name: name.trim(),
      typ,
      ort: ort.trim(),
      beschreibung: beschreibung.trim(),
      kontakt: {
        email: email.trim(),
        telefon: (telefon || '').trim() || null,
      },
      bildUrl: (bildUrl || '').trim() || null,
      status: 'pending',
      tier: 'basic',
      erstelltAm: new Date().toISOString(),
    };

    const targetDir = path.join(BETRIEB_DIR, finalSlug);
    fs.mkdirSync(targetDir, { recursive: true });
    fs.writeFileSync(path.join(targetDir, 'index.json'), JSON.stringify(entryData, null, 2), 'utf-8');

    console.log(`🏪 Betrieb registriert: ${entryData.name} → ${finalSlug}`);
    res.status(201).json({
      ok: true,
      slug: finalSlug,
      name: entryData.name,
      pfad: `/fuer-betriebe/pending/${finalSlug}/`,
    });
    
    // E-Mail-Benachrichtigung an Admin (fehlertolerant)
    sendBenachrichtigung(entryData).catch(() => {});
  } catch (e) {
    console.error('❌ Fehler bei Betrieb-Registrierung:', e.message);
    res.status(500).json({ error: 'Interner Serverfehler' });
  }
});

// GET /api/betriebe/pending — list all pending entries (for admin dashboard)
app.get('/api/betriebe/pending', (req, res) => {
  try {
    if (!fs.existsSync(BETRIEB_DIR)) return res.json([]);
    const entries = fs.readdirSync(BETRIEB_DIR).filter(f => {
      const indexPath = path.join(BETRIEB_DIR, f, 'index.json');
      return fs.existsSync(indexPath);
    }).map(f => {
      const data = JSON.parse(fs.readFileSync(path.join(BETRIEB_DIR, f, 'index.json'), 'utf-8'));
      return { slug: f, ...data };
    }).filter(e => e.status === 'pending');
    res.json(entries);
  } catch (e) {
    console.error('❌ Fehler beim Lesen der pending entries:', e.message);
    res.status(500).json({ error: 'Interner Serverfehler' });
  }
});

// GET /api/betriebe/pending/:slug — get a single pending entry
app.get('/api/betriebe/pending/:slug', (req, res) => {
  try {
    const filePath = path.join(BETRIEB_DIR, req.params.slug, 'index.json');
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: 'Eintrag nicht gefunden' });
    }
    res.json(JSON.parse(fs.readFileSync(filePath, 'utf-8')));
  } catch (e) {
    res.status(500).json({ error: 'Interner Serverfehler' });
  }
});

// POST /api/betriebe/pending/:slug/approve — approve a pending entry
app.post('/api/betriebe/pending/:slug/approve', express.json(), (req, res) => {
  try {
    const filePath = path.join(BETRIEB_DIR, req.params.slug, 'index.json');
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: 'Eintrag nicht gefunden' });
    }
    const entry = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    entry.status = 'approved';
    entry.freigegebenAm = new Date().toISOString();
    fs.writeFileSync(filePath, JSON.stringify(entry, null, 2), 'utf-8');
    console.log(`✅ Betrieb freigegeben: ${entry.name} (${req.params.slug})`);
    res.json({ ok: true, slug: req.params.slug });
  } catch (e) {
    res.status(500).json({ error: 'Interner Serverfehler' });
  }
});

// POST /api/betriebe/pending/:slug/reject — reject a pending entry
app.post('/api/betriebe/pending/:slug/reject', express.json(), (req, res) => {
  try {
    const filePath = path.join(BETRIEB_DIR, req.params.slug, 'index.json');
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: 'Eintrag nicht gefunden' });
    }
    const entry = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    entry.status = 'rejected';
    entry.abgelehntAm = new Date().toISOString();
    entry.ablehnungsGrund = req.body.grund || '';
    fs.writeFileSync(filePath, JSON.stringify(entry, null, 2), 'utf-8');
    console.log(`❌ Betrieb abgelehnt: ${entry.name} (${req.params.slug})`);
    res.json({ ok: true, slug: req.params.slug });
  } catch (e) {
    res.status(500).json({ error: 'Interner Serverfehler' });
  }
});

// POST /api/betriebe/pending/:slug/publish — approve + publish entry to its category
app.post('/api/betriebe/pending/:slug/publish', express.json(), (req, res) => {
  try {
    const filePath = path.join(BETRIEB_DIR, req.params.slug, 'index.json');
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: 'Eintrag nicht gefunden' });
    }
    const entry = JSON.parse(fs.readFileSync(filePath, 'utf-8'));

    // Determine target category
    const category = CATEGORY_MAP[entry.typ] || FALLBACK_CATEGORY;
    const dataDir = path.resolve(__dirname, '..', 'src', 'data', category);
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }

    // Avoid slug collisions
    let finalSlug = entry.slug;
    let counter = 0;
    while (fs.existsSync(path.join(dataDir, finalSlug))) {
      counter++;
      finalSlug = `${entry.slug}-${counter}`;
    }

    // Build published entry matching the site's index.json schema
    const publishedEntry = {
      slug: finalSlug,
      name: entry.name,
      ort: entry.ort || '',
      telefon: entry.kontakt?.telefon || null,
      email: entry.kontakt?.email || null,
      beschreibung: entry.beschreibung ? `<p>${entry.beschreibung.replace(/\n/g, '</p><p>')}</p>` : '',
      bilder: entry.bildUrl ? [{ url: entry.bildUrl }] : [],
      tier: 'basic',
      status: 'published',
      erstelltAm: entry.erstelltAm || new Date().toISOString(),
      // Category-specific fields
      ...(category === 'unterkuenfte' ? {
        typ: 'ferienwohnung',
        sterne: null,
        preis_ab: null,
        region: '',
        plz: '',
        adresse: '',
        webseite: null,
        ausstattung: [],
        tags: [],
        koordinaten: { lat: '', lng: '' },
        hero_bild: null,
      } : {}),
      ...(category === 'gastro' ? {
        region: '',
        kategorie: 'restaurant',
        kurzbeschreibung: entry.beschreibung ? entry.beschreibung.substring(0, 120) : '',
        emoji: '🍽️',
        farbe: '#E53935',
        adresse: '',
        preis: '€',
        tags: [],
        bilder: [],
        hero_bild: null,
        koordinaten: { lat: '', lng: '' },
      } : {}),
      ...(category === 'erlebnisse' ? {
        region: '',
        kategorie: 'aktiv',
        kurzbeschreibung: entry.beschreibung ? entry.beschreibung.substring(0, 120) : '',
        emoji: '🎯',
        dauer: '',
        preis_ab: null,
        tags: [],
        bilder: [],
        hero_bild: null,
        koordinaten: { lat: '', lng: '' },
      } : {}),
      ...(category === 'sehenswuerdigkeiten' ? {
        region: '',
        kategorie: 'natur',
        kurzbeschreibung: entry.beschreibung ? entry.beschreibung.substring(0, 120) : '',
        emoji: '🏛️',
        adresse: '',
        preis: '',
        oeffnungszeiten: '',
        tags: [],
        bilder: [],
        hero_bild: null,
        koordinaten: { lat: '', lng: '' },
      } : {}),
      ...(category === 'diverses' ? {
        region: '',
        kurzbeschreibung: entry.beschreibung ? entry.beschreibung.substring(0, 120) : '',
        tags: [],
        bilder: [],
        hero_bild: null,
      } : {}),
    };

    // Write to target directory
    const targetDir = path.join(dataDir, finalSlug);
    fs.mkdirSync(targetDir, { recursive: true });
    fs.writeFileSync(path.join(targetDir, 'index.json'), JSON.stringify(publishedEntry, null, 2), 'utf-8');

    // Mark pending as published
    entry.status = 'published';
    entry.publishedSlug = finalSlug;
    entry.publishedCategory = category;
    entry.freigegebenAm = new Date().toISOString();
    fs.writeFileSync(filePath, JSON.stringify(entry, null, 2), 'utf-8');

    console.log(`📰 Betrieb veröffentlicht: ${entry.name} → ${category}/${finalSlug}`);
    res.json({
      ok: true,
      slug: finalSlug,
      category,
      pfad: `/${category}/${finalSlug}/`,
      name: entry.name,
    });
  } catch (e) {
    console.error('❌ Fehler bei Veröffentlichung:', e.message);
    res.status(500).json({ error: 'Interner Serverfehler' });
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
  console.log(`   Betrieb-Registrierung API: http://localhost:${PORT}/api/betrieb-register`);
  console.log(`   Pending entries: ${BETRIEB_DIR}`);
  console.log('');
});
