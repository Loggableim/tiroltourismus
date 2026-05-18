/**
 * BetriebRegistrationForm.tsx — React self-registration form for businesses
 *
 * Betriebe können sich selbst eintragen. Daten werden in localStorage
 * unter 'tirol_pending_betriebe' gespeichert (Admin-Freigabe).
 *
 * Uses: client:load in Astro pages.
 * Fields: Name, Typ, Ort, Beschreibung, Kontakt, Bilder-URL
 * States: idle → loading → success / error
 */

import { useState, type FormEvent } from 'react';

/* ── Types ── */
type FormState = 'idle' | 'loading' | 'success' | 'error';

interface FormData {
  name: string;
  typ: string;
  ort: string;
  beschreibung: string;
  email: string;
  telefon: string;
  bildUrl: string;
  serverSlug?: string;
}

interface FormErrors {
  name?: string;
  typ?: string;
  ort?: string;
  beschreibung?: string;
  email?: string;
}

const BETRIEB_TYPEN = [
  'Unterkunft (Hotel, Pension, Ferienwohnung)',
  'Gastronomie (Restaurant, Café, Bar)',
  'Erlebnisanbieter',
  'Sport & Aktiv',
  'Kultur & Sehenswürdigkeit',
  'Einzelhandel',
  'Dienstleistung',
  'Sonstiges',
];

const STORAGE_KEY = 'tirol_pending_betriebe';
/* Server-API-Endpoint: in dev lokal, in prod über den Webhook-Server */
function getApiUrl() {
  return typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:3456/api/betrieb-register'
    : 'https://webhook.tiroltourismus.com/api/betrieb-register';
}

/* ── Helpers ── */
/** Einen lesbaren Slug aus dem Namen generieren */
function makeSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[ä]/g, 'ae')
    .replace(/[ö]/g, 'oe')
    .replace(/[ü]/g, 'ue')
    .replace(/[ß]/g, 'ss')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60);
}

/** Alle pending entries aus localStorage lesen */
function loadPending(): FormData[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

/** Einen neuen pending entry speichern */
function savePending(entry: FormData) {
  const existing = loadPending();
  existing.push(entry);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(existing));
}

