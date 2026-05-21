#!/usr/bin/env python3
"""Create all translation kanban tasks for the tirol-uebersetzung board."""
import subprocess, json, sys, os, time

HERMES_BASE = "E:/HermesPortable"
BOARD = "tirol-uebersetzung"
PROJECT = "F:/tiroltourismus"
PROFILE = "content-filler"

ENV = {**os.environ,
    "HERMES_KANBAN_BOARD": BOARD,
    "PYTHONPATH": f"{HERMES_BASE}/cids-hermes-agent"
}

CLI = [sys.executable, "-m", "hermes_cli.main", "kanban"]

def kanban(*args):
    cmd = CLI + list(args) + ["--json"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=ENV, cwd=HERMES_BASE)
    if r.returncode != 0:
        print(f"  ❌ {' '.join(args[:3])}: {r.stderr[:200]}", flush=True)
        return None
    try:
        data = json.loads(r.stdout)
        return data["id"]
    except:
        print(f"  ❌ {' '.join(args[:3])}: PARSING FAILED - {r.stdout[:200]}", flush=True)
        return None

CATS = ["gastro", "unterkuenfte", "orte", "camping", "sehenswuerdigkeiten", "magazin", "regionen", "erlebnisse", "events"]
COUNTS = {"gastro": 3415, "unterkuenfte": 1111, "orte": 258, "camping": 236,
          "sehenswuerdigkeiten": 154, "magazin": 43, "regionen": 13, "erlebnisse": 6, "events": 4}

print("=" * 60)
print("🏗️  CREATE TRANSLATION KANBAN BOARD")
print("=" * 60)

# ── PHASE 1: FR (already running) ──
print("\n--- 🇫🇷 FRANZÖSISCH ---")
fr_cats = {}
for cat in CATS:
    title = f"FR-{cat}-{COUNTS[cat]}"
    body = f"PROJEKT-PFAD: {PROJECT}\nÜbersetze Kategorie '{cat}' ins Französische.\nBefehl: cd {PROJECT} && python scripts/translate_worker.py {cat} fr\nAnzahl: {COUNTS[cat]} Einträge"
    tid = kanban("create", title, "--body", body, "--assignee", PROFILE)
    if tid:
        fr_cats[cat] = tid
        print(f"  ✅ FR-{cat} → {tid}", flush=True)
    time.sleep(0.2)

fr_master = kanban("create", "FR-Master-5241", "--body",
    f"PROJEKT-PFAD: {PROJECT}\nÜbersetze ALLE Kategorien ins Französische.\nLäuft bereits als Background-Prozess.\nNach Abschluss: EN freigeben.",
    "--assignee", PROFILE)
print(f"  ✅ FR-Master → {fr_master}", flush=True)

# ── Link FR category tasks to master ──
for cat, tid in fr_cats.items():
    kanban("link", "--parent", fr_master, "--child", tid)
    time.sleep(0.1)

# ── PHASE 2: EN ──
print("\n--- 🇬🇧 ENGLISCH ---")
en_cats = {}
for cat in CATS:
    title = f"EN-{cat}-{COUNTS[cat]}"
    body = f"PROJEKT-PFAD: {PROJECT}\nÜbersetze Kategorie '{cat}' ins Englische.\nBefehl: cd {PROJECT} && python scripts/translate_worker.py {cat} en\nAnzahl: {COUNTS[cat]} Einträge"
    tid = kanban("create", title, "--body", body, "--assignee", PROFILE, "--parent", fr_cats[cat])
    if tid:
        en_cats[cat] = tid
        print(f"  ✅ EN-{cat} → {tid}", flush=True)
    time.sleep(0.2)

en_master = kanban("create", "EN-Master-5241", "--body",
    f"PROJEKT-PFAD: {PROJECT}\nÜbersetze ALLE Kategorien ins Englische.\nBefehl: cd {PROJECT} && bash scripts/translate_language.sh en",
    "--assignee", PROFILE, "--parent", fr_master)
print(f"  ✅ EN-Master → {en_master}", flush=True)

# ── Link EN category tasks to master ──
for cat, tid in en_cats.items():
    kanban("link", "--parent", en_master, "--child", tid)
    time.sleep(0.1)

