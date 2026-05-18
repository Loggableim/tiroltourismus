/**
 * AdminPendingDashboard.tsx — Admin-Dashboard zur Freigabe von Betriebs-Einträgen
 *
 * Liest pending entries aus localStorage (von BetriebRegistrationForm gespeichert).
 * Approve: verschiebt in 'tirol_approved_betriebe', zeigt JSON zum Export.
 * Reject: entfernt aus pending und speichert in 'tirol_rejected_betriebe'.
 *
 * Use: client:load in /admin/pending/index.astro
 */

import { useState, useEffect, useCallback } from 'react';

/* ── Types ── */
export interface BetriebEntry {
  name: string;
  typ: string;
  ort: string;
  beschreibung: string;
  email: string;
  telefon: string;
  bildUrl: string;
  submittedAt?: string;
}

interface ApprovedEntry extends BetriebEntry {
  approvedAt: string;
}

const PENDING_KEY = 'tirol_pending_betriebe';
const APPROVED_KEY = 'tirol_approved_betriebe';
const REJECTED_KEY = 'tirol_rejected_betriebe';

/* ── Helpers ── */
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

function loadJSON<T>(key: string): T[] {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveJSON<T>(key: string, data: T[]) {
  localStorage.setItem(key, JSON.stringify(data));
}

/** Generiere vollständiges Eintrags-JSON für den Export */
function buildExportEntry(data: BetriebEntry, slug: string, status: 'published' | 'rejected') {
  return {
    slug,
    name: data.name,
    typ: data.typ,
    ort: data.ort,
    kurzbeschreibung: data.beschreibung,
    kontakt: {
      email: data.email,
      telefon: data.telefon || null,
    },
    bildUrl: data.bildUrl || null,
    status,
    erstelltAm: data.submittedAt || new Date().toISOString(),
    veroentlichtAm: status === 'published' ? new Date().toISOString() : null,
  };
}

/** Einen Datei-Download triggern */
function downloadJSON(filename: string, json: unknown) {
  const blob = new Blob([JSON.stringify(json, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/* ── Component ── */
export default function AdminPendingDashboard() {
  const [pending, setPending] = useState<BetriebEntry[]>([]);
  const [approved, setApproved] = useState<ApprovedEntry[]>([]);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending');
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  const loadData = useCallback(() => {
    setPending(loadJSON<BetriebEntry>(PENDING_KEY));
    setApproved(loadJSON<ApprovedEntry>(APPROVED_KEY));
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  /* ── Show notification ── */
  function notify(type: 'success' | 'error', msg: string) {
    setNotification({ type, msg });
    setTimeout(() => setNotification(null), 4000);
  }

  /* ── Approve an entry ── */
  function handleApprove(index: number) {
    const entry = pending[index];
    if (!entry) return;

    const approvedEntry: ApprovedEntry = {
      ...entry,
      submittedAt: entry.submittedAt || new Date().toISOString(),
      approvedAt: new Date().toISOString(),
    };

    // Move from pending to approved
    const newPending = [...pending];
    newPending.splice(index, 1);
    const newApproved = [...approved, approvedEntry];

    saveJSON(PENDING_KEY, newPending);
    saveJSON(APPROVED_KEY, newApproved);

    setPending(newPending);
    setApproved(newApproved);

    notify('success', `"${entry.name}" wurde freigegeben!`);
  }

  /* ── Reject an entry ── */
  function handleReject(index: number) {
    const entry = pending[index];
    if (!entry) return;

    // Append to rejected archive
    const rejectedLog = loadJSON<{ entry: BetriebEntry; rejectedAt: string }>(REJECTED_KEY);
    rejectedLog.push({ entry, rejectedAt: new Date().toISOString() });
    saveJSON(REJECTED_KEY, rejectedLog);

    // Remove from pending
    const newPending = [...pending];
    newPending.splice(index, 1);
    saveJSON(PENDING_KEY, newPending);
    setPending(newPending);

    notify('success', `"${entry.name}" wurde abgelehnt.`);
  }

  /* ── Download all approved entries as a single JSON collection ── */
  function handleDownloadAll() {
    const entries = approved.map((e) =>
      buildExportEntry(e, makeSlug(e.name), 'published')
    );
    downloadJSON('approved-betriebe.json', entries);
  }

  /* ── Download a single pending entry as JSON ── */
  function handleDownloadPending(entry: BetriebEntry) {
    const slug = makeSlug(entry.name);
    const json = buildExportEntry(entry, slug, 'pending');
    downloadJSON(`${slug}/index.json`, json);
  }

  /* ── Clear localStorage and reset everything ── */
  function handleClearAll() {
    if (!window.confirm('Alle Daten unwiderruflich löschen?')) return;
    localStorage.removeItem(PENDING_KEY);
    localStorage.removeItem(APPROVED_KEY);
    localStorage.removeItem(REJECTED_KEY);
    setPending([]);
    setApproved([]);
    notify('success', 'Alle Daten wurden gelöscht.');
  }

  return (
    <div className="admin-dashboard">
      {/* ── Notification bar ── */}
      {notification && (
        <div className={`admin-notification admin-notification-${notification.type}`} role="alert">
          {notification.msg}
        </div>
      )}

      {/* ── Stats ── */}
      <div className="admin-stats">
        <div className="admin-stat">
          <span className="admin-stat-num">{pending.length}</span>
          <span className="admin-stat-label">Ausstehend</span>
        </div>
        <div className="admin-stat">
          <span className="admin-stat-num" style={{color: 'var(--green, #00C853)'}}>{approved.length}</span>
          <span className="admin-stat-label">Freigegeben</span>
        </div>
        <div className="admin-stat">
          <span className="admin-stat-num">{loadJSON(REJECTED_KEY).length}</span>
          <span className="admin-stat-label">Abgelehnt</span>
        </div>
      </div>

      {/* ── Actions bar ── */}
      <div className="admin-actions-bar">
        <div className="admin-tabs">
          <button
            className={`admin-tab${filter === 'pending' ? ' active' : ''}`}
            onClick={() => setFilter('pending')}
          >
            ⏳ Ausstehend ({pending.length})
          </button>
          <button
            className={`admin-tab${filter === 'approved' ? ' active' : ''}`}
            onClick={() => setFilter('approved')}
          >
            ✅ Freigegeben ({approved.length})
          </button>
          <button
            className={`admin-tab${filter === 'all' ? ' active' : ''}`}
            onClick={() => setFilter('all')}
          >
            📋 Alle anzeigen
          </button>
        </div>
        <div className="admin-actions-r">
          <button className="admin-btn admin-btn-download" onClick={handleDownloadAll} disabled={approved.length === 0}>
            ⬇ Alle Exportieren
          </button>
          <button className="admin-btn admin-btn-danger" onClick={handleClearAll}>
            🗑 Zurücksetzen
          </button>
        </div>
      </div>

      {/* ── PENDING LIST ── */}
      {(filter === 'pending' || filter === 'all') && pending.length > 0 && (
        <section className="admin-section">
          <h2 className="admin-section-title">⏳ Ausstehende Einträge ({pending.length})</h2>
          {pending.map((entry, i) => (
            <div key={i} className="admin-entry">
              <div className="admin-entry-header">
                <span className="admin-entry-emoji">🏪</span>
                <div className="admin-entry-meta">
                  <h3 className="admin-entry-name">{entry.name}</h3>
                  <span className="admin-entry-typ">{entry.typ}</span>
                  <span className="admin-entry-divider">·</span>
                  <span className="admin-entry-ort">📍 {entry.ort}</span>
                </div>
                {entry.submittedAt && (
                  <span className="admin-entry-date">
                    {new Date(entry.submittedAt).toLocaleDateString('de-AT', {
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
                {entry.bildUrl && (
                  <div className="admin-entry-img">
                    <span>🖼️ </span>
                    <a href={entry.bildUrl} target="_blank" rel="noopener noreferrer" className="admin-link">
                      {entry.bildUrl}
                    </a>
                  </div>
                )}
              </div>

              {/* JSON Preview */}
              <details className="admin-entry-json-details">
                <summary className="admin-entry-json-summary">📄 JSON anzeigen</summary>
                <pre className="admin-entry-json">{JSON.stringify(
                  buildExportEntry(entry, makeSlug(entry.name), 'pending'),
                  null, 2
                )}</pre>
              </details>

              <div className="admin-entry-actions">
                <button
                  className="admin-btn admin-btn-approve"
                  onClick={() => handleApprove(i)}
                >
                  ✅ Freigeben
                </button>
                <button
                  className="admin-btn admin-btn-reject"
                  onClick={() => handleReject(i)}
                >
                  ❌ Ablehnen
                </button>
                <button
                  className="admin-btn admin-btn-ghost"
                  onClick={() => handleDownloadPending(entry)}
                >
                  ⬇ JSON
                </button>
              </div>
            </div>
          ))}
        </section>
      )}

      {/* ── APPROVED LIST ── */}
      {(filter === 'approved' || filter === 'all') && approved.length > 0 && (
        <section className="admin-section">
          <h2 className="admin-section-title">✅ Freigegebene Einträge ({approved.length})</h2>
          {approved.map((entry, i) => (
            <div key={i} className="admin-entry admin-entry-approved">
              <div className="admin-entry-header">
                <span className="admin-entry-emoji">✅</span>
                <div className="admin-entry-meta">
                  <h3 className="admin-entry-name">{entry.name}</h3>
                  <span className="admin-entry-typ">{entry.typ}</span>
                  <span className="admin-entry-divider">·</span>
                  <span className="admin-entry-ort">📍 {entry.ort}</span>
                </div>
                <span className="admin-entry-date">
                  Freigegeben: {new Date(entry.approvedAt).toLocaleDateString('de-AT', {
                    day: '2-digit', month: '2-digit', year: 'numeric',
                    hour: '2-digit', minute: '2-digit'
                  })}
                </span>
              </div>

              <details className="admin-entry-json-details">
                <summary className="admin-entry-json-summary">📄 JSON zum Einfügen in <code>src/data/pending/{makeSlug(entry.name)}/index.json</code></summary>
                <pre className="admin-entry-json">{JSON.stringify(
                  buildExportEntry(entry, makeSlug(entry.name), 'published'),
                  null, 2
                )}</pre>
              </details>
            </div>
          ))}
        </section>
      )}

      {/* ── Empty state ── */}
      {pending.length === 0 && (filter === 'pending' || filter === 'all') && (
        <div className="admin-empty">
          <div className="admin-empty-icon">📭</div>
          <h3 className="admin-empty-title">Keine ausstehenden Einträge</h3>
          <p className="admin-empty-text">
            Es wurden noch keine Betriebs-Einträge über das Registrierungsformular eingereicht.
          </p>
          <a href="/fuer-betriebe/registrierung/" className="btn btn-pink">
            Registrierungsformular öffnen →
          </a>
        </div>
      )}
    </div>
  );
}
