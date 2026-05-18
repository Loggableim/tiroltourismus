/**
 * NewsletterForm.tsx — React newsletter signup component
 *
 * Architecture:
 *   [Form] → POST /api/newsletter → [webhook server (Express)] → MailerLite API
 *
 * The webhook server proxies subscriptions to MailerLite. The API key lives
 * server-side in webhook/.env (MAILERLITE_API_KEY), never on the client.
 *
 * Fallback: Web3Forms (if webhook server URL is not configured).
 *
 * Setup:
 * 1. Deploy the webhook server (webhook/server.js)
 * 2. Set NEWSLETTER_API_URL below to your deployed server URL
 * 3. Verify in MailerLite dashboard: Group "Newsletter" → active subscribers
 */

import { useState, type FormEvent } from 'react';

/* ══ Newsletter API (backed by webhook server → MailerLite) ══
 * The webhook server proxies to MailerLite API (no key exposed on client).
 * Change NEWSLETTER_API_URL to your deployed webhook server URL.
 * Example: 'https://webhook.tiroltourismus.com/api/newsletter'
 */
const NEWSLETTER_API_URL = 'https://webhook.tiroltourismus.com/api/newsletter';

/* ══ Web3Forms Fallback (existing) ══
 * Used when webhook server is not yet deployed.
 * Sign up at https://web3forms.com/ (free tier: 250/mo).
 */
const WEB3FORMS_ACCESS_KEY = 'YOUR_ACCESS_KEY_HERE';
const WEB3FORMS_URL = 'https://api.web3forms.com/submit';

type FormState = 'idle' | 'loading' | 'success' | 'error';

interface NewsletterFormData {
  name: string;
  email: string;
  consent: boolean;
}

interface FormErrors {
  name?: string;
  email?: string;
  consent?: string;
}

interface NewsletterFormProps {
  /** Compact mode for footer embedding (smaller layout) */
  compact?: boolean;
  /** Optional CSS class override */
  className?: string;
}

