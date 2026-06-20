/**
 * EventSubmissionForm.tsx — React self-registration form for events.
 * Speichert in localStorage unter 'tirol_pending_events' (Admin-Freigabe analog Betriebe).
 * Uses: client:load in Astro pages.
 */

import { useState, type FormEvent } from 'react';

type FormState = 'idle' | 'loading' | 'success' | 'error';

const STORAGE_KEY = 'tirol_pending_events';

const KATEGORIEN = [
  'Sport', 'Konzert', 'Festival', 'Kultur', 'Kulinarik',
  'Wanderung', 'Markt', 'Vortrag', 'Workshop', 'Sonstiges',
];

interface FormFields {
  titel: string;
  kategorie: string;
  ort: string;
  datum_von: string;
  datum_bis: string;
  uhrzeit: string;
  beschreibung: string;
  preis: string;
  webseite: string;
  email: string;
  veranstalter: string;
}

function loadPending(): FormFields[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function savePending(entry: FormFields) {
  const existing = loadPending();
  existing.push(entry);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(existing));
}

function makeSlug(text: string): string {
  return text
    .toLowerCase()
    .replace(/[ä]/g, 'ae').replace(/[ö]/g, 'oe').replace(/[ü]/g, 'ue').replace(/[ß]/g, 'ss')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 60);
}

