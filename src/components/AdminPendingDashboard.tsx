/**
 * AdminPendingDashboard.tsx — Admin-Dashboard zur Freigabe von Betriebs-Einträgen
 *
 * Liest pending entries von der VPS-API (webhook.tiroltourismus.com).
 * Approve/Reject per API-Aufruf. Enthält einfachen Passwort-Schutz.
 *
 * Use: client:load in /admin/pending/index.astro
 */

import { useState, useEffect, useCallback } from 'react';
import AdminTabs from './AdminTabs';

/* ── Types ── */
export interface BetriebEntry {
  slug?: string;
  name: string;
  typ: string;
  ort: string;
  beschreibung: string;
  email: string;
  telefon: string;
  bildUrl: string;
  status?: string;
  erstelltAm?: string;
  freigegebenAm?: string;
  serverSlug?: string;
}

/* ── API ── */
function getApiBase() {
  return typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:3456'
    : 'https://webhook.tiroltourismus.com';
}

/* ── Simple Admin-Passwort (niedrige Sicherheitsstufe für GitHub Pages) ── */
const ADMIN_PASSWORD = 'tirol2026';

/* ── Component ── */
export default function AdminPendingDashboard() {
  const [authed, setAuthed] = useState(false);
  const [pwInput, setPwInput] = useState('');
  const [pwError, setPwError] = useState('');

  const [pending, setPending] = useState<BetriebEntry[]>([]);
  const [approved, setApproved] = useState<BetriebEntry[]>([]);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved'>('pending');
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);
  const [loading, setLoading] = useState(true);

  /* ── Passwort-Login ── */
  function handleLogin() {
    if (pwInput === ADMIN_PASSWORD) {
      setAuthed(true);
      setPwError('');
    } else {
      setPwError('Falsches Passwort.');
    }
  }

  function handlePwKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter') handleLogin();
  }

  /* ── Daten von API laden ── */
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${getApiBase()}/api/betriebe/pending`);
      if (resp.ok) {
        const entries: BetriebEntry[] = await resp.json();
        setPending(entries.filter(e => e.status === 'pending'));
        setApproved(entries.filter(e => e.status === 'published' || e.status === 'approved'));
      }
    } catch (e) {
      console.warn('Fehler beim Laden der pending entries:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authed) loadData();
  }, [authed, loadData]);

  /* ── Notification ── */
  function notify(type: 'success' | 'error', msg: string) {
    setNotification({ type, msg });
    setTimeout(() => setNotification(null), 4000);
  }

  /* ── Publish (freigeben + in Kategorie veröffentlichen) ── */
  async function handlePublish(slug: string) {
    try {
      const resp = await fetch(`${getApiBase()}/api/betriebe/pending/${slug}/publish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      const data = await resp.json();
      if (resp.ok) {
        notify('success', `"${data.name}" wurde veröffentlicht → /${data.category}/${data.slug}/`);
        await loadData();
      } else {
        notify('error', data.error || 'Fehler beim Veröffentlichen');
      }
    } catch (e) {
      notify('error', 'Server nicht erreichbar');
    }
  }

  /* ── Reject ── */
  async function handleReject(slug: string) {
    const grund = window.prompt('Grund für Ablehnung (optional):');
    try {
      const resp = await fetch(`${getApiBase()}/api/betriebe/pending/${slug}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grund: grund || '' }),
      });
      if (resp.ok) {
        const entry = pending.find(e => e.slug === slug);
        notify('success', `"${entry?.name || slug}" wurde abgelehnt.`);
        await loadData();
      } else {
        const err = await resp.json();
        notify('error', err.error || 'Fehler beim Ablehnen');
      }
    } catch (e) {
      notify('error', 'Server nicht erreichbar');
    }
  }

  /* ── Refresh ── */
  function handleRefresh() {
    loadData();
    notify('success', 'Daten aktualisiert.');
  }

  /* ── PASSWORT-GATE ── */
  if (!authed) {
    return (
      <div className="admin-gate">
        <div className="admin-gate-card">
          <div className="admin-gate-icon">🔐</div>
          <h2>Admin-Bereich</h2>
          <p>Bitte Passwort eingeben, um fortzufahren.</p>
          <input
            type="password"
            className="admin-gate-input"
            placeholder="Passwort"
            value={pwInput}
            onChange={e => setPwInput(e.target.value)}
            onKeyDown={handlePwKeyDown}
            autoFocus
          />
          <button className="admin-gate-btn" onClick={handleLogin}>
            Freischalten
          </button>
          {pwError && <p className="admin-gate-error">{pwError}</p>}
        </div>
      </div>
    );
  }

  /* ── LOADING ── */
  if (loading) {
    return (
      <div className="admin-loading">
        <div className="admin-loading-spinner" />
        <p className="admin-loading-text">Lade ausstehende Einträge…</p>
      </div>
    );
  }

  /* ── DASHBOARD ── */
  return (
    <div className="admin-dashboard">
      {/* Notification */}
      {notification && (
        <div className={`admin-notification admin-notification-${notification.type}`} role="alert">
          {notification.msg}
        </div>
      )}

      {/* Stats */}
      <div className="admin-stats">
        <div className="admin-stat">
          <span className="admin-stat-num">{pending.length}</span>
          <span className="admin-stat-label">Ausstehend</span>
        </div>
        <div className="admin-stat">
          <span className="admin-stat-num" style={{color: 'var(--green)'}}>{approved.length}</span>
          <span className="admin-stat-label">Freigegeben</span>
        </div>
        <div className="admin-stat">
          <span className="admin-stat-num">—</span>
          <span className="admin-stat-label">Abgelehnt (per API)</span>
        </div>
      </div>

      {/* Actions */}
      <div className="admin-actions-bar">
        <AdminTabs
          active={filter}
          onChange={setFilter}
          items={[
            { value: 'pending', label: `📋 Ausstehend (${pending.length})` },
            { value: 'approved', label: `✅ Freigegeben (${approved.length})` },
            { value: 'all', label: `📦 Alle (${pending.length + approved.length})` },
          ]}
        />
        <div className="admin-actions-r">
          <button className="admin-btn admin-btn-ghost" onClick={handleRefresh}>
            🔄 Aktualisieren
          </button>
        </div>
      </div>

      {/* PENDING LIST */}
      {(filter === 'pending' || filter === 'all') && pending.length > 0 && (
        <section className="admin-section">
          <h2 className="admin-section-title">⏳ Ausstehende Einträge ({pending.length})</h2>
          {pending.map((entry, i) => (
            <div key={entry.slug || i} className="admin-entry">
              <div className="admin-entry-header">
                <span className="admin-entry-emoji">🏪</span>
                <div className="admin-entry-meta">
                  <h3 className="admin-entry-name">{entry.name}</h3>
                  <span className="admin-entry-typ">{entry.typ}</span>
                  <span className="admin-entry-divider">·</span>
                  <span className="admin-entry-ort">📍 {entry.ort}</span>
                </div>
                {entry.erstelltAm && (
                  <span className="admin-entry-date">
                    {new Date(entry.erstelltAm).toLocaleDateString('de-AT', {
                      day: '2-digit', month: '2-digit', year: 'numeric',
                      hour: '2-digit', minute: '2-digit'
                    })}
                  </span>
                )}
              </div>

              <div className="admin-entry-body">
                <p className="admin-entry-desc">{entry.beschreibung}</p>
                <div className="admin-entry-contact">
                  <span>✉️ {entry.email}</span>
                  {entry.telefon && <span>📞 {entry.telefon}</span>}
                </div>
              </div>

              <div className="admin-entry-actions">
                <button className="admin-btn admin-btn-approve" onClick={() => handlePublish(entry.slug || '')}>
                  📰 Veröffentlichen
                </button>
                <button className="admin-btn admin-btn-reject" onClick={() => handleReject(entry.slug || '')}>
                  ❌ Ablehnen
                </button>
              </div>
            </div>
          ))}
        </section>
      )}

      {/* APPROVED LIST */}
      {(filter === 'approved' || filter === 'all') && approved.length > 0 && (
        <section className="admin-section">
          <h2 className="admin-section-title">✅ Freigegebene Einträge ({approved.length})</h2>
          {approved.map((entry, i) => (
            <div key={entry.slug || i} className="admin-entry admin-entry-approved">
              <div className="admin-entry-header">
                <span className="admin-entry-emoji">✅</span>
                <div className="admin-entry-meta">
                  <h3 className="admin-entry-name">{entry.name}</h3>
                  <span className="admin-entry-typ">{entry.typ}</span>
                  <span className="admin-entry-divider">·</span>
                  <span className="admin-entry-ort">📍 {entry.ort}</span>
                </div>
                {entry.freigegebenAm && (
                  <span className="admin-entry-date">
                    Freigegeben: {new Date(entry.freigegebenAm).toLocaleDateString('de-AT', {
                      day: '2-digit', month: '2-digit', year: 'numeric',
                      hour: '2-digit', minute: '2-digit'
                    })}
                  </span>
                )}
              </div>
              <p className="admin-entry-desc">{entry.beschreibung}</p>
              <div className="admin-entry-contact">
                <span>✉️ {entry.email}</span>
              </div>
            </div>
          ))}
        </section>
      )}

      {/* EMPTY STATE */}
      {pending.length === 0 && approved.length === 0 && (
        <div className="admin-empty">
          <div className="admin-empty-icon">📭</div>
          <h3 className="admin-empty-title">Keine Einträge</h3>
          <p className="admin-empty-text">
            Es wurden noch keine Betriebs-Einträge eingereicht.
          </p>
          <a href="/fuer-betriebe/registrierung/" className="btn btn-pink">
            Registrierungsformular öffnen →
          </a>
        </div>
      )}
    </div>
  );
}
