#!/usr/bin/env python3
"""
translate_cron.py — Cronjob-Runner für die Übersetzungs-Pipeline.

Läuft alle 30 Minuten, verarbeitet ein Batch (Sprache × Kategorie),
committet und pusht die Ergebnisse.

Nutzung: python scripts/translate_cron.py [--limit N] [--max-batches N]
"""
import os, sys, json, subprocess, time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "src" / "data"
PYTHON = sys.executable
WORKER = str(BASE / "scripts" / "translate_worker.py")

LANGS = ["it", "es", "zh", "pl", "hu", "sk"]  # Priorität: it/es/zh zuerst (haben Subdomains)
CATEGORIES = ["gastro", "orte", "unterkuenfte", "camping", "sehenswuerdigkeiten", "regionen", "magazin", "erlebnisse", "events"]

import re
def strip_html(t):
    return re.sub(r'<[^>]+>', '', t or '').strip()

def count_missing(lang, cat, sample=None):
    """Zählt Einträge mit fehlender Übersetzung (beschreibung oder kurzbeschreibung)."""
    de_dir = DATA / cat
    lang_dir = DATA / lang / cat
    if not de_dir.exists():
        return 0
    items = [d for d in de_dir.iterdir() if d.is_dir()]
    if sample:
        items = items[:sample]
    missing = 0
    for item in items:
        de_file = item / "index.json"
        if not de_file.exists():
            continue
        try:
            de = json.loads(de_file.read_text(encoding="utf-8"))
            if de.get("status") == "archived":
                continue
            de_kb = strip_html(de.get("kurzbeschreibung") or "")
            de_be = strip_html(de.get("beschreibung") or "")
            if len(de_kb) < 50 and len(de_be) < 100:
                continue
            lang_file = lang_dir / item.name / "index.json"
            if not lang_file.exists():
                missing += 1
                continue
            lg = json.loads(lang_file.read_text(encoding="utf-8"))
            lg_kb = strip_html(lg.get("kurzbeschreibung") or "")
            lg_be = strip_html(lg.get("beschreibung") or "")
            if len(de_be) >= 100 and len(lg_be) < 100:
                missing += 1
            elif len(de_kb) >= 50 and len(lg_kb) < 50:
                missing += 1
        except Exception:
            pass
    return missing

def git_publish():
    """Commit + Push der Übersetzungen."""
    r = subprocess.run(["git", "status", "--short", "src/data"], capture_output=True, text=True, cwd=str(BASE))
    if not r.stdout.strip():
        return False
    subprocess.run(["git", "add", "src/data"], cwd=str(BASE))
    r = subprocess.run(["git", "commit", "-m", f"i18n: batch translations {time.strftime('%Y-%m-%d %H:%M')}"],
                       capture_output=True, text=True, cwd=str(BASE))
    if r.returncode != 0:
        return False
    r = subprocess.run(["git", "push", "origin", "master"], capture_output=True, text=True, cwd=str(BASE), timeout=120)
    return r.returncode == 0

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=120, help="Max Einträge pro Kategorie")
    ap.add_argument("--max-batches", type=int, default=2, help="Max Kategorien pro Lauf")
    args = ap.parse_args()

    t0 = time.time()
    print(f"🌍 TRANSLATION CRON {time.strftime('%H:%M')}")

    # 1. Homepage-Check (schnell)
    for lang in LANGS:
        hp = DATA / lang / "homepage.json"
        if not hp.exists():
            print(f"📄 {lang}: homepage.json fehlt → übersetze")
            subprocess.run([PYTHON, str(BASE / "scripts" / "translate_homepage.py"), lang],
                           cwd=str(BASE), timeout=600)

    # 2. Content-Batches
    batches = 0
    summary = []
    for lang in LANGS:
        if batches >= args.max_batches:
            break
        for cat in CATEGORIES:
            if batches >= args.max_batches:
                break
            missing = count_missing(lang, cat)
            if missing == 0:
                continue
            print(f"🔄 {lang}/{cat}: {missing} fehlend → Worker (limit {args.limit})")
            try:
                r = subprocess.run([PYTHON, WORKER, cat, lang, "--limit", str(args.limit)],
                                   cwd=str(BASE), capture_output=True, text=True, timeout=1500)
                # Parse "X OK, Y failed"
                for line in (r.stdout or "").split("\n"):
                    if "OK," in line and "failed" in line:
                        summary.append(f"{lang}/{cat}: {line.strip()}")
                batches += 1
            except subprocess.TimeoutExpired:
                summary.append(f"{lang}/{cat}: timeout")
                batches += 1

    # 3. Git publish
    pushed = git_publish()
    elapsed = int(time.time() - t0)

    if summary:
        print("📊 " + " | ".join(summary))
    print(f"✅ {batches} batches in {elapsed}s" + (" | pushed" if pushed else ""))

if __name__ == "__main__":
    main()
