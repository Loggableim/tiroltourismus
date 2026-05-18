/**
 * LeafletMap.jsx — Enhanced OpenStreetMap component with:
 * - Single/multi markers with category emoji/colors
 * - Region polygon overlay (GeoJSON)
 * - Dark/Light tile switching
 * - Auto-fit bounds
 * - Marker clustering (12+ markers)
 * - Polygon hover glow/tooltip
 * - Responsive height
 * - Loading skeleton
 */
import { useEffect, useRef, useState } from 'react';

const TILES = {
  light: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
  dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
};

const TIROL_CENTER = { lat: 47.15, lng: 11.4 };

const CATEGORY_STYLES = {
  sehenswuerdigkeiten: { emoji: '🏛️', color: '#6B7280', bg: 'rgba(107,114,128,0.15)' },
  gastro:             { emoji: '🍽️', color: '#F59E0B', bg: 'rgba(245,158,11,0.15)' },
  unterkuenfte:       { emoji: '🏨', color: '#3B82F6', bg: 'rgba(59,130,246,0.15)' },
  camping:            { emoji: '🏕️', color: '#10B981', bg: 'rgba(16,185,129,0.15)' },
  erlebnisse:         { emoji: '🎯', color: '#EC4899', bg: 'rgba(236,72,153,0.15)' },
  orte:               { emoji: '🏘️', color: '#8B5CF6', bg: 'rgba(139,92,246,0.15)' },
  events:             { emoji: '🎪', color: '#F97316', bg: 'rgba(249,115,22,0.15)' },
  regionen:           { emoji: '🏔️', color: '#14B8A6', bg: 'rgba(20,184,166,0.15)' },
};

function getTheme() {
  if (typeof document === 'undefined') return 'light';
  return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
}

