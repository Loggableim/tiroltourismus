#!/usr/bin/env node
/**
 * check-content-gate.mjs
 * Prüft die unter src/data geänderten Dateien eines Branches gegen eine Basis
 * (Standard: origin/master). Ausgabe als Markdown-Tabelle, Exit 1 bei Fehlern.
 *
 * Aufruf: node scripts/check-content-gate.mjs [--base <ref>] [--no-network]
 */
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const DATA = 'src/data';
const LOCALES = ['de', 'cs', 'en', 'es', 'fr', 'it', 'nl', 'zh'];
const BLOCKED_FIELDS = new Set([
  'status', 'featured', 'emoji', 'farbe', 'bilder', 'hero_bild', 'grenzen',
  'koordinaten', 'slug', 'region', 'bezirk', 'hunde', 'title', 'metaDescription', 'text',
]);
const SOFT_STATUSES = new Set(['403', '429', 'timeout']);
const HARD_STATUSES = new Set(['404', '410']);
const HTTP_TIMEOUT_MS = 15000;
const CONCURRENCY = 12;
const HTML_TAG = /<[a-zA-Z][^>]*>/;

const args = process.argv.slice(2);
const baseIdx = args.indexOf('--base');
const BASE = baseIdx >= 0 ? args[baseIdx + 1] : 'origin/master';
const NO_NETWORK = args.includes('--no-network');

function git(gitArgs) {
  return execFileSync('git', gitArgs, { cwd: ROOT, encoding: 'utf8', maxBuffer: 256 * 1024 * 1024 });
}

function gitShow(ref, file) {
  try {
    return git(['show', `${ref}:${file}`]);
  } catch {
    return null;
  }
}

function changedFiles() {
  const out = git(['diff', '--name-status', '-M', `${BASE}...HEAD`, '--', DATA]);
  const files = [];
  for (const line of out.split('\n').filter(Boolean)) {
    const parts = line.split('\t');
    const status = parts[0][0];
    if (status === 'D') continue;
    files.push(parts[parts.length - 1]);
  }
  return files;
}

function splitLocale(file) {
  const rel = path.posix.relative(DATA, file);
  const parts = rel.split('/');
  if (LOCALES.includes(parts[0]) && parts.length > 1) {
    return { locale: parts[0], rest: parts.slice(1).join('/') };
  }
  return { locale: 'de', rest: rel };
}

function localeFilePath(locale, rest) {
  return locale === 'de' ? `${DATA}/${rest}` : `${DATA}/${locale}/${rest}`;
}

function entryName(rest) {
  return rest.replace(/\/index\.json$/, '').replace(/\.json$/, '');
}

function collectStrings(value, key, out) {
  if (typeof value === 'string') {
    out.push({ key, value });
  } else if (Array.isArray(value)) {
    value.forEach((v) => collectStrings(v, key, out));
  } else if (value && typeof value === 'object') {
    for (const [k, v] of Object.entries(value)) collectStrings(v, k, out);
  }
  return out;
}

function isHtmlField(key, value) {
  return key === 'beschreibung' || HTML_TAG.test(value);
}

