/**
 * NewsletterForm.tsx — React newsletter signup component
 *
 * Architecture:
 *   [Form] → POST /api/newsletter → [webhook server (Express)] → MailerLite API
 *
 * Design: Pink/Gold Duo, Dark-Glass, Tirol Design System.
 * API-Key liegt serverseitig in webhook/.env, nie im Client.
 *
 * Fallback: Web3Forms (wenn kein NEWSLETTER_API_URL konfiguriert).
 */

import { useState, type FormEvent } from 'react';

const NEWSLETTER_API_URL = 'https://webhook.tiroltourismus.com/api/newsletter';
const WEB3FORMS_ACCESS_KEY = 'YOUR_ACCESS_KEY_HERE';
const WEB3FORMS_URL = 'https://api.web3forms.com/submit';

type FormState = 'idle' | 'loading' | 'success' | 'error';

interface NewsletterFormProps {
  /** Compact mode for footer embedding */
  compact?: boolean;
}

export default function NewsletterForm({ compact = false }: NewsletterFormProps) {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [consent, setConsent] = useState(false);
  const [state, setState] = useState<FormState>('idle');
  const [errorMsg, setErrorMsg] = useState('');
  const [submittedEmail, setSubmittedEmail] = useState('');

  function validate(): boolean {
    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setErrorMsg('Bitte gib eine gültige E-Mail-Adresse ein.');
      return false;
    }
    if (!consent) {
      setErrorMsg('Bitte stimme der Datenschutzerklärung zu.');
      return false;
    }
    return true;
  }

  async function submitToApi(): Promise<boolean> {
    if (!NEWSLETTER_API_URL) return false;
    try {
      const res = await fetch(NEWSLETTER_API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), name: name.trim() }),
      });
      return res.ok;
    } catch { return false; }
  }

  async function submitToWeb3Forms(): Promise<boolean> {
    if (WEB3FORMS_ACCESS_KEY === 'YOUR_ACCESS_KEY_HERE') return false;
    try {
      const res = await fetch(WEB3FORMS_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          access_key: WEB3FORMS_ACCESS_KEY,
          email: email.trim(),
          name: name.trim(),
          subject: '📬 Newsletter – tiroltourismus.com',
          botcheck: '',
        }),
      });
      return res.ok;
    } catch { return false; }
  }

  async function handleSubmit(ev: FormEvent) {
    ev.preventDefault();
    setErrorMsg('');
    if (!validate()) { setState('error'); return; }

    setState('loading');
    setSubmittedEmail(email.trim());

    const apiOk = await submitToApi();
    if (apiOk) {
      setState('success');
      setEmail(''); setName(''); setConsent(false);
      return;
    }

    const web3Ok = await submitToWeb3Forms();
    if (web3Ok) {
      setState('success');
      setEmail(''); setName(''); setConsent(false);
    } else {
      setErrorMsg('Fehler bei der Anmeldung. Bitte versuche es später erneut.');
      setState('error');
    }
  }

  return (
    <>
      <style>{`
        .nl-root {
          --nl-bg: linear-gradient(135deg, rgba(255,20,147,.06), rgba(212,168,0,.06));
          --nl-border: 1px solid rgba(255,255,255,.08);
          --nl-radius: 16px;
          --nl-gap: 12px;
        }
        .nl-root.nl-compact {
          text-align: left;
          padding: 0;
        }
        .nl-root.nl-compact .nl-form-wrap {
          gap: 10px;
        }
        .nl-root.nl-compact .nl-row {
          display: flex;
          gap: 10px;
          align-items: stretch;
        }
        .nl-root.nl-compact .nl-input {
          flex: 1;
          padding: 11px 14px;
          border-radius: 999px;
          border: 1px solid rgba(255,255,255,.12);
          background: rgba(255,255,255,.06);
          color: var(--text, #F0EDEE);
          font-size: 12px;
          font-family: var(--font-body, 'Montserrat', sans-serif);
          backdrop-filter: blur(10px);
          transition: all .3s;
          min-width: 0;
        }
        .nl-root.nl-compact .nl-input::placeholder { color: rgba(255,255,255,.32); }
        .nl-root.nl-compact .nl-input:focus { border-color: var(--pink, #FF1493); background: rgba(255,255,255,.1); box-shadow: 0 0 0 3px rgba(255,20,147,.12); }
        .nl-root.nl-compact .nl-input.error { border-color: #ff4444; }

        .nl-submit {
          padding: 12px 24px;
          border-radius: 100px;
          border: none;
          background: linear-gradient(135deg, var(--pink, #FF1493), var(--pink-dark, #C0006E));
          color: #fff;
          font-size: 12px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: .5px;
          cursor: pointer;
          transition: all .3s cubic-bezier(.16,1,.3,1);
          white-space: nowrap;
          font-family: var(--font-body, 'Montserrat', sans-serif);
          display: inline-flex;
          align-items: center;
          gap: 6px;
          justify-content: center;
        }
        .nl-root.nl-compact .nl-submit {
          padding: 11px 16px;
          font-size: 11px;
          letter-spacing: .35px;
        }
        .nl-submit:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(255,20,147,.35); }
        .nl-submit:disabled { opacity: .5; cursor: not-allowed; transform: none; box-shadow: none; }
        .nl-submit.gold {
          background: linear-gradient(135deg, var(--gold, #D4A800), var(--gold-light, #FFD700));
          color: #1a1a1a;
        }
        .nl-submit.gold:hover { box-shadow: 0 6px 24px rgba(212,168,0,.35); }

        .nl-spinner {
          display: inline-block;
          width: 14px; height: 14px;
          border: 2px solid rgba(255,255,255,.3);
          border-top-color: #fff;
          border-radius: 50%;
          animation: nl-spin .6s linear infinite;
        }
        @keyframes nl-spin { to { transform: rotate(360deg); } }

        .nl-state {
          padding: 16px 20px;
          border-radius: 12px;
          font-size: 14px;
          line-height: 1.5;
          text-align: center;
          animation: nl-fadeIn .3s ease;
        }
        .nl-state.success {
          background: rgba(0,200,83,.12);
          border: 1px solid rgba(0,200,83,.25);
          color: #00E676;
        }
        .nl-state.error {
          background: rgba(255,68,68,.1);
          border: 1px solid rgba(255,68,68,.2);
          color: #FF6B6B;
        }
        .nl-state .nl-email {
          font-weight: 700;
          word-break: break-all;
        }
        .nl-state strong { display: block; margin-bottom: 4px; font-size: 15px; }
        .nl-state p { margin: 0; font-size: 13px; }

        .nl-checkbox {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          font-size: 11px;
          line-height: 1.5;
          color: rgba(255,255,255,.55);
          cursor: pointer;
        }
        .nl-checkbox input {
          margin-top: 2px;
          width: 16px; height: 16px;
          accent-color: var(--pink, #FF1493);
          cursor: pointer;
          flex-shrink: 0;
        }
        .nl-checkbox a {
          color: var(--gold-light, #FFD700);
          text-decoration: underline;
          text-underline-offset: 2px;
        }
        .nl-checkbox a:hover { color: var(--gold, #D4A800); }

        @keyframes nl-fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }

        /* ── Extra Name-Feld nur bei voller Version ── */
        .nl-name-row {
          display: flex;
          gap: 8px;
        }
        .nl-name-row .nl-input { flex: 1; }

        /* ── Full Hero Style ── */
        .nl-hero {
          position: relative;
          padding: 80px 0;
          text-align: center;
          overflow: hidden;
        }
        .nl-hero::before {
          content: '';
          position: absolute;
          inset: 0;
          background: linear-gradient(135deg, var(--pink, #FF1493), var(--pink-dark, #C0006E));
          opacity: .92;
          pointer-events: none;
        }
        .nl-hero::after {
          content: '';
          position: absolute;
          inset: 0;
          background-image: radial-gradient(circle, rgba(255,255,255,.06) 1.5px, transparent 1.5px);
          background-size: 20px 20px;
          pointer-events: none;
        }
        .nl-hero .nl-inner {
          position: relative;
          z-index: 1;
          max-width: 560px;
          margin: 0 auto;
        }
        .nl-hero h2 {
          font-family: var(--font-display, 'Bebas Neue', Impact, sans-serif);
          font-size: clamp(42px, 8vw, 90px);
          line-height: .9;
          letter-spacing: 2px;
          text-transform: uppercase;
          color: #fff;
          margin-bottom: 4px;
        }
        .nl-hero h2 .gold {
          background: linear-gradient(135deg, var(--gold-light, #FFD700), #fff);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .nl-hero p {
          font-size: 15px;
          color: rgba(255,255,255,.75);
          margin-bottom: 28px;
          line-height: 1.6;
        }
        .nl-hero .nl-form-wrap {
          max-width: 480px;
          margin: 0 auto;
        }
        .nl-hero .nl-row {
          background: rgba(255,255,255,.1);
          padding: 4px;
          border-radius: 100px;
          backdrop-filter: blur(12px);
          border: 1px solid rgba(255,255,255,.1);
        }
        .nl-hero .nl-input {
          background: transparent;
          border: none;
          color: #fff;
          padding: 14px 20px;
          font-size: 14px;
        }
        .nl-hero .nl-input::placeholder { color: rgba(255,255,255,.4); }
        .nl-hero .nl-submit {
          padding: 14px 28px;
          background: #fff;
          color: var(--pink-dark, #C0006E);
          font-size: 12px;
        }
        .nl-hero .nl-submit:hover { box-shadow: 0 8px 30px rgba(0,0,0,.3); }

        /* ── Compact Footer Style ── */
        .nl-compact .nl-row {
          display: flex;
          gap: 6px;
        }
        .nl-compact .nl-input {
          padding: 10px 16px;
          font-size: 12px;
        }
        .nl-compact .nl-submit {
          padding: 10px 18px;
          font-size: 11px;
        }

        @media (max-width: 500px) {
          .nl-row { flex-direction: column; }
          .nl-hero .nl-row { border-radius: 16px; padding: 8px; }
          .nl-name-row { flex-direction: column; }
        }
      `}</style>

      <div className={`nl-root ${compact ? 'nl-compact' : 'nl-hero'}`}>
        <div className={compact ? '' : 'nl-inner'}>
          <form onSubmit={handleSubmit} noValidate className="nl-form-wrap">
            {state === 'success' && (
              <div className="nl-state success">
                <strong>🎉 Fast geschafft!</strong>
                <p>
                  Wir haben eine Bestätigungs-Mail an{' '}
                  <span className="nl-email">{submittedEmail}</span> gesendet.
                  Bitte klicke den Link darin, um dein Abonnement zu aktivieren.
                </p>
              </div>
            )}

            {state === 'error' && (
              <div className="nl-state error">
                <strong>✕ Fehler</strong>
                <p>{errorMsg}</p>
              </div>
            )}

            {state !== 'success' && (
              <>
                {!compact && (
                  <>
                    <h2>#tiroltourismus <span className="gold">Newsletter</span></h2>
                    <p>
                      Verpassen Sie keine Neuigkeit aus Tirol. Exklusive Tipps,
                      neue Angebote und Geschichten direkt in Ihr Postfach – jederzeit kündbar.
                    </p>
                  </>
                )}

                {!compact && (
                  <div className="nl-name-row">
                    <input
                      type="text"
                      className="nl-input"
                      placeholder="Dein Vorname"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      autoComplete="given-name"
                    />
                  </div>
                )}

                <div className="nl-row">
                  <input
                    type="email"
                    className={`nl-input${errorMsg && !email.trim() ? ' error' : ''}`}
                    placeholder={compact ? 'Deine E-Mail' : 'deine@email.at'}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
                    required
                  />
                  <button
                    type="submit"
                    className={`nl-submit ${compact ? '' : 'gold'}`}
                    disabled={state === 'loading'}
                  >
                    {state === 'loading' ? (
                      <span className="nl-spinner" />
                    ) : compact ? (
                      'Anmelden ✈️'
                    ) : (
                      'Kostenlos anmelden'
                    )}
                  </button>
                </div>

                <label className="nl-checkbox">
                  <input
                    type="checkbox"
                    checked={consent}
                    onChange={(e) => setConsent(e.target.checked)}
                  />
                  <span>
                    Ich habe die{' '}
                    <a href="/datenschutz/" target="_blank" rel="noopener noreferrer">
                      Datenschutzerklärung
                    </a>{' '}
                    gelesen und stimme zu.
                  </span>
                </label>

                {!compact && (
                  <p style={{
                    fontSize: '11px',
                    color: 'rgba(255,255,255,.4)',
                    marginTop: '4px',
                  }}>
                    Mit dem Absenden erklärst du dich mit der Verarbeitung
                    zum Newsletter-Versand einverstanden. Abmeldung jederzeit.
                  </p>
                )}
              </>
            )}
          </form>
        </div>
      </div>
    </>
  );
}
