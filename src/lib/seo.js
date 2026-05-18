/**
 * seo.js — SEO Meta Description Generator
 * Erzeugt 120–160 Zeichen lange Meta Descriptions mit
 * Keyword-vorne + CTA für alle Collection-Typen.
 *
 * Nutzung:
 *   import { generateMetaDescription } from '../lib/seo.js';
 *   description={generateMetaDescription(entry, 'camping')}
 */

/**
 * Stripped HTML-Tags aus einem String
 */
function stripHtml(html) {
  if (!html) return '';
  return html
    .replace(/<[^>]+>/g, ' ')    // Tags entfernen
    .replace(/&[a-z]+;/g, ' ')   // HTML-Entities
    .replace(/\s+/g, ' ')        // Mehrfach-Leerzeichen
    .trim();
}

/**
 * Kürzt Text auf maximal `maxLen` Zeichen,
 * bricht an der letzten natürlichen Satz-/Komma-Grenze.
 */
function truncateText(text, maxLen = 150) {
  if (!text || text.length <= maxLen) return text || '';

  const truncated = text.slice(0, maxLen);
  // Letzte natürliche Grenze finden: . ! ? , — –
  const boundaries = ['.', '!', '?', ',', '–', '—', ';'];
  let cutAt = -1;
  for (const b of boundaries) {
    const idx = truncated.lastIndexOf(b);
    if (idx > Math.floor(maxLen * 0.6) && idx > cutAt) cutAt = idx;
  }
  if (cutAt > 0) return truncated.slice(0, cutAt + 1).trim();
  // Keine schöne Grenze → am letzten Leerzeichen trennen + …
  const lastSpace = truncated.lastIndexOf(' ');
  if (lastSpace > 0) return truncated.slice(0, lastSpace).trim() + ' …';
  return truncated.trim();
}

/**
 * Extrahiert den ersten aussagekräftigen Textabschnitt aus beschreibung HTML.
 * Entfernt Einleitungssätze mit "Der/Die/Das/… liegt/befindet" da die
 * Keyword-vorne-Strategie den Namen bereits nennt.
 */
function extractDescription(htmlText) {
  const text = stripHtml(htmlText);
  if (!text) return '';

  // Versuche Satz 2+ zu nehmen, wenn Satz 1 nur eine schwache Einleitung ist
  const sentences = text.match(/[^.!?]+[.!?]+/g);
  if (sentences && sentences.length >= 2) {
    const first = sentences[0].trim().toLowerCase();
    const weakStart = /^(der|die|das|den|dem|des|ein|eine|einen|einer|eines)\s.*(liegt|befindet|ist|bietet|hat|verfügt|wird)/;
    if (weakStart.test(first)) {
      // Ab dem zweiten Satz nehmen
      const rest = sentences.slice(1).join(' ').trim();
      if (rest.length > 60) return rest;
    }
  }

  return text;
}

/**
 * CTA-Phrasen pro Collection
 */
const CTAS = {
  camping:        '✅ Campingplatz in Tirol – jetzt Plätze sichern!',
  unterkuenfte:   '✅ Jetzt Unterkunft buchen und Tirol erleben!',
  regionen:       '🏔️ Jetzt Reise nach Tirol planen!',
  orte:           '📍 Jetzt Ort entdecken und Ausflug planen!',
  gastro:         '🍽️ Jetzt Tisch reservieren und genießen!',
  sehenswuerdigkeiten: '🏛️ Jetzt Sehenswürdigkeit entdecken!',
  erlebnisse:     '🎯 Jetzt Erlebnis buchen!',
  events:         '🎪 Jetzt Event besuchen – Tickets sichern!',
  magazin:        '📖 Jetzt lesen und inspirieren lassen!',
  bezirke:        '🗺️ Jetzt Bezirk entdecken und Ausflug planen!',
  default:        '✅ Jetzt mehr erfahren!',
};

const CTAS_EN = {
  regionen:       '🏔️ Plan your trip to Tyrol now!',
  default:        '✅ Discover more now!',
};

/**
 * Hauptfunktion: Erzeugt eine SEO-optimierte Meta Description
 *
 * @param {object} entry          - Das CMS-Entry-Objekt
 * @param {string} collection     - Collection-Name (camping, unterkuenfte, …)
 * @param {string} [locale='de']  - 'de' oder 'en'
 * @param {object} [opts]         - Optionale Parameter
 * @param {string} [opts.typLabel] - Typ-Label für unterkuenfte
 * @returns {string}              - 120–160 Zeichen langer Description-Text
 */