function sameJson(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

async function checkUrl(url) {
  try {
    const res = await fetch(url, {
      redirect: 'follow',
      signal: AbortSignal.timeout(HTTP_TIMEOUT_MS),
      headers: { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36', Accept: 'text/html,*/*' },
    });
    res.body?.cancel();
    return String(res.status);
  } catch (err) {
    if (err?.name === 'TimeoutError' || err?.name === 'AbortError') return 'timeout';
    return `error:${err?.cause?.code || err?.message || 'unknown'}`;
  }
}

async function runPool(items, worker) {
  const results = new Map();
  let next = 0;
  const runners = Array.from({ length: CONCURRENCY }, async () => {
    while (next < items.length) {
      const item = items[next++];
      results.set(item, await worker(item));
    }
  });
  await Promise.all(runners);
  return results;
}

function cell(text) {
  return String(text).replace(/\|/g, '\\|').replace(/\n/g, ' ');
}

async function main() {
  try {
    git(['rev-parse', '--verify', BASE]);
  } catch {
    console.error(`Basis-Ref "${BASE}" nicht gefunden.`);
    process.exit(2);
  }

  const files = changedFiles();
  const findings = [];
  const addFinding = (file, entry, check, level, detail) =>
    findings.push({ file, entry, check, level, detail });

  if (files.length === 0) {
    console.log(`Keine geänderten Dateien unter ${DATA} gegenüber ${BASE}.`);
    process.exit(0);
  }

  const parsed = new Map();
  for (const file of files) {
    const { locale, rest } = splitLocale(file);
    const entry = entryName(rest);
    const abs = path.join(ROOT, file);
    let raw;
    try {
      raw = fs.readFileSync(abs, 'utf8');
    } catch (err) {
      addFinding(file, entry, '1 JSON gültig', 'error', `Datei nicht lesbar: ${err.code}`);
      continue;
    }

    let data;
    try {
      data = JSON.parse(raw);
    } catch (err) {
      addFinding(file, entry, '1 JSON gültig', 'error', `Ungültiges JSON: ${err.message}`);
      continue;
    }
    parsed.set(file, { data, locale, rest, entry });

    const siblings = LOCALES.filter((l) => {
      const p = localeFilePath(l, rest);
      return fs.existsSync(path.join(ROOT, p));
    });
    const missing = LOCALES.filter((l) => !siblings.includes(l));
    if (missing.length) {
      addFinding(file, entry, '2 Alle 8 Sprachen', 'error', `Fehlende Sprachen: ${missing.join(', ')}`);
    }

    const baseRaw = gitShow(BASE, file);
    if (baseRaw !== null) {
      let baseData = null;
      try {
        baseData = JSON.parse(baseRaw);
      } catch {
        addFinding(file, entry, '3 Nur Inhaltsfelder', 'error', 'Basis-Version ist kein gültiges JSON');
      }
      if (baseData) {
        const keys = new Set([...Object.keys(baseData), ...Object.keys(data)]);
        for (const key of keys) {
          if (!BLOCKED_FIELDS.has(key) || sameJson(baseData[key], data[key])) continue;
          if (key in baseData) {
            addFinding(file, entry, '3 Nur Inhaltsfelder', 'error', `Blockiertes Feld geändert: ${key}`);
          } else {
            addFinding(file, entry, '3 Nur Inhaltsfelder', 'warn', `Blockiertes Feld neu ergänzt: ${key}`);
          }
        }
      }
    }

    for (const { key, value } of collectStrings(data, '', [])) {
      if (value.includes('**') && isHtmlField(key, value)) {
        addFinding(file, entry, '4 Kein ** in HTML', 'error', `Feld ${key || '(root)'} enthält "**"`);
      }
    }

    if (!('sources' in data)) {
      addFinding(file, entry, '5 Quellen', 'error', 'Feld sources fehlt');
    } else if (!Array.isArray(data.sources)) {
      addFinding(file, entry, '5 Quellen', 'error', 'sources ist kein Array');
    } else {
      for (const url of data.sources) {
        if (typeof url !== 'string' || !url.startsWith('https://')) {
          addFinding(file, entry, '5 Quellen https', 'error', `Keine https-URL: ${url}`);
        }
      }
    }
  }

  const urlStatus = new Map();
  if (!NO_NETWORK) {
    const urls = [...new Set(
      [...parsed.values()].flatMap(({ data }) =>
        Array.isArray(data.sources) ? data.sources.filter((u) => typeof u === 'string' && u.startsWith('https://')) : []
      )
    )];
    const results = await runPool(urls, checkUrl);
    for (const [url, status] of results) urlStatus.set(url, status);
  }

  for (const [file, { data, entry }] of parsed) {
    if (!Array.isArray(data.sources) || NO_NETWORK) continue;
    const httpUrls = data.sources.filter((u) => typeof u === 'string' && u.startsWith('https://'));
    const statuses = httpUrls.map((u) => [u, urlStatus.get(u)]);
    const hasOk = statuses.some(([, s]) => s && /^2\d\d$/.test(s));
    for (const [url, status] of statuses) {
      if (HARD_STATUSES.has(status)) {
        addFinding(file, entry, '5 HTTP-Status', 'error', `${status} ${url}`);
      } else if (SOFT_STATUSES.has(status)) {
        if (!hasOk) {
          addFinding(file, entry, '5 HTTP-Status', 'error', `${status} ohne 200-Quelle im Eintrag: ${url}`);
        } else {
          addFinding(file, entry, '5 HTTP-Status', 'warn', `${status} (andere Quelle 200): ${url}`);
        }
      } else if (status && !/^2\d\d$/.test(status) && !status.startsWith('3')) {
        addFinding(file, entry, '5 HTTP-Status', 'warn', `${status} ${url}`);
      }
    }
  }

  const errors = findings.filter((f) => f.level === 'error');
  const warns = findings.filter((f) => f.level === 'warn');
  console.log(`# Content-Gate: ${BASE}...HEAD`);
  console.log('');
  console.log(`Geprüfte Dateien: ${files.length} | Fehler: ${errors.length} | Warnungen: ${warns.length} | Netzwerk: ${NO_NETWORK ? 'aus' : 'an'}`);
  console.log('');
  if (findings.length === 0) {
    console.log('Keine Befunde.');
  } else {
    console.log('| Datei | Eintrag | Prüfung | Stufe | Befund |');
    console.log('| --- | --- | --- | --- | --- |');
    for (const f of findings) {
      console.log(`| ${cell(f.file)} | ${cell(f.entry)} | ${cell(f.check)} | ${f.level} | ${cell(f.detail)} |`);
    }
  }
  process.exit(errors.length ? 1 : 0);
}

main();
