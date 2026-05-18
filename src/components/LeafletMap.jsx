/**
 * LeafletMap.jsx — React component for OpenStreetMap display via Leaflet.
 * Used with client:only / client:load in Astro pages.
 *
 * Props:
 *  - markers: Array of { lat, lng, label?, href?, emoji?, color? }
 *  - center: { lat, lng } — map center (default: first marker or Tirol center)
 *  - zoom: number (default: 8 for overview, 13 for single)
 *  - height: string (default: '400px')
 *  - scrollWheelZoom: boolean (default: false — true for detail maps)
 */

import { useEffect, useRef, useState } from 'react';

// Dark tile style that matches the AlpenPeak dark theme
const TILES = {
  light: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
  dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
};

const TIROL_CENTER = { lat: 47.15, lng: 11.4 };

function getTheme() {
  if (typeof document === 'undefined') return 'light';
  return document.documentElement.getAttribute('data-theme') === 'alpenpeak' ? 'dark' : 'light';
}

export default function LeafletMap({
  markers = [],
  center,
  zoom,
  height = '400px',
  scrollWheelZoom = false,
}) {
  const mapContainer = useRef(null);
  const mapInstance = useRef(null);
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    // Detect initial theme
    setTheme(getTheme());

    // Listen for theme changes
    const observer = new MutationObserver(() => setTheme(getTheme()));
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!mapContainer.current || typeof window === 'undefined') return;

    // Dynamic import to avoid SSR issues
    import('leaflet').then((L) => {
      // Skip if map already initialized
      if (mapInstance.current) return;

      // Load Leaflet CSS if not already loaded
      if (!document.getElementById('leaflet-css')) {
        const link = document.createElement('link');
        link.id = 'leaflet-css';
        link.rel = 'stylesheet';
        link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
        document.head.appendChild(link);
      }

      // Fix default icon paths for bundlers
      delete (L.Icon.Default.prototype)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      });

      const tileTheme = getTheme();

      const map = L.map(mapContainer.current, {
        center: center ? [center.lat, center.lng] : [TIROL_CENTER.lat, TIROL_CENTER.lng],
        zoom: zoom || (markers.length > 1 ? 8 : 13),
        scrollWheelZoom: scrollWheelZoom,
        zoomControl: true,
        attributionControl: true,
      });

      mapInstance.current = map;

      L.tileLayer(tileTheme === 'dark' ? TILES.dark : TILES.light, {
        attribution: TILES.attribution,
        maxZoom: 19,
      }).addTo(map);

      // Add markers
      if (markers && markers.length > 0) {
        const markerBounds = [];
        markers.forEach((m) => {
          if (!m.lat || !m.lng) return;
          const latlng = [parseFloat(m.lat), parseFloat(m.lng)];
          markerBounds.push(latlng);

          // Custom icon if emoji provided
          let icon;
          if (m.emoji) {
            icon = L.divIcon({
              html: `<div style="
                font-size: 24px;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: ${m.color || 'var(--pink, #FF1493)'};
                border-radius: 50%;
                box-shadow: 0 2px 8px rgba(0,0,0,.25);
                border: 2px solid #fff;
              ">${m.emoji}</div>`,
              className: '',
              iconSize: [40, 40],
              iconAnchor: [20, 20],
            });
          }

          const marker = L.marker(latlng, { icon }).addTo(map);

          if (m.label) {
            const html = m.href
              ? `<a href="${m.href}" style="font-weight:600;color:#FF1493;text-decoration:none">${m.label}</a>`
              : `<strong>${m.label}</strong>`;
            marker.bindPopup(html);
          }
        });

        // Auto-fit bounds for multiple markers
        if (markerBounds.length > 1) {
          map.fitBounds(markerBounds, { padding: [40, 40], maxZoom: 10 });
        }
      }
    });

    return () => {
      if (mapInstance.current) {
        mapInstance.current.remove();
        mapInstance.current = null;
      }
    };
  }, []); // Only run once

  return (
    <div
      ref={mapContainer}
      style={{
        width: '100%',
        height: height,
        borderRadius: 'var(--radius, 12px)',
        overflow: 'hidden',
        border: '1px solid var(--glass-border, rgba(0,0,0,.06))',
      }}
    />
  );
}
