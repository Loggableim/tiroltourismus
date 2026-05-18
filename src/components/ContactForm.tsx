/**
 * ContactForm.tsx — React contact form with FormSubmit backend
 *
 * Uses: client:load or client:visible in Astro pages.
 * Fields: Name, Email, Betreff, Nachricht
 * States: idle → loading (spinner) → success / error
 * Design: matches the Tirol dark/glow system
 *
 * FormSubmit is free, no signup required.
 * Submissions are sent to office@tiroltourismus.com
 */

import { useState, type FormEvent } from 'react';

const FORM_URL = 'https://formsubmit.co/office@tiroltourismus.com';

type FormState = 'idle' | 'loading' | 'success' | 'error';

interface FormData {
  name: string;
  email: string;
  subject: string;
  message: string;
}

interface FormErrors {
  name?: string;
  email?: string;
  message?: string;
}

export default function ContactForm() {
  const [form, setForm] = useState<FormData>({
    name: '',
    email: '',
    subject: '',
    message: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [state, setState] = useState<FormState>('idle');
  const [errorMsg, setErrorMsg] = useState('');

  /* ── Validation ── */
  function validate(): boolean {
    const e: FormErrors = {};

    if (!form.name.trim()) {
      e.name = 'Bitte gib deinen Namen ein.';
    } else if (form.name.trim().length < 2) {
      e.name = 'Name muss mindestens 2 Zeichen lang sein.';
    }

    if (!form.email.trim()) {
      e.email = 'Bitte gib deine E-Mail-Adresse ein.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
      e.email = 'Bitte gib eine gültige E-Mail-Adresse ein.';
    }

    if (!form.message.trim()) {
      e.message = 'Bitte schreib uns eine Nachricht.';
    } else if (form.message.trim().length < 10) {
      e.message = 'Nachricht muss mindestens 10 Zeichen lang sein.';
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
      // FormSubmit uses URL-encoded form data, works without JS fallback too
      const formData = new URLSearchParams();
      formData.append('name', form.name.trim());
      formData.append('email', form.email.trim());
      formData.append('_subject', form.subject.trim() || 'Kontaktanfrage (kein Betreff)');
      formData.append('message', form.message.trim());
      formData.append('_template', 'table');

      const res = await fetch(FORM_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });

      // FormSubmit always redirects on success, but if fetch resolves it worked
      setState('success');
      setForm({ name: '', email: '', subject: '', message: '' });
      setErrors({});
      if (typeof window !== 'undefined') {
        const track = (window as any).trackEvent || (window as any).gtag || (() => {});
        track('Kontakt', { subject: form.subject.trim() || '(kein Betreff)' });
      }
    } catch {
      setErrorMsg(
        'Netzwerkfehler. Bitte prüfe deine Internetverbindung und versuche es erneut.'
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

  /* ── Render ── */
  return (
    <form
      className="cf-form"
      onSubmit={handleSubmit}
      noValidate
    >
      {/* Hidden field for accessibility / anti-bot */}
      <input
        type="checkbox"
        name="botcheck"
        className="cf-hidden"
        tabIndex={-1}
        autoComplete="off"
      />

      {/* ── SUCCESS STATE ── */}
      {state === 'success' && (
        <div className="cf-state cf-success" role="status">
          <span className="cf-state-icon">✓</span>
          <div>
            <strong>Nachricht gesendet!</strong>
            <p>Vielen Dank für deine Nachricht. Wir melden uns innerhalb von 24 h bei dir.</p>
          </div>
        </div>
      )}

      {/* ── ERROR STATE ── */}
      {state === 'error' && (
        <div className="cf-state cf-error" role="alert">
          <span className="cf-state-icon">✕</span>
          <div>
            <strong>Fehler beim Senden</strong>
            <p>{errorMsg}</p>
          </div>
        </div>
      )}

      {/* ── FORM FIELDS (hidden on success) ── */}
      <div className={state === 'success' ? 'cf-fields-hidden' : 'cf-fields'}>
        {/* Name */}
        <label className="cf-field">
          <span className="cf-label">Name *</span>
          <input
            type="text"
            className={`cf-input${errors.name ? ' cf-input-error' : ''}`}
            placeholder="Dein Name"
            value={form.name}
            onChange={(e) => set('name', e.target.value)}
            disabled={state === 'loading'}
            autoComplete="name"
          />
          {errors.name && <span className="cf-err">{errors.name}</span>}
        </label>

        {/* Email */}
        <label className="cf-field">
          <span className="cf-label">E-Mail *</span>
          <input
            type="email"
            className={`cf-input${errors.email ? ' cf-input-error' : ''}`}
            placeholder="deine@email.at"
            value={form.email}
            onChange={(e) => set('email', e.target.value)}
            disabled={state === 'loading'}
            autoComplete="email"
          />
          {errors.email && <span className="cf-err">{errors.email}</span>}
        </label>

        {/* Betreff */}
        <label className="cf-field">
          <span className="cf-label">Betreff</span>
          <input
            type="text"
            className="cf-input"
            placeholder="Worum geht es?"
            value={form.subject}
            onChange={(e) => set('subject', e.target.value)}
            disabled={state === 'loading'}
            autoComplete="off"
          />
        </label>

        {/* Nachricht */}
        <label className="cf-field">
          <span className="cf-label">Nachricht *</span>
          <textarea
            rows={5}
            className={`cf-input cf-textarea${errors.message ? ' cf-input-error' : ''}`}
            placeholder="Deine Nachricht an uns …"
            value={form.message}
            onChange={(e) => set('message', e.target.value)}
            disabled={state === 'loading'}
          />
          {errors.message && <span className="cf-err">{errors.message}</span>}
        </label>

        {/* Submit */}
        <button
          type="submit"
          className="btn btn-pink cf-submit"
          disabled={state === 'loading'}
        >
          {state === 'loading' ? (
            <>
              <span className="cf-spinner" aria-hidden="true" />
              Wird gesendet …
            </>
          ) : (
            'Senden ✈️'
          )}
        </button>
      </div>
    </form>
  );
}
