/**
 * richtext.js — defensives Rendering für Text-/HTML-Felder aus den JSON-Daten.
 *
 * Einige übersetzte Felder enthalten versehentlich Markdown/Roh-HTML (z.B. <p>,
 * <strong>, <h2>) oder HTML-Entities (&lt;p&gt;). Wird ein solches Feld als
 * Titel/Fließtext mit `{feld}` gerendert, escaped Astro die Tags und sie werden
 * als sichtbarer Text ausgegeben. Diese Helfer normalisieren das:
 *
 *   plainText(value)  → Tags + Entities entfernt, für Headings/Titel/Breadcrumbs
 *   richText(value)   → erlaubte Tags erhalten, Rest sicher escaped/entfernt
 *
 * richText wird mit `set:html` ausgegeben.
 */

const ALLOWED_TAGS = new Set([
  'p', 'strong', 'em', 'a', 'ul', 'ol', 'li', 'h2', 'h3', 'br',
]);

const NAMED_ENTITIES = {
  amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ',
  copy: '©', reg: '®', hellip: '…', mdash: '—', ndash: '–',
  rsquo: '’', lsquo: '‘', ldquo: '“', rdquo: '”', euro: '€',
  deg: '°', szlig: 'ß', auml: 'ä', ouml: 'ö', uuml: 'ü',
  Auml: 'Ä', Ouml: 'Ö', Uuml: 'Ü',
};

/** Dekodiert die wichtigsten benannten und numerischen HTML-Entities. */
export function decodeHtmlEntities(value) {
  const s = String(value ?? '');
  if (!s.includes('&')) return s;
  return s.replace(/&(#x?[0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]*);/g, (match, entity) => {
    if (entity[0] === '#') {
      const hex = entity[1] === 'x' || entity[1] === 'X';
      const code = hex ? parseInt(entity.slice(2), 16) : parseInt(entity.slice(1), 10);
      if (!Number.isNaN(code)) {
        try { return String.fromCodePoint(code); } catch { return match; }
      }
      return match;
    }
    return NAMED_ENTITIES[entity] ?? NAMED_ENTITIES[entity.toLowerCase()] ?? match;
  });
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/** Entfernt alle Tags (roh oder escaped) und normalisiert Whitespace. */
export function plainText(value) {
  if (value === null || value === undefined) return '';
  return decodeHtmlEntities(value)
    .replace(/<[^>]*>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function sanitizeTag(tagRaw) {
  const match = tagRaw.match(/^<(\/)?\s*([a-zA-Z0-9]+)([\s\S]*?)(\/)?>$/);
  if (!match) return ' ';
  const closing = Boolean(match[1]);
  const tag = String(match[2]).toLowerCase();
  const attrs = match[3] || '';
  if (!ALLOWED_TAGS.has(tag)) return ' ';
  if (tag === 'br') return '<br>';
  if (tag !== 'a' || closing) return closing ? `</${tag}>` : `<${tag}>`;

  const hrefMatch = attrs.match(/href\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/i);
  let href = hrefMatch ? (hrefMatch[1] ?? hrefMatch[2] ?? hrefMatch[3] ?? '') : '';
  if (/^\s*(javascript:|data:)/i.test(href)) href = '';
  const safeHref = escapeHtml(href.trim());
  return safeHref ? `<a href="${safeHref}">` : '<a>';
}

/**
 * Wenn ein Feld HTML enthält (roh oder escaped), wird es dekodiert und auf eine
 * kleine Whitelist beschränkt. Sonst wird reiner Text escaped zurückgegeben.
 * Ergebnis ist für `set:html` gedacht.
 */
export function richText(value) {
  if (value === null || value === undefined) return '';
  const decoded = decodeHtmlEntities(value);
  const hasHtml = /<\/?\s*[a-zA-Z][^>]*>/.test(decoded) || /<\s*[a-zA-Z][^>]*>/.test(String(value));
  if (!hasHtml) return escapeHtml(String(value).trim());

  const withoutBlocks = decoded
    .replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi, ' ')
    .replace(/<!--[\s\S]*?-->/g, ' ');

  const sanitized = withoutBlocks.replace(/<[^>]+>/g, (tag) => sanitizeTag(tag));
  return sanitized.replace(/[ \t]{2,}/g, ' ').trim();
}

/** Wahr, wenn ein Feld sichtbares Roh- oder escaped HTML enthält. */
export function looksLikeHtml(value) {
  if (value === null || value === undefined) return false;
  const s = String(value);
  return /<\/?\s*[a-zA-Z][^>]*>/.test(s) || /&lt;\s*\/?\s*[a-zA-Z]/.test(s);
}