export function generateMetaDescription(entry, collection, locale = 'de', opts = {}) {
  if (!entry) return '';

  const name = entry.name || entry.titel || '';
  const ort = entry.ort || '';
  const cta = locale === 'en' ? (CTAS_EN[collection] || CTAS_EN.default) : (CTAS[collection] || CTAS.default);
  const isDE = locale === 'de';

  /**
   * Helper: Baut finalen String aus Main-Keyword + Body + CTA
   * und kürzt auf 120–160 Zeichen
   */
  function build(keyword, body) {
    let result = keyword;
    let separator = '';
    if (body) {
      // "keyword: body. CTA" oder "keyword – body. CTA"
      separator = body.length > 80 ? ': ' : ' – ';
      result += separator + body;
    }
    // CTA anhängen (wenn Platz)
    const ctaJoined = '. ' + cta;
    const totalWithCTA = result.length + ctaJoined.length;
    if (totalWithCTA <= 160) {
      result += ctaJoined;
    } else if (result.length > 120) {
      // CTA nicht reinpassend, truncate body
      result = keyword + separator + truncateText(body, 120 - keyword.length - separator.length - ctaJoined.length);
      result += ctaJoined;
    } else {
      // result already short, just add CTA
      result += ctaJoined;
    }

    // Final check: sollte zwischen 120–160 liegen
    if (result.length > 160) {
      result = truncateText(result, 157) + '…';
    }
    return result;
  }

  switch (collection) {
    // ─── CAMPING ───────────────────────────────────────────
    case 'camping': {
      // Beschreibung aus CMS extrahieren (HTML strip + intelligenter Satz)
      let body = extractDescription(entry.beschreibung);
      if (!body) {
        body = `Campingplatz in ${ort || 'Tirol'} mit Natur pur, Stellplätzen und Bergpanorama`;
      }
      return build(name, body);
    }

    // ─── UNTERKÜNFTE ───────────────────────────────────────
    case 'unterkuenfte': {
      const typ = opts.typLabel || entry.typ || 'Unterkunft';
      let body = extractDescription(entry.beschreibung);
      if (!body) {
        const sterne = entry.sterne ? `${entry.sterne}-Stern ` : '';
        body = `${sterne}${typ} in ${ort || 'Tirol'} – Komfort & Urlaubsgefühl in den Alpen`;
      }
      return build(name, body);
    }

    // ─── REGIONEN ──────────────────────────────────────────
    case 'regionen': {
      let body = entry.kurzbeschreibung || extractDescription(entry.beschreibung);
      if (body && body.length < 80) {
        body += ` – ${isDE ? 'Wanderwege, Skigebiete & Ausflugsziele' : 'Hiking trails, ski resorts & attractions'}`;
      }
      return build(name, body);
    }

    // ─── ORTE ──────────────────────────────────────────────
    case 'orte': {
      let body = entry.kurzbeschreibung || '';
      if (body && body.length < 60 && entry.region) {
        body += ` – Ausflugsziel in ${entry.region}`;
      }
      if (!body) {
        body = `${isDE ? 'Urlaubsort in Tirol mit Bergpanorama & Naturerlebnissen' : 'Town in Tyrol surrounded by mountains'}`;
      }
      return build(name, body);
    }

    // ─── GASTRO ────────────────────────────────────────────
    case 'gastro': {
      let body = entry.kurzbeschreibung || extractDescription(entry.beschreibung);
      if (!body) {
        const kat = entry.kategorie || 'Kulinarik';
        body = `${isDE ? 'Einkehren & genießen' : 'Dine & enjoy'} in ${ort || 'Tirol'} – ${kat}`;
      }
      return build(name, body);
    }

    // ─── SEHENSWÜRDIGKEITEN ────────────────────────────────
    case 'sehenswuerdigkeiten': {
      let body = entry.kurzbeschreibung || extractDescription(entry.beschreibung);
      if (!body) {
        body = `${isDE ? 'Sehenswürdigkeit' : 'Sight'} in ${ort || 'Tirol'} – ${entry.kategorie || ''}`;
      }
      return build(name, body);
    }

    // ─── ERLEBNISSE ────────────────────────────────────────
    case 'erlebnisse': {
      const kategorieLabel = {
        wandern: 'Wandern', ski: 'Ski & Snowboard', bike: 'Bike & Mountainbike',
        wellness: 'Wellness & Erholung', familie: 'Familie & Kinder',
        kulinarik: 'Kulinarik', kultur: 'Kultur', abenteuer: 'Abenteuer',
      };
      let body = entry.beschreibung || '';
      if (!body) {
        const kat = kategorieLabel[entry.kategorie] || 'Erlebnis';
        body = `${kat} in ${ort || 'Tirol'} – ${isDE ? 'ein unvergessliches Abenteuer' : 'an unforgettable adventure'}`;
      }
      return build(name, body);
    }

    // ─── EVENTS ────────────────────────────────────────────
    case 'events': {
      let body = entry.kurzbeschreibung || entry.beschreibung || '';
      if (!body) {
        body = `Event in ${ort || 'Tirol'} – ${entry.kategorie || 'Veranstaltung'}`;
      }
      return build(name, body);
    }

    // ─── MAGAZIN ───────────────────────────────────────────
    case 'magazin': {
      let body = entry.teaser || '';
      if (!body) {
        body = `${isDE ? 'Spannender Magazinbeitrag' : 'Interesting magazine article'} über ${name}`;
      }
      return build(name, body);
    }

    // ─── BEZIRKE ───────────────────────────────────────────
    case 'bezirke': {
      let body = entry.beschreibung || '';
      if (!body) {
        body = `${isDE ? 'Alle Gemeinden, Regionen & Ausflugsziele' : 'Municipalities, regions & attractions'}`;
      }
      return build(name, body);
    }

    // ─── DEFAULT ───────────────────────────────────────────
    default: {
      const body = entry.kurzbeschreibung || entry.beschreibung || entry.teaser || '';
      return build(name, body);
    }
  }
}