export default function LeafletMap({
  markers = [],
  center,
  zoom,
  height = '400px',
  scrollWheelZoom = false,
  polygons = [],  // { coords: [[lat,lng],...], label, color, fillOpacity }
  filterable = false,  // show category filter bar
}) {
  const mapContainer = useRef(null);
  const mapInstance = useRef(null);
  const polygonsRef = useRef([]);
  const markersRef = useRef([]);
  const markerClusterRef = useRef(null);
  const [theme, setTheme] = useState('light');
  const [loading, setLoading] = useState(true);
  const [activeFilters, setActiveFilters] = useState(new Set());

  // Theme detection via MutationObserver
  useEffect(() => {
    setTheme(getTheme());
    const observer = new MutationObserver(() => setTheme(getTheme()));
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);

  // Main map initialization
  useEffect(() => {
    if (!mapContainer.current || typeof window === 'undefined') return;

    import('leaflet').then((L) => {
      if (mapInstance.current) return;

      // Load Leaflet CSS
      if (!document.getElementById('leaflet-css')) {
        const link = document.createElement('link');
        link.id = 'leaflet-css';
        link.rel = 'stylesheet';
        link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
        document.head.appendChild(link);
      }

      // Fix default icon paths
      delete (L.Icon.Default.prototype)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      });

      const activeTheme = getTheme();
      const map = L.map(mapContainer.current, {
        center: center ? [center.lat, center.lng] : [TIROL_CENTER.lat, TIROL_CENTER.lng],
        zoom: zoom || (markers.length > 1 ? 8 : 13),
        scrollWheelZoom,
        zoomControl: true,
        attributionControl: true,
      });

      mapInstance.current = map;
      setLoading(false);

      // Tile layer
      const tiles = L.tileLayer(activeTheme === 'dark' ? TILES.dark : TILES.light, {
        attribution: TILES.attribution,
        maxZoom: 19,
      }).addTo(map);

      // Store tiles ref for theme switching
      map._tileLayer = tiles;

      // Draw polygons
      drawPolygons(L, map);

      // Draw markers
      drawMarkers(L, map);

      // Fit bounds
      fitBounds(map);
    });

    return () => {
      if (mapInstance.current) {
        mapInstance.current.remove();
        mapInstance.current = null;
      }
    };
  }, []); // Run once

  // Re-draw markers when markers prop changes
  useEffect(() => {
    if (!mapInstance.current) return;
    import('leaflet').then((L) => {
      const map = mapInstance.current;
      clearMarkers(map);
      drawMarkers(L, map);
      fitBounds(map);
    });
  }, [markers, polygons]);

  // Switch tiles on theme change
  useEffect(() => {
    if (!mapInstance.current) return;
    const map = mapInstance.current;
    if (map._tileLayer) {
      map._tileLayer.setUrl(theme === 'dark' ? TILES.dark : TILES.light);
    }
  }, [theme]);

  // ── Helpers ──

  function drawPolygons(L, map) {
    // Clear existing
    polygonsRef.current.forEach(p => map.removeLayer(p));
    polygonsRef.current = [];

    if (!polygons || polygons.length === 0) return;

    polygons.forEach((poly) => {
      if (!poly.coords || poly.coords.length < 3) return;

      // Convert [[lat,lng],...] to Leaflet latlngs
      const latlngs = poly.coords.map(c => [parseFloat(c[0]), parseFloat(c[1])]);
      const color = poly.color || 'var(--pink, #FF1493)';

      const polygon = L.polygon(latlngs, {
        color: color,
        weight: 2,
        opacity: 0.8,
        fillColor: color,
        fillOpacity: poly.fillOpacity || 0.12,
        smoothFactor: 1,
      }).addTo(map);

      // Hover effects
      polygon.on('mouseover', function () {
        this.setStyle({ fillOpacity: 0.25, weight: 3, opacity: 1 });
        if (poly.label) {
          this.bindTooltip(poly.label, {
            permanent: false,
            direction: 'center',
            className: 'map-polygon-tooltip',
            offset: [0, 0],
          }).openTooltip();
        }
      });

      polygon.on('mouseout', function () {
        this.setStyle({ fillOpacity: poly.fillOpacity || 0.12, weight: 2, opacity: 0.8 });
        this.unbindTooltip();
      });

      polygonsRef.current.push(polygon);
    });
  }

  function drawMarkers(L, map) {
    if (!markers || markers.length === 0) return;
    const markerBounds = [];
    const useClustering = markers.length > 12;

    if (useClustering) {
      // Grid-based spatial clustering
      const gridSize = 0.04; // ~4km at Tirol latitude
      const grid = new Map();

      markers.forEach((m, idx) => {
        if (!m.lat || !m.lng) return;
        const lat = parseFloat(m.lat);
        const lng = parseFloat(m.lng);
        const gx = Math.round(lat / gridSize);
        const gy = Math.round(lng / gridSize);
        const key = gx + ':' + gy;

        if (!grid.has(key)) grid.set(key, []);
        grid.get(key).push({ ...m, lat, lng, idx });
      });

      grid.forEach((group) => {
        const centerLat = group.reduce((a, g) => a + g.lat, 0) / group.length;
        const centerLng = group.reduce((a, g) => a + g.lng, 0) / group.length;
        markerBounds.push([centerLat, centerLng]);

        // Check if any marker in group passes filter
        const cat = group[0].category;
        if (activeFilters.size > 0 && cat && !activeFilters.has(cat)) return;

        if (group.length === 1) {
          // Single marker
          const m = group[0];
          const catStyle = m.category ? CATEGORY_STYLES[m.category] : null;
          const iconColor = m.color || catStyle?.color || 'var(--pink, #FF1493)';
          const markerEmoji = m.emoji || catStyle?.emoji || '📍';
          const icon = L.divIcon({
            html: `<div style="font-size:20px;width:34px;height:34px;display:flex;align-items:center;justify-content:center;background:${iconColor};border-radius:50%;box-shadow:0 2px 8px rgba(0,0,0,.3);border:2px solid #fff;cursor:pointer">${markerEmoji}</div>`,
            className: '', iconSize: [34, 34], iconAnchor: [17, 17],
          });
          const marker = L.marker([centerLat, centerLng], { icon }).addTo(map);
          if (m.label) {
            marker.bindPopup(m.href
              ? `<a href="${m.href}" style="font-weight:600;color:${iconColor};text-decoration:none">${m.label}</a><br><a href="https://www.google.com/maps/dir/?api=1&destination=${centerLat},${centerLng}&travelmode=driving" target="_blank" rel="noopener" style="font-size:11px;color:#666;text-decoration:none">📍 Route planen ↗</a>`
              : `<strong>${m.label}</strong><br><a href="https://www.google.com/maps/dir/?api=1&destination=${centerLat},${centerLng}&travelmode=driving" target="_blank" rel="noopener" style="font-size:11px;color:#666;text-decoration:none">📍 Route planen ↗</a>`);
          }
          markersRef.current.push(marker);
        } else {
          // Cluster
          const count = group.length;
          const clusterColor = '#a855f7';
          const icon = L.divIcon({
            html: `<div style="width:44px;height:44px;display:flex;align-items:center;justify-content:center;background:${clusterColor};border-radius:50%;box-shadow:0 2px 12px rgba(168,85,247,.4);border:3px solid #fff;color:#fff;font-size:13px;font-weight:700;cursor:pointer">${count}</div>`,
            className: '', iconSize: [44, 44], iconAnchor: [22, 22],
          });
          const cluster = L.marker([centerLat, centerLng], { icon }).addTo(map);
          cluster.bindPopup(`<strong>${count} Orte</strong><br><em>Zoom rein zum Erkunden</em>`);
          cluster.on('click', () => {
            map.fitBounds(group.map(g => [g.lat, g.lng]), { padding: [40, 40], maxZoom: 14 });
          });
          markersRef.current.push(cluster);
        }
      });
    } else {
      // Direct markers for small sets
      markers.forEach((m) => {
        if (!m.lat || !m.lng) return;
        const latlng = [parseFloat(m.lat), parseFloat(m.lng)];
        markerBounds.push(latlng);
        const catStyle = m.category ? CATEGORY_STYLES[m.category] : null;
        const iconColor = m.color || catStyle?.color || 'var(--pink, #FF1493)';
        const markerEmoji = m.emoji || catStyle?.emoji || '📍';
        const icon = L.divIcon({
          html: `<div style="font-size:22px;width:36px;height:36px;display:flex;align-items:center;justify-content:center;background:${iconColor};border-radius:50%;box-shadow:0 2px 8px rgba(0,0,0,.3);border:2px solid #fff;transition:transform .2s ease;cursor:pointer">${markerEmoji}</div>`,
          className: '', iconSize: [36, 36], iconAnchor: [18, 18],
        });
        const marker = L.marker(latlng, { icon }).addTo(map);
        if (m.label) {
          marker.bindPopup(m.href
            ? `<a href="${m.href}" style="font-weight:600;color:${iconColor};text-decoration:none">${m.label}</a><br><a href="https://www.google.com/maps/dir/?api=1&destination=${m.lat},${m.lng}&travelmode=driving" target="_blank" rel="noopener" style="font-size:11px;color:#666;text-decoration:none">📍 Route planen ↗</a>`
            : `<strong>${m.label}</strong><br><a href="https://www.google.com/maps/dir/?api=1&destination=${m.lat},${m.lng}&travelmode=driving" target="_blank" rel="noopener" style="font-size:11px;color:#666;text-decoration:none">📍 Route planen ↗</a>`);
        }
        markersRef.current.push(marker);
      });
    }

    // Auto-fit bounds
    if (markerBounds.length > 1) {
      map.fitBounds(markerBounds, { padding: [40, 40], maxZoom: 10 });
    }
  }

  function clearMarkers(map) {
    markersRef.current.forEach(m => map.removeLayer(m));
    markersRef.current = [];
  }

  function fitBounds(map) {
    const allBounds = [];

    // Marker bounds
    markersRef.current.forEach(m => {
      if (m.getLatLng()) allBounds.push(m.getLatLng());
    });

    // Polygon bounds
    polygonsRef.current.forEach(p => {
      const b = p.getBounds();
      if (b.isValid()) allBounds.push(b.getNorthWest(), b.getSouthEast());
    });

    if (allBounds.length > 1) {
      map.fitBounds(allBounds, { padding: [40, 40], maxZoom: 12 });
    } else if (allBounds.length === 1) {
      map.setView(allBounds[0], zoom || 13);
    }
  }

  // Responsive height
  const [respH, setRespH] = useState(height);
  useEffect(() => {
    const u = () => setRespH(window.innerWidth <= 600 ? '250px' : height);
    u(); window.addEventListener('resize', u);
    return () => window.removeEventListener('resize', u);
  }, [height]);

  // Category filter
  const cats = filterable ? [...new Set(markers.map(m => m.category).filter(Boolean))] : [];
  const toggleFilter = (c) => {
    setActiveFilters(p => { const n = new Set(p); n.has(c) ? n.delete(c) : n.add(c); return n; });
  };
  // Re-draw markers on filter change
  useEffect(() => {
    if (!mapInstance.current) return;
    import('leaflet').then(L => {
      clearMarkers(mapInstance.current);
      drawMarkers(L, mapInstance.current);
      fitBounds(mapInstance.current);
    });
  }, [activeFilters]);

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      {/* Category filter bar */}
      {cats.length > 1 && (
        <div style={{
          display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '12px',
          justifyContent: 'center',
        }}>
          {cats.map(cat => {
            const style = CATEGORY_STYLES[cat] || { emoji: '📍', color: '#999' };
            const isActive = activeFilters.size === 0 || activeFilters.has(cat);
            return (
              <button key={cat} onClick={() => toggleFilter(cat)}
                style={{
                  padding: '6px 14px', borderRadius: '100px', border: '1px solid ' + (isActive ? style.color : 'var(--glass-border, #ddd)'),
                  background: isActive ? style.color + '22' : 'transparent',
                  color: isActive ? style.color : 'var(--text3, #999)',
                  cursor: 'pointer', fontSize: '12px', fontWeight: 600,
                  transition: 'all .2s ease',
                }}>
                {style.emoji} {cat}
              </button>
            );
          })}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div style={{
          width: '100%', height: respH,
          borderRadius: 'var(--radius, 12px)',
          background: 'linear-gradient(90deg, var(--bg2, #f0f0f0) 25%, var(--surface, #e0e0e0) 50%, var(--bg2, #f0f0f0) 75%)',
          backgroundSize: '200% 100%',
          animation: 'mapSkeleton 1.5s ease-in-out infinite',
          border: '1px solid var(--glass-border, rgba(0,0,0,.06))',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--text3, #aaa)', fontSize: '14px',
        }}>
          <span>🗺️ Karte wird geladen…</span>
        </div>
      )}
      <div
        ref={mapContainer}
        style={{
          width: '100%', height: respH,
          borderRadius: 'var(--radius, 12px)',
          overflow: 'hidden',
          border: '1px solid var(--glass-border, rgba(0,0,0,.06))',
          boxShadow: '0 4px 24px rgba(0,0,0,.08)',
          display: loading ? 'none' : 'block',
          transition: 'height .3s ease',
        }}
      />
      <style>{`
        @keyframes mapSkeleton {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
        .map-polygon-tooltip {
          background: rgba(0,0,0,.8) !important;
          color: #fff !important;
          border: none !important;
          border-radius: 8px !important;
          padding: 6px 14px !important;
          font-size: 13px !important;
          font-weight: 600 !important;
          box-shadow: 0 4px 12px rgba(0,0,0,.3) !important;
        }
        .map-polygon-tooltip::before {
          border-top-color: rgba(0,0,0,.8) !important;
        }
        .leaflet-popup-content-wrapper {
          border-radius: 10px !important;
          font-family: inherit !important;
        }
        .leaflet-popup-content { margin: 10px 14px !important; }
        @media (max-width: 600px) {
          .leaflet-popup-content { margin: 8px 10px !important; font-size: 13px; }
        }
      `}</style>
    </div>
  );
}
