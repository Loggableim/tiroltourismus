// MerklistePage.tsx — Client-seitige React-Komponente für die Merkliste-Seite
// Liest Favoriten aus dem LocalStorage und zeigt sie als interaktive Karten an.

import React, { useState, useEffect, useCallback } from 'react';

interface FavoriteItem {
  id: string;
  collection: string;
  slug: string;
  name: string;
  emoji?: string;
  ort?: string;
  color?: string;
}

const COLLECTION_META: Record<string, { label: string; link: string; defaultEmoji: string; color: string }> = {
  unterkuenfte: { label: 'Unterkunft', link: '/unterkuenfte/', defaultEmoji: '🏨', color: '#FF1493' },
  gastro: { label: 'Gastro', link: '/gastro/', defaultEmoji: '🍽️', color: '#FF6B35' },
  orte: { label: 'Ort', link: '/orte/', defaultEmoji: '🏘️', color: '#FF1493' },
  regionen: { label: 'Region', link: '/regionen/', defaultEmoji: '🏔️', color: '#FF1493' },
  sehenswuerdigkeiten: { label: 'Sehenswürdigkeit', link: '/sehenswuerdigkeiten/', defaultEmoji: '🏛️', color: '#8B5CF6' },
  erlebnisse: { label: 'Erlebnis', link: '/erlebnisse/', defaultEmoji: '🏔️', color: '#C8102E' },
  events: { label: 'Event', link: '/events/', defaultEmoji: '🎪', color: '#FF1493' },
  magazin: { label: 'Magazin', link: '/magazin/', defaultEmoji: '📰', color: '#FF1493' },
};

export default function MerklistePage() {
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadFavorites = useCallback(() => {
    try {
      const raw = localStorage.getItem('tirol_favorites');
      const items: FavoriteItem[] = raw ? JSON.parse(raw) : [];
      setFavorites(items);
    } catch {
      setFavorites([]);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadFavorites();

    const handleChange = () => loadFavorites();
    window.addEventListener('favorites-changed', handleChange);
    return () => window.removeEventListener('favorites-changed', handleChange);
  }, [loadFavorites]);

  const removeFavorite = (id: string) => {
    const updated = favorites.filter((f) => f.id !== id);
    localStorage.setItem('tirol_favorites', JSON.stringify(updated));
    setFavorites(updated);
    window.dispatchEvent(new CustomEvent('favorites-changed', { detail: { favorites: updated } }));
  };

  const clearAll = () => {
    localStorage.setItem('tirol_favorites', JSON.stringify([]));
    setFavorites([]);
    window.dispatchEvent(new CustomEvent('favorites-changed', { detail: { favorites: [] } }));
  };

  if (loading) {
    return <div className="merkliste-loading">Lade Merkliste…</div>;
  }

  if (favorites.length === 0) {
    return (
      <div className="merkliste-empty">
        <div className="merkliste-empty-icon">💔</div>
        <h2 className="merkliste-empty-title">Deine Merkliste ist leer</h2>
        <p className="merkliste-empty-text">
          Markiere Unterkünfte, Erlebnisse, Events, Sehenswürdigkeiten und mehr
          als Favorit – sie erscheinen dann hier.
        </p>
        <a href="/" className="btn btn-pink">
          Entdecken →
        </a>
      </div>
    );
  }

  // Group favorites by collection type
  const grouped: Record<string, FavoriteItem[]> = {};
  for (const fav of favorites) {
    const group = fav.collection || 'sonstiges';
    if (!grouped[group]) grouped[group] = [];
    grouped[group].push(fav);
  }

  const order = ['unterkuenfte', 'erlebnisse', 'events', 'sehenswuerdigkeiten', 'gastro', 'orte', 'regionen', 'magazin'];

  return (
    <div className="merkliste-page">
      <div className="merkliste-header">
        <span className="merkliste-count">
          ❤️ <strong>{favorites.length}</strong> {favorites.length === 1 ? 'Eintrag' : 'Einträge'}
        </span>
        <button className="merkliste-clear" onClick={clearAll} title="Alle entfernen">
          🗑️ Alle löschen
        </button>
      </div>

      {order.map((group) => {
        if (!grouped[group]) return null;
        const meta = COLLECTION_META[group] || {
          label: group,
          link: `/${group}/`,
          defaultEmoji: '⭐',
          color: 'var(--tirol-pink)',
        };
        return (
          <div key={group} className="merkliste-group">
            <h3 className="merkliste-group-title">
              <a href={meta.link}>{meta.defaultEmoji} {meta.label}</a>
              <span className="merkliste-group-count">{grouped[group].length}</span>
            </h3>
            <div className="merkliste-grid">
              {grouped[group].map((fav) => {
                const meta = COLLECTION_META[fav.collection] || COLLECTION_META['unterkuenfte'];
                const emoji = fav.emoji || meta.defaultEmoji;
                const url = `${meta.link}${fav.slug}/`;
                return (
                  <div key={fav.id} className="merkliste-card">
                    <a href={url} className="merkliste-card-link">
                      <div className="merkliste-card-emoji">{emoji}</div>
                      <div className="merkliste-card-body">
                        <div className="merkliste-card-label">{meta.label}</div>
                        <div className="merkliste-card-name">{fav.name}</div>
                        {fav.ort && <div className="merkliste-card-ort">📍 {fav.ort}</div>}
                      </div>
                    </a>
                    <button
                      className="merkliste-card-remove"
                      onClick={() => removeFavorite(fav.id)}
                      aria-label={`${fav.name} von Merkliste entfernen`}
                      title="Entfernen"
                    >
                      ✕
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
