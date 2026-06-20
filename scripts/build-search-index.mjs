/**
 * build-search-index.mjs
 * Generates a MiniSearch-compatible search index from all content collections.
 * Run as part of `npm run build` → outputs /public/search-index.json
 *
 * Includes: regionen, unterkuenfte, orte, sehenswuerdigkeiten, gastro, camping, magazin
 * (all locales de/en/fr)
 *
 * Why not Pagefind: Pagefind's static index exceeds Cloudflare Pages'
 * 20k file limit (16k fragments + 16k pages). MiniSearch keeps the
 * entire index in a single ~200-400KB JSON file, served from CF Pages itself.
 *
 * Tradeoff: not full-text over every paragraph, but full-text over title,
 * kurzbeschreibung, beschreibung, tags, ort, kategorie — which is what
 * 99% of Tirol-Tourismus-Suche users actually want.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import MiniSearch from 'minisearch';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(__dirname, '..', 'src', 'data');
const OUT_DIR = path.join(__dirname, '..', 'public');

const COLLECTIONS = [
  { name: 'regionen', path: 'regionen', type: 'region', emoji: '🏔️' },
  { name: 'orte', path: 'orte', type: 'ort', emoji: '🏘️' },
  { name: 'unterkuenfte', path: 'unterkuenfte', type: 'unterkunft', emoji: '🏨' },
  { name: 'sehenswuerdigkeiten', path: 'sehenswuerdigkeiten', type: 'sight', emoji: '🏛️' },
  { name: 'gastro', path: 'gastro', type: 'gastro', emoji: '🍽️' },
  { name: 'camping', path: 'camping', type: 'camping', emoji: '🏕️' },
  { name: 'magazin', path: 'magazin', type: 'magazin', emoji: '📰' },
];

const LOCALES = ['de', 'en', 'fr']; // it/es/zh/nl/cs are not yet ready

// Common stop words per locale — drops ~30% of index tokens that
// carry no search signal. Tuned manually for German + English.
const STOPWORDS = new Set([
  // German
  'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einer', 'eines', 'einem',
  'und', 'oder', 'aber', 'mit', 'von', 'aus', 'bei', 'nach', 'seit', 'für', 'auf',
  'in', 'an', 'am', 'im', 'um', 'zu', 'zur', 'zum', 'als', 'wie', 'wenn', 'dann',
  'ist', 'sind', 'war', 'waren', 'hat', 'haben', 'wird', 'werden', 'kann', 'können',
  'sich', 'auch', 'noch', 'nur', 'sehr', 'hier', 'dort', 'diese', 'dieser', 'diesem',
  'diesen', 'jede', 'jeder', 'jedem', 'jeden', 'alle', 'aller', 'allem', 'allen',
  'was', 'wer', 'wen', 'wem', 'wann', 'wo', 'wieso', 'weshalb', 'warum', 'welche',
  'durch', 'über', 'unter', 'gegen', 'ohne', 'statt', 'trotz', 'während',
  'nicht', 'kein', 'keine', 'keiner', 'keinem', 'keinen',
  // English
  'the', 'a', 'an', 'and', 'or', 'but', 'with', 'of', 'from', 'at', 'by', 'for',
  'in', 'on', 'to', 'as', 'if', 'then', 'is', 'are', 'was', 'were', 'has', 'have',
  'will', 'can', 'its', 'also', 'just', 'only', 'very', 'this', 'that', 'these',
  'those', 'each', 'every', 'all', 'any', 'some', 'what', 'who', 'when', 'where',
  // French
  'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'mais', 'avec',
  'dans', 'sur', 'pour', 'par', 'à', 'au', 'aux', 'en', 'est', 'sont', 'a', 'ont',
  'pas', 'plus', 'très', 'cette', 'ces', 'ce', 'son', 'sa', 'ses', 'leur', 'leurs',
  'qui', 'que', 'quoi', 'dont', 'où', 'quand', 'comme', 'si', 'ne', 'se', 'y',
]);

function readCollection(name, locale) {
  const dir = locale === 'de'
    ? path.join(DATA_DIR, name)
    : path.join(DATA_DIR, locale, name);
  if (!fs.existsSync(dir)) return [];
  const entries = [];
  for (const item of fs.readdirSync(dir, { withFileTypes: true })) {
    if (!item.isDirectory()) continue;
    const jsonPath = path.join(dir, item.name, 'index.json');
    if (!fs.existsSync(jsonPath)) continue;
    try {
      const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
      if (data.status === 'archived' || data.status === 'draft') continue;
      if (data.published === false) continue;
      entries.push({ slug: item.name, entry: data });
    } catch (e) {
      // Skip malformed files silently
    }
  }
  return entries;
}

function stripMarkdown(md) {
  if (!md) return '';
  return md
    .replace(/<[^>]+>/g, ' ')           // HTML
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // [text](url) → text
    .replace(/[#*_`>~]+/g, ' ')         // markdown chars
    .replace(/\s+/g, ' ')
    .trim();
}

function buildDoc({ collection, locale, slug, entry, type, emoji }) {
  const name = entry.name || entry.titel || slug;
  const urlPrefix = locale === 'de' ? '' : `/${locale}`;
  const urlPath = {
    region: 'regionen',
    ort: 'orte',
    unterkunft: 'unterkuenfte',
    sight: 'sehenswuerdigkeiten',
    gastro: 'gastro',
    camping: 'camping',
    magazin: 'magazin',
  }[type] || type;
  const url = `${urlPrefix}/${urlPath}/${slug}/`;

  // Collect all searchable text fields
  const tags = (entry.tags || []).join(' ');
  const kategorien = (entry.kategorien || (entry.kategorie ? [entry.kategorie] : [])).join(' ');
  const ausstattung = Array.isArray(entry.ausstattung) ? entry.ausstattung.join(' ') : (entry.ausstattung || '');

  return {
    id: `${locale}:${type}:${slug}`,
    locale,
    type,
    name,
    emoji: entry.emoji || emoji,
    ort: entry.ort || '',
    region: entry.region || '',
    kategorie: entry.kategorie || kategorien || '',
    tier: entry.tier || '',
    sterne: entry.sterne || '',
    preis_ab: entry.preis_ab || '',
    kurzbeschreibung: stripMarkdown(entry.kurzbeschreibung || '').slice(0, 300),
    url,
    // Concatenated search corpus — single field, capped at 800 chars total
    // to keep the inverted index small. Title + name + location + tags are
    // the highest-signal terms; long prose dilutes the index.
    search: [
      name,
      entry.titel,
      entry.ort,
      entry.region,
      kategorien,
      tags,
      ausstattung,
      stripMarkdown(entry.kurzbeschreibung || ''),
      stripMarkdown(entry.beschreibung || '').slice(0, 400),
    ].filter(Boolean).join(' ').slice(0, 800),
  };
}

function main() {
  console.log('🔍 Building search indexes per locale…');
  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });

  let totalDocs = 0;

  for (const locale of LOCALES) {
    const docs = [];
    for (const coll of COLLECTIONS) {
      const entries = readCollection(coll.path, locale);
      for (const { slug, entry } of entries) {
        docs.push(buildDoc({
          collection: coll.name,
          locale,
          slug,
          entry,
          type: coll.type,
          emoji: coll.emoji,
        }));
      }
    }

    const miniSearch = new MiniSearch({
      idField: 'id',
      fields: ['search', 'name', 'ort', 'region', 'kategorie', 'tags'],
      storeFields: ['name', 'type', 'emoji', 'ort', 'region', 'url', 'locale', 'kategorie', 'tier', 'sterne', 'preis_ab', 'kurzbeschreibung'],
      searchOptions: {
        boost: { name: 3, ort: 2, region: 2, tags: 1.5 },
        fuzzy: 0.2,
        prefix: true,
        combineWith: 'AND',
      },
      tokenize: (text, fieldName) => {
        if (!text) return [];
        const tokens = text.toLowerCase()
          .replace(/[^\p{L}\p{N}\s-]/gu, ' ')
          .split(/\s+/)
          .filter(t => t.length >= 2 && t.length <= 30 && !STOPWORDS.has(t));
        return tokens;
      },
      processTerm: (term) => term.toLowerCase(),
      extractField: (doc, fieldName) => {
        const v = doc[fieldName];
        if (Array.isArray(v)) return v.join(' ');
        return v == null ? '' : String(v);
      },
    });
    miniSearch.addAll(docs);

    const output = {
      generatedAt: new Date().toISOString(),
      totalDocs: docs.length,
      index: miniSearch.toJSON(),
    };

    const outFile = path.join(OUT_DIR, `search-index.${locale}.json`);
    fs.writeFileSync(outFile, JSON.stringify(output));
    const sizeKB = (fs.statSync(outFile).size / 1024).toFixed(1);
    console.log(`  ${locale}: ${docs.length} docs → ${outFile} (${sizeKB} KB)`);
    totalDocs += docs.length;
  }

  console.log(`✅ ${totalDocs} total docs indexed across ${LOCALES.length} locales`);
}

main();