export default function NewsletterForm({ compact = false }: NewsletterFormProps) {
  const [form, setForm] = useState<NewsletterFormData>({
    name: '',
    email: '',
    consent: false,
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [state, setState] = useState<FormState>('idle');
  const [errorMsg, setErrorMsg] = useState('');
  const [submittedEmail, setSubmittedEmail] = useState('');

  /* ── Validation ── */
  function validate(): boolean {
    const e: FormErrors = {};

    if (!form.name.trim()) {
      e.name = 'Bitte gib deinen Vornamen ein.';
    } else if (form.name.trim().length < 2) {
      e.name = 'Name muss mindestens 2 Zeichen lang sein.';
    }

    if (!form.email.trim()) {
      e.email = 'Bitte gib deine E-Mail-Adresse ein.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
      e.email = 'Bitte gib eine gültige E-Mail-Adresse ein.';
    }

    if (!form.consent) {
      e.consent = 'Bitte stimme der Datenschutzerklärung zu.';
    }

    setErrors(e);
    return Object.keys(e).length === 0;
  }

  /* ── Submit to Newsletter API (webhook server → MailerLite) ── */
  async function submitToApi(data: NewsletterFormData): Promise<boolean> {
    if (!NEWSLETTER_API_URL) return false;

    try {
      const res = await fetch(NEWSLETTER_API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: data.email.trim(),
          name: data.name.trim(),
        }),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  /* ── Submit to Web3Forms (fallback) ── */
  async function submitToWeb3Forms(data: NewsletterFormData): Promise<boolean> {
    if (WEB3FORMS_ACCESS_KEY === 'YOUR_ACCESS_KEY_HERE') {
      setErrorMsg(
        'Das Newsletter-Formular ist noch nicht konfiguriert. Bitte setze einen MailerLite-Form-Link oder Web3Forms Access Key ein.'
      );
      setState('error');
      return false;
    }

    try {
      const res = await fetch(WEB3FORMS_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          access_key: WEB3FORMS_ACCESS_KEY,
          name: data.name.trim(),
          email: data.email.trim(),
          subject: '📬 Newsletter-Anmeldung – tiroltourismus.com',
          message: `Neue Newsletter-Anmeldung\n\nName: ${data.name.trim()}\nE-Mail: ${data.email.trim()}\nDSGVO zugestimmt: Ja`,
          botcheck: '',
        }),
      });

      return res.ok;
    } catch {
      return false;
    }
  }

  /* ── Submit ── */
  async function handleSubmit(ev: FormEvent) {
    ev.preventDefault();
    if (!validate()) return;

    setState('loading');
    setErrorMsg('');
    setSubmittedEmail(form.email.trim());

    // Try Newsletter API (webhook server → MailerLite), fall back to Web3Forms
    const apiOk = await submitToApi(form);
    if (apiOk) {
      setState('success');
      setForm({ name: '', email: '', consent: false });
      setErrors({});
      return;
    }

    // Fallback
    const web3Ok = await submitToWeb3Forms(form);
    if (web3Ok) {
      setState('success');
      setForm({ name: '', email: '', consent: false });
      setErrors({});
    } else if (state !== 'error') {
      // Only set error if not already set by submitToWeb3Forms
      setErrorMsg('Fehler bei der Anmeldung. Bitte versuche es später erneut.');
      setState('error');
    }
  }

  /* ── Helper ── */
  function set(field: keyof Omit<NewsletterFormData, 'consent'>, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  }

  /* ── Render ── */
  const wrapperClass = compact ? 'nf-compact' : 'nf-full';

  return (
    <form
      className={`nf-form ${wrapperClass}`}
      onSubmit={handleSubmit}
      noValidate
    >
      {/* Hidden anti-bot field */}
      <input
        type="checkbox"
        name="botcheck"
        className="nf-hidden"
        tabIndex={-1}
        autoComplete="off"
      />

      {/* ── SUCCESS STATE ── */}
      {state === 'success' && (
        <div className="nf-state nf-success" role="status">
          <span className="nf-state-icon">✓</span>
          <div>
            <strong>Fast geschafft!</strong>
            <p>
              Vielen Dank für deine Anmeldung! Wir haben dir eine Bestätigungs-E-Mail
              an <strong>{submittedEmail}</strong> gesendet. Bitte klicke den Link darin,
              um dein Abonnement zu aktivieren (Double Opt-in).
            </p>
          </div>
        </div>
      )}

      {/* ── ERROR STATE ── */}
      {state === 'error' && (
        <div className="nf-state nf-error" role="alert">
          <span className="nf-state-icon">✕</span>
          <div>
            <strong>Fehler bei der Anmeldung</strong>
            <p>{errorMsg}</p>
          </div>
        </div>
      )}

      {/* ── FORM FIELDS (hidden on success) ── */}
      <div className={state === 'success' ? 'nf-fields-hidden' : 'nf-fields'}>
        {/* Name */}
        <label className="nf-field">
          <span className="nf-label">
            {compact ? 'Vorname' : 'Vorname *'}
          </span>
          <input
            type="text"
            className={`nf-input${errors.name ? ' nf-input-error' : ''}`}
            placeholder="Dein Vorname"
            value={form.name}
            onChange={(e) => set('name', e.target.value)}
            disabled={state === 'loading'}
            autoComplete="given-name"
          />
          {errors.name && <span className="nf-err">{errors.name}</span>}
        </label>

        {/* Email */}
        <label className="nf-field">
          <span className="nf-label">E-Mail *</span>
          <input
            type="email"
            className={`nf-input${errors.email ? ' nf-input-error' : ''}`}
            placeholder="deine@email.at"
            value={form.email}
            onChange={(e) => set('email', e.target.value)}
            disabled={state === 'loading'}
            autoComplete="email"
          />
          {errors.email && <span className="nf-err">{errors.email}</span>}
        </label>

        {/* DSGVO Consent */}
        <label className={`nf-field nf-checkbox${errors.consent ? ' nf-checkbox-error' : ''}`}>
          <input
            type="checkbox"
            checked={form.consent}
            onChange={(e) => {
              setForm((prev) => ({ ...prev, consent: e.target.checked }));
              if (errors.consent) {
                setErrors((prev) => ({ ...prev, consent: undefined }));
              }
            }}
            disabled={state === 'loading'}
          />
          <span className="nf-checkbox-label">
            Ich habe die{' '}
            <a href="/datenschutz/" target="_blank" rel="noopener noreferrer">
              Datenschutzerklärung
            </a>{' '}
            gelesen und stimme der Verarbeitung meiner Daten zum Zweck des
            Newsletter-Versands zu. *
          </span>
        </label>
        {errors.consent && <span className="nf-err">{errors.consent}</span>}

        {/* Submit */}
        <button
          type="submit"
          className={compact ? 'btn btn-pink nf-submit nf-submit-compact' : 'btn btn-pink nf-submit'}
          disabled={state === 'loading'}
        >
          {state === 'loading' ? (
            <>
              <span className="nf-spinner" aria-hidden="true" />
              Wird angemeldet …
            </>
          ) : compact ? (
            'Anmelden ✈️'
          ) : (
            'Kostenlos anmelden ✈️'
          )}
        </button>

        {!compact && (
          <p className="nf-dsgvo-note">
            Mit dem Absenden des Formulars erklärst du dich damit einverstanden, dass
            wir deine Daten zum Zweck des Newsletter-Versands verarbeiten. Du kannst
            dich jederzeit über den Link in unseren E-Mails abmelden.
          </p>
        )}
      </div>
    </form>
  );
}