# ── PHASE 3: IT ──
print("\n--- 🇮🇹 ITALIENISCH ---")
it_cats = {}
for cat in CATS:
    title = f"IT-{cat}-{COUNTS[cat]}"
    body = f"PROJEKT-PFAD: {PROJECT}\nÜbersetze Kategorie '{cat}' ins Italienische.\nBefehl: cd {PROJECT} && python scripts/translate_worker.py {cat} it\nAnzahl: {COUNTS[cat]} Einträge"
    tid = kanban("create", title, "--body", body, "--assignee", PROFILE, "--parent", en_cats[cat])
    if tid:
        it_cats[cat] = tid
        print(f"  ✅ IT-{cat} → {tid}", flush=True)
    time.sleep(0.2)

it_master = kanban("create", "IT-Master-5241", "--body",
    f"PROJEKT-PFAD: {PROJECT}\nÜbersetze ALLE Kategorien ins Italienische.\nBefehl: cd {PROJECT} && bash scripts/translate_language.sh it",
    "--assignee", PROFILE, "--parent", en_master)
print(f"  ✅ IT-Master → {it_master}", flush=True)

for cat, tid in it_cats.items():
    kanban("link", "--parent", it_master, "--child", tid)
    time.sleep(0.1)

# ── PHASE 4: ES ──
print("\n--- 🇪🇸 SPANISCH ---")
es_cats = {}
for cat in CATS:
    title = f"ES-{cat}-{COUNTS[cat]}"
    body = f"PROJEKT-PFAD: {PROJECT}\nÜbersetze Kategorie '{cat}' ins Spanische.\nBefehl: cd {PROJECT} && python scripts/translate_worker.py {cat} es\nAnzahl: {COUNTS[cat]} Einträge"
    tid = kanban("create", title, "--body", body, "--assignee", PROFILE, "--parent", it_cats[cat])
    if tid:
        es_cats[cat] = tid
        print(f"  ✅ ES-{cat} → {tid}", flush=True)
    time.sleep(0.2)

es_master = kanban("create", "ES-Master-5241", "--body",
    f"PROJEKT-PFAD: {PROJECT}\nÜbersetze ALLE Kategorien ins Spanische.\nBefehl: cd {PROJECT} && bash scripts/translate_language.sh es",
    "--assignee", PROFILE, "--parent", it_master)
print(f"  ✅ ES-Master → {es_master}", flush=True)

for cat, tid in es_cats.items():
    kanban("link", "--parent", es_master, "--child", tid)
    time.sleep(0.1)

# ── PHASE 5: ZH ──
print("\n--- 🇨🇳 CHINESISCH ---")
zh_cats = {}
for cat in CATS:
    title = f"ZH-{cat}-{COUNTS[cat]}"
    body = f"PROJEKT-PFAD: {PROJECT}\nÜbersetze Kategorie '{cat}' ins Chinesische.\nBefehl: cd {PROJECT} && python scripts/translate_worker.py {cat} zh\nAnzahl: {COUNTS[cat]} Einträge\nHinweis: Für Chinesisch bei Bedarf deepseek-v4-flash nutzen."
    tid = kanban("create", title, "--body", body, "--assignee", PROFILE, "--parent", es_cats[cat])
    if tid:
        zh_cats[cat] = tid
        print(f"  ✅ ZH-{cat} → {tid}", flush=True)
    time.sleep(0.2)

zh_master = kanban("create", "ZH-Master-5241", "--body",
    f"PROJEKT-PFAD: {PROJECT}\nÜbersetze ALLE Kategorien ins Chinesische.\nBefehl: cd {PROJECT} && bash scripts/translate_language.sh zh",
    "--assignee", PROFILE, "--parent", es_master)
print(f"  ✅ ZH-Master → {zh_master}", flush=True)

for cat, tid in zh_cats.items():
    kanban("link", "--parent", zh_master, "--child", tid)
    time.sleep(0.1)

print(f"\n{'='*60}")
print(f"🏁 BOARD COMPLETE: 50 Tasks")
print(f"{'='*60}")
print(f"\nFR läuft bereits als Background-Prozess.")
print(f"Kanban Dispatcher starten: cron job alle 2 Minuten")
