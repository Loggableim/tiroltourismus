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

// Lokalisierte Texte für die Merkliste
const T: Record<string, any> = {
  de: { loading: 'Lade Merkliste…', emptyTitle: 'Deine Merkliste ist leer', emptyText: 'Markiere Unterkünfte, Erlebnisse, Events, Sehenswürdigkeiten und mehr als Favorit – sie erscheinen dann hier.', discover: 'Entdecken →', clearAll: 'Alle löschen', clearTitle: 'Alle entfernen', entry: 'Eintrag', entries: 'Einträge', remove: 'Entfernen', removeAria: 'von Merkliste entfernen' },
  en: { loading: 'Loading wishlist…', emptyTitle: 'Your wishlist is empty', emptyText: 'Mark accommodations, experiences, events, sights and more as favorites – they will appear here.', discover: 'Discover →', clearAll: 'Clear all', clearTitle: 'Remove all', entry: 'entry', entries: 'entries', remove: 'Remove', removeAria: 'remove from wishlist' },
  fr: { loading: 'Chargement des favoris…', emptyTitle: 'Votre liste de favoris est vide', emptyText: 'Marquez des hébergements, expériences, événements, sites et plus comme favoris – ils apparaîtront ici.', discover: 'Découvrir →', clearAll: 'Tout effacer', clearTitle: 'Tout supprimer', entry: 'entrée', entries: 'entrées', remove: 'Supprimer', removeAria: 'retirer des favoris' },
  cs: { loading: 'Načítání seznamu…', emptyTitle: 'Váš seznam je prázdný', emptyText: 'Označte ubytování, zážitky, akce, pamětihodnosti a další jako oblíbené – objeví se zde.', discover: 'Objevit →', clearAll: 'Vymazat vše', clearTitle: 'Odebrat vše', entry: 'záznam', entries: 'záznamů', remove: 'Odebrat', removeAria: 'odebrat ze seznamu' },
  nl: { loading: 'Verlanglijst laden…', emptyTitle: 'Je verlanglijst is leeg', emptyText: 'Markeer accommodaties, ervaringen, evenementen, bezienswaardigheden en meer als favoriet – ze verschijnen hier.', discover: 'Ontdekken →', clearAll: 'Alles wissen', clearTitle: 'Alles verwijderen', entry: 'item', entries: 'items', remove: 'Verwijderen', removeAria: 'van verlanglijst verwijderen' },
  it: { loading: 'Caricamento preferiti…', emptyTitle: 'La tua lista è vuota', emptyText: 'Contrassegna alloggi, esperienze, eventi, attrazioni e altro come preferiti – appariranno qui.', discover: 'Scoprire →', clearAll: 'Cancella tutto', clearTitle: 'Rimuovi tutto', entry: 'voce', entries: 'voci', remove: 'Rimuovi', removeAria: 'rimuovi dai preferiti' },
  es: { loading: 'Cargando favoritos…', emptyTitle: 'Tu lista está vacía', emptyText: 'Marca alojamientos, experiencias, eventos, atracciones y más como favoritos – aparecerán aquí.', discover: 'Descubrir →', clearAll: 'Borrar todo', clearTitle: 'Eliminar todo', entry: 'entrada', entries: 'entradas', remove: 'Eliminar', removeAria: 'eliminar de favoritos' },
  zh: { loading: '加载收藏夹…', emptyTitle: '您的收藏夹是空的', emptyText: '将住宿、体验、活动、景点等标记为收藏 – 它们将显示在这里。', discover: '探索 →', clearAll: '全部清除', clearTitle: '全部移除', entry: '条目', entries: '条目', remove: '移除', removeAria: '从收藏夹移除' },
};

export default function MerklistePage({ locale = 'de' }: { locale?: string }) {
  const t = T[locale] || T.de;
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
    return <div className="merkliste-loading">{t.loading}</div>;
  }

  if (favorites.length === 0) {
    return (
      <div className="merkliste-empty">
        <div className="merkliste-empty-icon">💔</div>
        <h2 className="merkliste-empty-title">{t.emptyTitle}</h2>
        <p className="merkliste-empty-text">
          {t.emptyText}
        </p>
        <a href="/" className="btn btn-pink">
          {t.discover}
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
          ❤️ <strong>{favorites.length}</strong> {favorites.length === 1 ? t.entry : t.entries}
        </span>
        <button className="merkliste-clear" onClick={clearAll} title={t.clearTitle}>
          🗑️ {t.clearAll}
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
                      aria-label={`${fav.name} ${t.removeAria}`}
                      title={t.remove}
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