/* ── Component ── */
export default function BetriebRegistrationForm() {
  const [form, setForm] = useState<FormData>({
    name: '',
    typ: '',
    ort: '',
    beschreibung: '',
    email: '',
    telefon: '',
    bildUrl: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [state, setState] = useState<FormState>('idle');
  const [errorMsg, setErrorMsg] = useState('');
  const [savedEntry, setSavedEntry] = useState<FormData | null>(null);

  /* ── Validation ── */
  function validate(): boolean {
    const e: FormErrors = {};

    if (!form.name.trim()) {
      e.name = 'Bitte gib den Betriebsnamen ein.';
    } else if (form.name.trim().length < 2) {
      e.name = 'Name muss mindestens 2 Zeichen lang sein.';
    }

    if (!form.typ) {
      e.typ = 'Bitte wähle eine Kategorie.';
    }

    if (!form.ort.trim()) {
      e.ort = 'Bitte gib den Ort an.';
    } else if (form.ort.trim().length < 2) {
      e.ort = 'Bitte gib einen gültigen Ort ein.';
    }

    if (!form.beschreibung.trim()) {
      e.beschreibung = 'Bitte schreib eine kurze Beschreibung.';
    } else if (form.beschreibung.trim().length < 10) {
      e.beschreibung = 'Beschreibung muss mindestens 10 Zeichen lang sein.';
    }

    if (!form.email.trim()) {
      e.email = 'Bitte gib deine E-Mail-Adresse ein.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
      e.email = 'Bitte gib eine gültige E-Mail-Adresse ein.';
    }

    setErrors(e);
    return Object.keys(e).length === 0;
  }

  /* ── Submit ── */
  async function handleSubmit(ev: FormEvent) {
    ev.preventDefault();
    if (!validate()) return;

    setState('loading');
    setErrorMsg('');

    try {
      const entry: FormData = {
        name: form.name.trim(),
        typ: form.typ,
        ort: form.ort.trim(),
        beschreibung: form.beschreibung.trim(),
        email: form.email.trim(),
        telefon: form.telefon.trim(),
        bildUrl: form.bildUrl.trim(),
      };

      // 1. Immer in localStorage speichern (Offline-Fallback + Admin-Dashboard)
      savePending(entry);

      // 2. Optional an Server senden (falls verfügbar)
      let serverSlug: string | undefined;
      try {
        const resp = await fetch(getApiUrl(), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(entry),
        });
        if (resp.ok) {
          const data = await resp.json();
          serverSlug = data.slug;
          console.log(`✅ Betrieb auf Server registriert: ${serverSlug}`);
        } else {
          const errData = await resp.json();
          console.warn('⚠️ Server-Registrierung fehlgeschlagen:', errData.error || resp.status);
        }
      } catch (netErr) {
        // Server nicht erreichbar → nur localStorage (kein Fehler für User)
        console.warn('⚠️ Server nicht erreichbar, nur lokal gespeichert');
      }

      setSavedEntry({ ...entry, serverSlug });
      setState('success');
      setForm({
        name: '',
        typ: '',
        ort: '',
        beschreibung: '',
        email: '',
        telefon: '',
        bildUrl: '',
      });
      setErrors({});
    } catch (err) {
      setErrorMsg(
        'Fehler beim Speichern. Bitte versuche es später erneut.'
      );
      setState('error');
    }
  }

  /* ── Helper: set a field ── */
  function set(field: keyof FormData, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  }

  /* ── Build JSON preview ── */
  function buildJSONPreview(data: FormData): string {
    const slug = makeSlug(data.name);
    const json = {
      slug,
      name: data.name,
      typ: data.typ,
      ort: data.ort,
      beschreibung: data.beschreibung,
      kontakt: {
        email: data.email,
        telefon: data.telefon || null,
      },
      bildUrl: data.bildUrl || null,
      status: 'pending',
      erstelltAm: new Date().toISOString(),
    };
    return JSON.stringify(json, null, 2);
  }

  /* ── Render ── */
  return (
    <form className="br-form" onSubmit={handleSubmit} noValidate>
      {/* ── SUCCESS STATE ── */}
      {state === 'success' && savedEntry && (
        <div className="br-success" role="status">
          <div className="br-success-icon">✅</div>
          <h3 className="br-success-title">Eintrag erfolgreich!</h3>
          <p className="br-success-text">
            Vielen Dank! Dein Eintrag für <strong>{savedEntry.name}</strong> wurde
            übermittelt und wird von unserem Team geprüft. Du erhältst in Kürze
            eine Bestätigung per E-Mail.
          </p>
          {savedEntry.serverSlug && (
            <p className="br-success-text" style={{ fontSize: '12px', color: 'var(--green)' }}>
              ✅ Auch auf dem Server gespeichert (Slug: {savedEntry.serverSlug})
            </p>
          )}

          <div className="br-success-json">
            <strong>📄 JSON-Vorschau (wird an Admin gesendet):</strong>
            <pre className="br-json-preview">{buildJSONPreview(savedEntry)}</pre>
            <p className="br-success-hint">
              Speicherort (Server): <code>src/data/pending/{makeSlug(savedEntry.name)}/index.json</code>
            </p>
          </div>

          <button
            type="button"
            className="btn btn-pink"
            onClick={() => {
              setState('idle');
              setSavedEntry(null);
            }}
          >
            Weiteren Betrieb eintragen →
          </button>
        </div>
      )}

      {/* ── ERROR STATE ── */}
      {state === 'error' && (
        <div className="br-state br-error" role="alert">
          <span className="br-state-icon">✕</span>
          <div>
            <strong>Fehler beim Speichern</strong>
            <p>{errorMsg}</p>
          </div>
        </div>
      )}

      {/* ── FORM FIELDS (hidden on success) ── */}
      <div className={state === 'success' ? 'br-fields-hidden' : 'br-fields'}>
        {/* Name */}
        <label className="br-field">
          <span className="br-label">
            Name des Betriebs <span className="br-required">*</span>
          </span>
          <input
            type="text"
            className={`br-input${errors.name ? ' br-input-error' : ''}`}
            placeholder="z.B. Gasthof zur Post"
            value={form.name}
            onChange={(e) => set('name', e.target.value)}
            disabled={state === 'loading'}
            autoComplete="organization"
          />
          {errors.name && <span className="br-err">{errors.name}</span>}
        </label>

        {/* Typ */}
        <label className="br-field">
          <span className="br-label">
            Kategorie <span className="br-required">*</span>
          </span>
          <select
            className={`br-input br-select${errors.typ ? ' br-input-error' : ''}`}
            value={form.typ}
            onChange={(e) => set('typ', e.target.value)}
            disabled={state === 'loading'}
          >
            <option value="">— Bitte wählen —</option>
            {BETRIEB_TYPEN.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          {errors.typ && <span className="br-err">{errors.typ}</span>}
        </label>

        {/* Ort */}
        <label className="br-field">
          <span className="br-label">
            Ort <span className="br-required">*</span>
          </span>
          <input
            type="text"
            className={`br-input${errors.ort ? ' br-input-error' : ''}`}
            placeholder="z.B. Innsbruck, Sölden, Mayrhofen …"
            value={form.ort}
            onChange={(e) => set('ort', e.target.value)}
            disabled={state === 'loading'}
            autoComplete="address-level2"
          />
          {errors.ort && <span className="br-err">{errors.ort}</span>}
        </label>

        {/* Beschreibung */}
        <label className="br-field">
          <span className="br-label">
            Beschreibung <span className="br-required">*</span>
          </span>
          <textarea
            rows={5}
            className={`br-input br-textarea${errors.beschreibung ? ' br-input-error' : ''}`}
            placeholder="Kurze Vorstellung Ihres Betriebs – was macht Sie besonders? …"
            value={form.beschreibung}
            onChange={(e) => set('beschreibung', e.target.value)}
            disabled={state === 'loading'}
          />
          {errors.beschreibung && (
            <span className="br-err">{errors.beschreibung}</span>
          )}
        </label>

        {/* Email */}
        <label className="br-field">
          <span className="br-label">
            E-Mail (Kontakt) <span className="br-required">*</span>
          </span>
          <input
            type="email"
            className={`br-input${errors.email ? ' br-input-error' : ''}`}
            placeholder="deine@email.at"
            value={form.email}
            onChange={(e) => set('email', e.target.value)}
            disabled={state === 'loading'}
            autoComplete="email"
          />
          {errors.email && <span className="br-err">{errors.email}</span>}
        </label>

        {/* Telefon */}
        <label className="br-field">
          <span className="br-label">Telefon (optional)</span>
          <input
            type="tel"
            className="br-input"
            placeholder="+43 512 1234567"
            value={form.telefon}
            onChange={(e) => set('telefon', e.target.value)}
            disabled={state === 'loading'}
            autoComplete="tel"
          />
        </label>

        {/* Bilder-URL */}
        <label className="br-field">
          <span className="br-label">Bilder-URL (optional)</span>
          <input
            type="url"
            className="br-input"
            placeholder="https://example.com/mein-betrieb.jpg"
            value={form.bildUrl}
            onChange={(e) => set('bildUrl', e.target.value)}
            disabled={state === 'loading'}
          />
          <span className="br-hint">
            Link zu einem Foto Ihres Betriebs (oder Google Maps / Instagram)
          </span>
        </label>

        {/* Submit */}
        <button
          type="submit"
          className="btn btn-pink br-submit"
          disabled={state === 'loading'}
        >
          {state === 'loading' ? (
            <>
              <span className="br-spinner" aria-hidden="true" />
              Wird gespeichert …
            </>
          ) : (
            'Kostenlos eintragen ✨'
          )}
        </button>

        <p className="br-legal">
          Mit dem Absenden stimmst du zu, dass deine Daten zum Zweck der
          Eintragung verarbeitet werden. Deine Daten werden nicht an Dritte
          weitergegeben. <a href="/datenschutz/">Datenschutzerklärung</a>
        </p>
      </div>
    </form>
  );
}
