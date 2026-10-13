/**
 * Benchmark content.js helpers used on gastro detail pages.
 * Run from repo root: node scripts/bench-content.mjs
 */
import {
  readCollection,
  isPublished,
  findNearby,
  findByTag,
  autoLinkContent,
  invalidateCollectionCache,
  invalidateEntityCache,
} from '../src/lib/content.js';

const LOCALES = ['de', 'en', 'fr', 'es', 'zh'];
const SAMPLE_SIZE = 12;

function hrMs(start) {
  return Number(process.hrtime.bigint() - start) / 1e6;
}

function pickSamples(entries, n) {
  const pub = entries.filter((e) => isPublished(e.entry));
  if (pub.length <= n) return pub;
  const step = Math.max(1, Math.floor(pub.length / n));
  const out = [];
  for (let i = 0; i < pub.length && out.length < n; i += step) {
    out.push(pub[i]);
  }
  while (out.length < n && out.length < pub.length) {
    out.push(pub[out.length]);
  }
  return out;
}

function benchOne(label, fn) {
  const t0 = process.hrtime.bigint();
  const result = fn();
  const ms = hrMs(t0);
  return { label, ms, result };
}

function warmLocale(locale) {
  invalidateCollectionCache();
  invalidateEntityCache(locale);
  for (const coll of [
    'regionen',
    'unterkuenfte',
    'camping',
    'gastro',
    'orte',
    'sehenswuerdigkeiten',
    'magazin',
    'erlebnisse',
    'events',
  ]) {
    readCollection(coll, locale);
  }
}

function countPublishedGastro(locale) {
  return readCollection('gastro', locale).filter((g) => isPublished(g.entry)).length;
}

function runSampleBenchmarks() {
  console.log('\n=== Published gastro counts (isPublished) ===');
  const counts = {};
  for (const locale of LOCALES) {
    invalidateCollectionCache();
    counts[locale] = countPublishedGastro(locale);
    console.log(`  ${locale}: ${counts[locale]}`);
  }

  console.log('\n=== Sample benchmarks (per locale, ms) ===');
  console.log(
    'locale\tsamples\tfindNearby_avg\tfindNearby_max\tfindByTag_avg\tfindByTag_max\tautoLink_avg\tautoLink_max\tdesc_chars_avg'
  );

  for (const locale of LOCALES) {
    warmLocale(locale);
    const all = readCollection('gastro', locale);
    const samples = pickSamples(all, SAMPLE_SIZE);

    const nearbyTimes = [];
    const tagTimes = [];
    const linkTimes = [];
    let descChars = 0;

    for (const { slug, entry } of samples) {
      const html = [entry.kurzbeschreibung, entry.beschreibung].filter(Boolean).join('<br><br>');
      descChars += html.replace(/<[^>]+>/g, '').length;

      const tag = entry.tags?.[0];
      if (entry.koordinaten) {
        nearbyTimes.push(
          benchOne('findNearby', () => findNearby(entry, 'gastro', locale, 8)).ms
        );
      }
      if (tag) {
        tagTimes.push(
          benchOne('findByTag', () =>
            findByTag(tag, locale).filter((r) => r.collection === 'gastro' && r.slug !== slug)
          ).ms
        );
      }
      if (html) {
        linkTimes.push(
          benchOne('autoLink', () =>
            autoLinkContent(html, { ...entry, slug }, locale, 5, 'gastro', slug)
          ).ms
        );
      }
    }

    const avg = (arr) => (arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0);
    const max = (arr) => (arr.length ? Math.max(...arr) : 0);

    console.log(
      [
        locale,
        samples.length,
        avg(nearbyTimes).toFixed(2),
        max(nearbyTimes).toFixed(2),
        avg(tagTimes).toFixed(2),
        max(tagTimes).toFixed(2),
        avg(linkTimes).toFixed(2),
        max(linkTimes).toFixed(2),
        samples.length ? Math.round(descChars / samples.length) : 0,
      ].join('\t')
    );
  }

  return counts;
}

function runFrWorstCase() {
  console.log('\n=== FR worst-case: all published gastro (cached collections) ===');
  const locale = 'fr';
  warmLocale(locale);
  const pub = readCollection('gastro', locale).filter((g) => isPublished(g.entry));

  const byNearby = [];
  const byLink = [];

  for (const { slug, entry } of pub) {
    const html = [entry.kurzbeschreibung, entry.beschreibung].filter(Boolean).join('<br><br>');

    if (entry.koordinaten) {
      const ms = benchOne('findNearby', () => findNearby(entry, 'gastro', locale, 8)).ms;
      byNearby.push({ slug, ms, descLen: html.length });
    }
    if (html) {
      const ms = benchOne('autoLink', () =>
        autoLinkContent(html, { ...entry, slug }, locale, 5, 'gastro', slug)
      ).ms;
      byLink.push({ slug, ms, descLen: html.length });
    }
  }

  byNearby.sort((a, b) => b.ms - a.ms);
  byLink.sort((a, b) => b.ms - a.ms);

  console.log('\nTop 10 findNearby (fr):');
  for (const row of byNearby.slice(0, 10)) {
    console.log(`  ${row.ms.toFixed(2)} ms\t${row.slug}\tdescLen=${row.descLen}`);
  }

  console.log('\nTop 10 autoLinkContent (fr):');
  for (const row of byLink.slice(0, 10)) {
    console.log(`  ${row.ms.toFixed(2)} ms\t${row.slug}\tdescLen=${row.descLen}`);
  }

  const nearbyTotal = byNearby.reduce((s, r) => s + r.ms, 0);
  const linkTotal = byLink.reduce((s, r) => s + r.ms, 0);
  console.log('\nFR totals (published with coords / with html):');
  console.log(`  findNearby: ${byNearby.length} pages, sum=${nearbyTotal.toFixed(2)} ms, avg=${(nearbyTotal / byNearby.length).toFixed(2)} ms`);
  console.log(`  autoLinkContent: ${byLink.length} pages, sum=${linkTotal.toFixed(2)} ms, avg=${(linkTotal / byLink.length).toFixed(2)} ms`);

  return { byNearby, byLink, nearbyTotal, linkTotal };
}

function runEnCompareWorstCase() {
  console.log('\n=== EN totals for comparison (same methodology) ===');
  const locale = 'en';
  warmLocale(locale);
  const pub = readCollection('gastro', locale).filter((g) => isPublished(g.entry));

  let nearbyTotal = 0;
  let nearbyN = 0;
  let linkTotal = 0;
  let linkN = 0;

  for (const { slug, entry } of pub) {
    const html = [entry.kurzbeschreibung, entry.beschreibung].filter(Boolean).join('<br><br>');
    if (entry.koordinaten) {
      nearbyTotal += benchOne('findNearby', () => findNearby(entry, 'gastro', locale, 8)).ms;
      nearbyN++;
    }
    if (html) {
      linkTotal += benchOne('autoLink', () =>
        autoLinkContent(html, { ...entry, slug }, locale, 5, 'gastro', slug)
      ).ms;
      linkN++;
    }
  }

  console.log(`  findNearby: ${nearbyN} pages, sum=${nearbyTotal.toFixed(2)} ms, avg=${(nearbyTotal / nearbyN).toFixed(2)} ms`);
  console.log(`  autoLinkContent: ${linkN} pages, sum=${linkTotal.toFixed(2)} ms, avg=${(linkTotal / linkN).toFixed(2)} ms`);
}

runSampleBenchmarks();
runFrWorstCase();
runEnCompareWorstCase();