export default function EventSubmissionForm() {
  const [status, setStatus] = useState<FormState>('idle');
  const [errMsg, setErrMsg] = useState('');

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setStatus('loading');
    setErrMsg('');

    const form = e.currentTarget;
    const formData = new FormData(form);

    const entry: FormFields = {
      titel: (formData.get('titel') as string) || '',
      kategorie: (formData.get('kategorie') as string) || '',
      ort: (formData.get('ort') as string) || '',
      datum_von: (formData.get('datum_von') as string) || '',
      datum_bis: (formData.get('datum_bis') as string) || '',
      uhrzeit: (formData.get('uhrzeit') as string) || '',
      beschreibung: (formData.get('beschreibung') as string) || '',
      preis: (formData.get('preis') as string) || '',
      webseite: (formData.get('webseite') as string) || '',
      email: (formData.get('email') as string) || '',
      veranstalter: (formData.get('veranstalter') as string) || '',
    };

    // Validation
    if (!entry.titel || !entry.ort || !entry.datum_von) {
      setErrMsg('Bitte Titel, Ort und Datum ausfüllen.');
      setStatus('error');
      return;
    }

    try {
      // In localStorage speichern
      savePending(entry);

      // Optional: an Server senden
      try {
        await fetch('https://webhook.tiroltourismus.com/api/event-register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(entry),
        });
      } catch {
        // Server nicht erreichbar → nur localStorage (kein Fehler)
      }

      setStatus('success');
      form.reset();
    } catch (err) {
      setErrMsg('Fehler beim Speichern. Bitte versuch es erneut.');
      setStatus('error');
    }
  };

  if (status === 'success') {
    return (
      <div class="ev-form-success">
        <div class="ev-form-success-icon">✅</div>
        <h3>Event eingereicht!</h3>
        <p>Dein Event wurde gespeichert und wird nach Prüfung durch unser Team freigeschaltet.</p>
        <button class="btn btn-pink" onClick={() => setStatus('idle')}>
          Ein weiteres Event eintragen
        </button>
      </div>
    );
  }

  return (
    <form class="ev-form" onSubmit={handleSubmit}>
      {errMsg && <div class="ev-form-error">{errMsg}</div>}

      <div class="ev-form-row">
        <div class="ev-form-group full">
          <label>Titel des Events *</label>
          <input type="text" name="titel" required placeholder="z.B. Bergfest am Gipfel" />
        </div>
      </div>

      <div class="ev-form-row">
        <div class="ev-form-group">
          <label>Kategorie</label>
          <select name="kategorie" required>
            <option value="">Bitte wählen</option>
            {KATEGORIEN.map(k => <option value={k}>{k}</option>)}
          </select>
        </div>
        <div class="ev-form-group">
          <label>Ort *</label>
          <input type="text" name="ort" required placeholder="z.B. Innsbruck" />
        </div>
      </div>

      <div class="ev-form-row">
        <div class="ev-form-group">
          <label>Startdatum *</label>
          <input type="date" name="datum_von" required />
        </div>
        <div class="ev-form-group">
          <label>Enddatum</label>
          <input type="date" name="datum_bis" />
        </div>
        <div class="ev-form-group">
          <label>Uhrzeit</label>
          <input type="time" name="uhrzeit" />
        </div>
      </div>

      <div class="ev-form-group full">
        <label>Beschreibung</label>
        <textarea name="beschreibung" rows={4} placeholder="Kurze Beschreibung des Events…" />
      </div>

      <div class="ev-form-row">
        <div class="ev-form-group">
          <label>Eintrittspreis</label>
          <input type="text" name="preis" placeholder="z.B. €35,– oder Eintritt frei" />
        </div>
        <div class="ev-form-group">
          <label>Webseite</label>
          <input type="url" name="webseite" placeholder="https://…" />
        </div>
      </div>

      <div class="ev-form-row">
        <div class="ev-form-group">
          <label>Dein Name / Veranstalter</label>
          <input type="text" name="veranstalter" placeholder="Max Mustermann" />
        </div>
        <div class="ev-form-group">
          <label>E-Mail (nicht öffentlich)</label>
          <input type="email" name="email" placeholder="deine@email.at" />
        </div>
      </div>

      <div class="ev-form-actions">
        <p class="ev-form-hinweis">* Pflichtfelder. Nach Prüfung wird dein Event freigeschaltet.</p>
        <button type="submit" class="btn btn-pink" disabled={status === 'loading'}>
          {status === 'loading' ? '⏳ Wird gespeichert…' : 'Event einreichen 🎪'}
        </button>
      </div>

      <style>{`
        .ev-form{max-width:680px;margin:0 auto}
        .ev-form-error{background:rgba(255,20,147,.1);border:1px solid var(--tirol-pink);border-radius:var(--radius);padding:12px 16px;margin-bottom:20px;color:var(--tirol-pink);font-size:14px}
        .ev-form-row{display:flex;gap:16px;margin-bottom:16px}
        .ev-form-group{flex:1;display:flex;flex-direction:column;gap:4px}
        .ev-form-group.full{width:100%;margin-bottom:16px}
        .ev-form-group label{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--text3)}
        .ev-form-group input,.ev-form-group select,.ev-form-group textarea{padding:10px 14px;border:1px solid var(--glass-border);border-radius:var(--radius-sm);background:var(--bg);color:var(--text);font-size:14px;font-family:inherit;transition:border-color .2s}
        .ev-form-group input:focus,.ev-form-group select:focus,.ev-form-group textarea:focus{outline:none;border-color:var(--tirol-pink);box-shadow:0 0 0 3px rgba(255,20,147,.1)}
        .ev-form-group textarea{resize:vertical;min-height:100px}
        .ev-form-actions{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;padding-top:8px;border-top:1px solid var(--glass-border)}
        .ev-form-hinweis{font-size:12px;color:var(--text3);margin:0}
        .ev-form-success{text-align:center;padding:60px 20px}
        .ev-form-success-icon{font-size:64px;margin-bottom:16px}
        .ev-form-success h3{font-family:var(--font-display);font-size:28px;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px}
        .ev-form-success p{color:var(--text2);max-width:400px;margin:0 auto 24px;line-height:1.6}
        @media(max-width:600px){
          .ev-form-row{flex-direction:column;gap:12px}
          .ev-form-actions{flex-direction:column;align-items:stretch}
          .ev-form-hinweis{text-align:center}
        }
      `}</style>
    </form>
  );
}
