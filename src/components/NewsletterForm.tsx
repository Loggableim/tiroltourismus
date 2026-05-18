/**
 * NewsletterForm.tsx — React newsletter signup component
 *
 * Uses: Web3Forms API (same backend as ContactForm).
 * Fields: Vorname, Email + DSGVO consent.
 * States: idle → loading → success / error
 *
 * Double Opt-in: Web3Forms supports "Autoresponder" on paid plans.
 * Configure in the Web3Forms dashboard → Email Settings → Autoresponder
 * to send a confirmation email after subscription.
 *
 * Before use: replace the access_key below with your Web3Forms key.
 * Sign up at https://web3forms.com/ to get one (free tier: 250/mo).
 */

import { useState, type FormEvent } from 'react';

/* 🔑 Replace with your actual Web3Forms access_key */
const ACCESS_KEY = 'YOUR_ACCESS_KEY_HERE';

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

  /* ── Submit ── */
  async function handleSubmit(ev: FormEvent) {
    ev.preventDefault();
    if (!validate()) return;
    if (ACCESS_KEY === 'YOUR_ACCESS_KEY_HERE') {
      setErrorMsg(
        'Das Newsletter-Formular ist noch nicht konfiguriert. Bitte setze einen Web3Forms Access Key ein.'
      );
      setState('error');
      return;
    }

    setState('loading');
    setErrorMsg('');

    try {
      const res = await fetch(WEB3FORMS_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          access_key: ACCESS_KEY,
          name: form.name.trim(),
          email: form.email.trim(),
          subject: '📬 Newsletter-Anmeldung – tiroltourismus.com',
          message: `Neue Newsletter-Anmeldung\n\nName: ${form.name.trim()}\nE-Mail: ${form.email.trim()}\nDSGVO zugestimmt: Ja\n\n(Der Empfänger muss in Web3Forms unter "Email Settings" → "Autoresponder" eine Bestätigungsmail konfigurieren.)`,
          botcheck: '',
        }),
      });

      if (res.ok) {
        setState('success');
        setForm({ name: '', email: '', consent: false });
        setErrors({});
      } else {
        const data = await res.json().catch(() => null);
        setErrorMsg(
          data?.message || 'Fehler bei der Anmeldung. Bitte versuche es später erneut.'
        );
        setState('error');
      }
    } catch {
      setErrorMsg('Netzwerkfehler. Bitte prüfe deine Internetverbindung.');
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
              an <strong>{form.email}</strong> gesendet. Bitte klicke den Link darin,
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
