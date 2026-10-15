#!/usr/bin/env node
/**
 * gate-sweep.mjs
 * Führt scripts/check-content-gate.mjs für mehrere Branches gegen origin/master aus.
 * Jeder Branch bekommt einen temporären Worktree, der danach wieder entfernt wird.
 *
 * Aufruf: node scripts/gate-sweep.mjs --branches a,b,c
 *         cat branches.txt | node scripts/gate-sweep.mjs
 */
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const GATE_SRC = path.join(ROOT, 'scripts', 'check-content-gate.mjs');
const BASE = 'origin/master';
const TLS_PATTERN = /CERT|TLS|SSL/;

function git(args, cwd = ROOT) {
  return execFileSync('git', args, { cwd, encoding: 'utf8', maxBuffer: 256 * 1024 * 1024 });
}

function parseBranches(argv) {
  const idx = argv.indexOf('--branches');
  if (idx >= 0) {
    const value = argv[idx + 1];
    if (!value || value.startsWith('--')) throw new Error('--branches braucht eine Liste');
    return value.split(',').map((s) => s.trim()).filter(Boolean);
  }
  if (!process.stdin.isTTY) {
    return fs.readFileSync(0, 'utf8').split('\n').map((s) => s.trim()).filter(Boolean);
  }
  throw new Error('Keine Branches: --branches a,b,c oder Liste über stdin angeben');
}

function runGateOnBranch(branch, index) {
  const worktree = path.join(os.tmpdir(), `gate-sweep-${process.pid}-${index}`);
  const result = { branch, errors: 0, warns: 0, http404: 0, tls: 0, types: '', note: '' };
  try {
    git(['fetch', '-q', 'origin', `+refs/heads/${branch}:refs/remotes/origin/${branch}`]);
    git(['worktree', 'add', '-q', '--detach', worktree, `origin/${branch}`]);
    fs.mkdirSync(path.join(worktree, 'scripts'), { recursive: true });
    fs.copyFileSync(GATE_SRC, path.join(worktree, 'scripts', 'check-content-gate.mjs'));

    let output = '';
    try {
      output = execFileSync('node', ['scripts/check-content-gate.mjs', '--base', BASE], {
        cwd: worktree,
        encoding: 'utf8',
        maxBuffer: 256 * 1024 * 1024,
      });
    } catch (err) {
      output = err.stdout?.toString() ?? '';
    }

    const summary = output.match(/Fehler: (\d+) \| Warnungen: (\d+)/);
    if (!summary) {
      result.note = 'Gate-Lauf ohne Ausgabe';
      return result;
    }
    result.errors = Number(summary[1]);
    result.warns = Number(summary[2]);

    const types = new Map();
    for (const line of output.split('\n')) {
      if (!line.startsWith('| src/data')) continue;
      const cols = line.split(' | ').map((c) => c.replace(/^\| /, '').replace(/ \|$/, '').trim());
      const [, , check, stufe, detail] = cols;
      if (stufe !== 'error') continue;
      if (/^(404|410) /.test(detail)) result.http404 += 1;
      if (/error:/.test(detail) && TLS_PATTERN.test(detail)) result.tls += 1;
      types.set(check, (types.get(check) ?? 0) + 1);
    }
    result.types = [...types.keys()].sort().join(', ') || '-';
    return result;
  } catch (err) {
    result.note = `Lauf fehlgeschlagen: ${err.message.split('\n')[0]}`;
    return result;
  } finally {
    try {
      git(['worktree', 'remove', '--force', worktree]);
    } catch {
      fs.rmSync(worktree, { recursive: true, force: true });
    }
  }
}

function main() {
  let branches;
  try {
    branches = parseBranches(process.argv.slice(2));
  } catch (err) {
    console.error(err.message);
    process.exit(2);
  }
  if (branches.length === 0) {
    console.error('Keine Branches angegeben.');
    process.exit(2);
  }

  git(['fetch', '-q', 'origin', 'master']);
  console.log('| Branch | Fehler | Warnungen | 404/410 | TLS-Fehler | Befundtyp | Hinweis |');
  console.log('| --- | --- | --- | --- | --- | --- | --- |');
  branches.forEach((branch, i) => {
    const r = runGateOnBranch(branch, i);
    const http404 = r.http404;
    console.log(`| ${branch} | ${r.errors} | ${r.warns} | ${http404} | ${r.tls} | ${r.types} | ${r.note || '-'} |`);
  });
}

main();
