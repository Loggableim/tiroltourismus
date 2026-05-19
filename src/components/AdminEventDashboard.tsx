/**
 * AdminEventDashboard.tsx — Admin-Dashboard zur Freigabe von Event-Einträgen
 *
 * Liest pending events aus localStorage + API.
 * Approve: erstellt JSON-Datei-Struktur in /src/data/events/
 * Reject: entfernt Eintrag
 *
 * Use: client:load in /admin/events/index.astro
 */

import { useState, useEffect, useCallback } from 'react';

/* ── Types ── */
interface EventEntry {
  slug?: string;
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
  status?: string;
  erstelltAm?: string;
}

/* ── Simple Admin-Passwort (gleiches wie Betriebe) ── */
const ADMIN_PASSWORD = 'tirol2026';
const STORAGE_KEY = 'tirol_pending_events';

/* ── Component ── */
export default function AdminEventDashboard() {
  const [authed, setAuthed] = useState(false);
  const [pwInput, setPwInput] = useState('');
  const [pwError, setPwError] = useState('');

  const [pending, setPending] = useState<EventEntry[]>([]);
  const [approved, setApproved] = useState<EventEntry[]>([]);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved'>('pending');
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(Date.now());

  /* ── Passwort-Login ── */
  function handleLogin() {
    if (pwInput === ADMIN_PASSWORD) {
      setAuthed(true);
      setPwError('');
    } else {
      setPwError('Falsches Passwort.');
    }
  }

  /* ── Daten laden (localStorage + API) ── */
  const loadData = useCallback(async () => {
    setLoading(true);
    const allEntries: EventEntry[] = [];

    // 1. Aus localStorage lesen
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const localEntries: EventEntry[] = JSON.parse(raw);
        localEntries.forEach(e => {
          if (!e.status) e.status = 'pending';
          if (!e.erstelltAm) e.erstelltAm = new Date().toISOString();
        });
        allEntries.push(...localEntries);
      }
    } catch (e) {
      console.warn('Fehler beim Lesen von localStorage:', e);
    }

    // 2. Versuche API
    try {
      const apiBase = (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
        ? 'http://localhost:3456'
        : 'https://webhook.tiroltourismus.com';
      const resp = await fetch(`${apiBase}/api/events/pending`);
      if (resp.ok) {
        const apiEntries: EventEntry[] = await resp.json();
        // Merge ohne Duplikate
        const existingSlugs = new Set(allEntries.map(e => e.slug || makeSlug(e.titel)));
        for (const ae of apiEntries) {
          const slug = ae.slug || makeSlug(ae.titel);
          if (!existingSlugs.has(slug)) {
            allEntries.push(ae);
            existingSlugs.add(slug);
          }
        }
      }
    } catch {
      // API nicht erreichbar → nur localStorage
    }

    setPending(allEntries.filter(e => e.status === 'pending'));
    setApproved(allEntries.filter(e => e.status === 'published' || e.status === 'approved'));
    setLoading(false);
  }, []);

  useEffect(() => {
    if (authed) loadData();
  }, [authed, loadData, lastRefresh]);

  /* ── Notification ── */
  function notify(type: 'success' | 'error', msg: string) {
    setNotification({ type, msg });
    setTimeout(() => setNotification(null), 4000);
  }

  /* ── Slug generieren ── */
  function makeSlug(text: string): string {
    return text
      .toLowerCase()
      .replace(/[ä]/g, 'ae').replace(/[ö]/g, 'oe').replace(/[ü]/g, 'ue').replace(/[ß]/g, 'ss')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .substring(0, 60);
  }

  /* ── Publish (freigeben) ── */
  async function handlePublish(slug: string, entry: EventEntry) {
    const idx = pending.findIndex(e => (e.slug || makeSlug(e.titel)) === slug);
    if (idx === -1) return;

    try {
      // 1. Aus localStorage entfernen
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const all: EventEntry[] = JSON.parse(raw);
        const filtered = all.filter(e => (e.slug || makeSlug(e.titel)) !== slug);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
      }

      // 2. In approved verschieben
      const published = { ...entry, status: 'published', slug };
      setApproved(prev => [...prev, published]);
      setPending(prev => prev.filter(e => (e.slug || makeSlug(e.titel)) !== slug));

      // 3. Als JSON-Datei-Struktur EXPORTIEREN
      // Download als JSON zum Einspielen ins Repo
      const jsonData = {
        titel: entry.titel,
        name: entry.titel,
        slug,
        status: 'published',
        kategorie: entry.kategorie,
        ort: entry.ort,
        region: entry.ort || '',
        datum: entry.datum_von,
        datum_von: entry.datum_von,
        datum_bis: entry.datum_bis || entry.datum_von,
        uhrzeit: entry.uhrzeit || '',
        kurzbeschreibung: entry.beschreibung?.substring(0, 200) || entry.titel,
        beschreibung: entry.beschreibung || '',
        preis: entry.preis || '',
        link: entry.webseite || '#',
        webseite: entry.webseite || '#',
        veranstalter: entry.veranstalter || '',
        email: entry.email || '',
        tags: [entry.kategorie?.toLowerCase() || '', entry.ort?.toLowerCase() || ''].filter(Boolean),
        emoji: '🎪',
        farbe: '#FF1493',
        bilder: [],
        hero_bild: null,
        koordinaten: null,
      };

      // Download als JSON
      const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${slug}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      notify('success', `"${entry.titel}" wurde freigegeben → JSON exportiert (in src/data/events/${slug}/index.json einspielen)`);

      // 4. Optional: an Server senden
      try {
        const apiBase = (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
          ? 'http://localhost:3456'
          : 'https://webhook.tiroltourismus.com';
        await fetch(`${apiBase}/api/events/publish`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ slug, ...jsonData }),
        });
      } catch {}
    } catch (e) {
      notify('error', 'Fehler beim Freigeben');
    }
  }

  /* ── Reject ── */
  function handleReject(slug: string) {
    const grund = window.prompt('Grund für Ablehnung (optional):');

    // Aus localStorage entfernen
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const all: EventEntry[] = JSON.parse(raw);
      const filtered = all.filter(e => (e.slug || makeSlug(e.titel)) !== slug);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    }

    setPending(prev => prev.filter(e => (e.slug || makeSlug(e.titel)) !== slug));
    notify('success', `Event wurde abgelehnt.${grund ? ' Grund: ' + grund : ''}`);
  }

  /* ── Refresh ── */
  function handleRefresh() {
    setLastRefresh(Date.now());
    notify('success', 'Daten aktualisiert.');
  }

  /* ── PASSWORT-GATE ── */
  if (!authed) {
    return (
      <div class="admin-login">
        <div class="admin-login-box">
          <div style="font-size:48px;margin-bottom:12px">🔐</div>
          <h3>Admin-Zugang</h3>
          <p>Bitte Passwort eingeben, um Events zu verwalten.</p>
          <div class="admin-pw-row">
            <input
              type="password"
              value={pwInput}
              onChange={e => setPwInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleLogin()}
              placeholder="Passwort"
              class="admin-pw-input"
              autoFocus
            />
            <button onClick={handleLogin} class="admin-pw-btn">Login</button>
          </div>
          {pwError && <p class="admin-pw-error">{pwError}</p>}
        </div>
      </div>
    );
  }

  /* ── DASHBOARD ── */
  const displayEntries = filter === 'pending' ? pending : filter === 'approved' ? approved : [...pending, ...approved];

  return (
    <div class="admin-dashboard">
      {/* Notification */}
      {notification && (
        <div class={`admin-notification admin-notification-${notification.type}`}>
          {notification.msg}
        </div>
      )}

      {/* Header */}
      <div class="admin-dash-header">
        <div class="admin-stats">
          <div class="admin-stat">
            <span class="admin-stat-num">{pending.length}</span>
            <span class="admin-stat-label">Ausstehend</span>
          </div>
          <div class="admin-stat">
            <span class="admin-stat-num">{approved.length}</span>
            <span class="admin-stat-label">Freigegeben</span>
          </div>
          <div class="admin-stat">
            <span class="admin-stat-num">{pending.length + approved.length}</span>
            <span class="admin-stat-label">Gesamt</span>
          </div>
        </div>
        <div class="admin-actions">
          <button onClick={handleRefresh} class="admin-btn admin-btn-refresh">🔄 Aktualisieren</button>
        </div>
      </div>

      {/* Filter */}
      <div class="admin-tabs">
        {(['pending', 'approved', 'all'] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            class={`admin-tab ${filter === f ? 'active' : ''}`}
          >
            {f === 'pending' ? '📋 Ausstehend' : f === 'approved' ? '✅ Freigegeben' : '📦 Alle'}
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && <div class="admin-loading">⏳ Daten werden geladen…</div>}

      {/* Empty */}
      {!loading && displayEntries.length === 0 && (
        <div class="admin-empty">
          <div style="font-size:48px;margin-bottom:12px">🎉</div>
          <h3>Keine Einträge</h3>
          <p>{filter === 'pending' ? 'Alle Events wurden bearbeitet.' : 'Noch keine Events vorhanden.'}</p>
        </div>
      )}

      {/* List */}
      {!loading && displayEntries.length > 0 && (
        <div class="admin-list">
          {displayEntries.map((entry, i) => {
            const slug = entry.slug || makeSlug(entry.titel);
            const isPending = entry.status === 'pending' || !entry.status;
            return (
              <div key={slug + i} class={`admin-card ${isPending ? '' : 'admin-card-approved'}`}>
                <div class="admin-card-left">
                  <div class="admin-card-emoji">🎪</div>
                  <div class="admin-card-info">
                    <h3 class="admin-card-title">{entry.titel}</h3>
                    <div class="admin-card-meta">
                      {entry.ort && <span>📍 {entry.ort}</span>}
                      {entry.datum_von && <span>📅 {entry.datum_von}</span>}
                      {entry.kategorie && <span className="admin-card-tag">{entry.kategorie}</span>}
                      {entry.veranstalter && <span>👤 {entry.veranstalter}</span>}
                    </div>
                    {entry.beschreibung && (
                      <p class="admin-card-desc">{entry.beschreibung.substring(0, 200)}{entry.beschreibung.length > 200 ? '…' : ''}</p>
                    )}
                    <div class="admin-card-details">
                      {entry.uhrzeit && <span>🕐 {entry.uhrzeit}</span>}
                      {entry.preis && <span>💰 {entry.preis}</span>}
                      {entry.webseite && <span>🌐 <a href={entry.webseite} target="_blank" rel="noopener">{entry.webseite.substring(0, 40)}</a></span>}
                      {entry.email && <span>✉️ {entry.email}</span>}
                      {entry.erstelltAm && <span>🕐 {new Date(entry.erstelltAm).toLocaleDateString('de-DE')}</span>}
                    </div>
                  </div>
                </div>
                {isPending && (
                  <div class="admin-card-actions">
                    <button onClick={() => handlePublish(slug, entry)} class="admin-btn admin-btn-publish">
                      ✅ Freigeben
                    </button>
                    <button onClick={() => handleReject(slug)} class="admin-btn admin-btn-reject">
                      ❌ Ablehnen
                    </button>
                  </div>
                )}
                {!isPending && (
                  <div class="admin-card-badge">✅ Freigegeben</div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <style>{`
        .admin-login{max-width:400px;margin:60px auto;text-align:center}
        .admin-login-box{padding:40px;background:var(--surface);border:1px solid var(--glass-border);border-radius:var(--radius-lg)}
        .admin-login-box h3{font-family:var(--font-display);font-size:22px;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px}
        .admin-login-box p{font-size:13px;color:var(--text2);margin-bottom:24px}
        .admin-pw-row{display:flex;gap:8px;max-width:300px;margin:0 auto}
        .admin-pw-input{flex:1;padding:10px 14px;border:1px solid var(--glass-border);border-radius:var(--radius-sm);background:var(--bg);color:var(--text);font-size:14px;text-align:center}
        .admin-pw-input:focus{outline:none;border-color:var(--pink)}
        .admin-pw-btn{padding:10px 20px;background:var(--pink);color:#fff;border:none;border-radius:var(--radius-sm);font-weight:700;cursor:pointer;white-space:nowrap}
        .admin-pw-error{color:var(--pink);font-size:13px;margin-top:12px}

        .admin-dash-header{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;margin-bottom:24px}
        .admin-stats{display:flex;gap:24px}
        .admin-stat{text-align:center}
        .admin-stat-num{font-family:var(--font-display);font-size:36px;color:var(--pink);display:block;line-height:1}
        .admin-stat-label{font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:.5px}
        .admin-actions{display:flex;gap:8px}
        .admin-btn{padding:10px 20px;border-radius:100px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;border:1px solid var(--glass-border);background:var(--surface);color:var(--text);cursor:pointer;transition:all .2s;white-space:nowrap}
        .admin-btn:hover{border-color:var(--pink)}
        .admin-btn-refresh{background:var(--surface)}

        .admin-tabs{display:flex;gap:4px;margin-bottom:24px;background:var(--surface);border:1px solid var(--glass-border);border-radius:100px;padding:4px;width:fit-content}
        .admin-tab{padding:6px 18px;border:none;border-radius:100px;font-size:12px;font-weight:600;background:transparent;color:var(--text3);cursor:pointer;transition:all .2s}
        .admin-tab.active{background:var(--pink);color:#fff}

        .admin-loading{text-align:center;padding:60px 0;color:var(--text3)}
        .admin-empty{text-align:center;padding:60px 0}
        .admin-empty h3{font-size:22px;margin-bottom:8px}
        .admin-empty p{color:var(--text2);font-size:14px}

        .admin-list{display:flex;flex-direction:column;gap:12px}
        .admin-card{display:flex;justify-content:space-between;align-items:flex-start;padding:20px 24px;background:var(--bg);border:1px solid var(--glass-border);border-radius:var(--radius);gap:16px;transition:all .2s}
        .admin-card-approved{opacity:.6;border-color:rgba(16,185,129,.3)}
        .admin-card-left{display:flex;gap:16px;flex:1;min-width:0}
        .admin-card-emoji{font-size:32px;flex-shrink:0;margin-top:4px}
        .admin-card-info{min-width:0}
        .admin-card-title{font-family:var(--font-display);font-size:18px;letter-spacing:.5px;margin-bottom:4px}
        .admin-card-meta{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px}
        .admin-card-meta span{font-size:11px;color:var(--text3)}
        .admin-card-tag{display:inline-block;padding:2px 10px;border-radius:100px;font-size:9px;font-weight:700;background:rgba(255,20,147,.1);color:var(--pink);text-transform:uppercase}
        .admin-card-desc{font-size:13px;color:var(--text2);line-height:1.5;margin-bottom:8px}
        .admin-card-details{display:flex;flex-wrap:wrap;gap:8px;font-size:11px;color:var(--text3)}
        .admin-card-details a{color:var(--pink);text-decoration:none}
        .admin-card-actions{display:flex;flex-direction:column;gap:6px;flex-shrink:0}
        .admin-btn-publish{background:rgba(16,185,129,.1);border-color:rgba(16,185,129,.3);color:rgb(16,185,129)}
        .admin-btn-publish:hover{background:rgba(16,185,129,.2);border-color:rgb(16,185,129)}
        .admin-btn-reject{background:rgba(239,68,68,.1);border-color:rgba(239,68,68,.3);color:rgb(239,68,68)}
        .admin-btn-reject:hover{background:rgba(239,68,68,.2);border-color:rgb(239,68,68)}
        .admin-card-badge{padding:6px 16px;border-radius:100px;font-size:11px;font-weight:700;background:rgba(16,185,129,.1);color:rgb(16,185,129);flex-shrink:0;margin-top:4px}
        .admin-notification{position:fixed;top:24px;left:50%;transform:translateX(-50%);padding:12px 24px;border-radius:var(--radius);font-size:14px;font-weight:600;z-index:9999;box-shadow:0 8px 32px rgba(0,0,0,.15)}
        .admin-notification-success{background:rgba(16,185,129,.95);color:#fff}
        .admin-notification-error{background:rgba(239,68,68,.95);color:#fff}
        @media(max-width:600px){
          .admin-card{flex-direction:column}
          .admin-card-actions{flex-direction:row;width:100%}
          .admin-btn-publish,.admin-btn-reject{flex:1}
          .admin-dash-header{flex-direction:column;align-items:stretch}
          .admin-stats{justify-content:space-around}
          .admin-tabs{width:100%}
          .admin-tab{flex:1;text-align:center}
        }
      `}</style>
    </div>
  );
}
