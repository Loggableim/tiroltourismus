import sqlite3, os, datetime

BOARD_NAME = "tirol-cicd"
PROJEKT = "F:\\tiroltourismus"
HERMES_HOME = "C:\\HermesPortable\\home"

DB_PATHS = [
    f"{HERMES_HOME}/kanban/boards/{BOARD_NAME}/kanban.db",
    f"{HERMES_HOME}/spaces/tirol-tourismus/kanban/boards/{BOARD_NAME}/kanban.db",
]

def create_task(conn, tid, title, body, assignee, priority=1, parents=None):
    now = datetime.datetime.now().timestamp()
    conn.execute("""INSERT OR REPLACE INTO tasks 
        (id, title, body, assignee, status, priority, created_at, max_runtime_seconds, max_retries)
        VALUES (?, ?, ?, ?, 'ready', ?, ?, 7200, 3)""",
        (tid, title, body[:2000], assignee, priority, now))
    
    if parents:
        for p in parents:
            conn.execute("INSERT OR REPLACE INTO task_links VALUES (?, ?)", (p, tid))
            # Put child in 'todo' since it has parents
            conn.execute("UPDATE tasks SET status='todo' WHERE id=?", (tid,))
    
    conn.commit()

# Connect to both DBs
conns = []
for db_path in DB_PATHS:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY, title TEXT, body TEXT, assignee TEXT DEFAULT '',
            status TEXT DEFAULT 'pending', priority INTEGER DEFAULT 0,
            created_by TEXT DEFAULT '', created_at REAL, started_at REAL,
            completed_at REAL, workspace_kind TEXT DEFAULT '', workspace_path TEXT DEFAULT '',
            claim_lock TEXT DEFAULT '', claim_expires REAL DEFAULT 0,
            tenant TEXT DEFAULT '', result TEXT DEFAULT '', idempotency_key TEXT DEFAULT '',
            consecutive_failures INTEGER DEFAULT 0, worker_pid TEXT DEFAULT '',
            last_failure_error TEXT DEFAULT '', max_runtime_seconds INTEGER DEFAULT 3600,
            last_heartbeat_at REAL DEFAULT 0, current_run_id TEXT DEFAULT '',
            workflow_template_id TEXT DEFAULT '', current_step_key TEXT DEFAULT '',
            skills TEXT DEFAULT '', max_retries INTEGER DEFAULT 3
        );
        CREATE TABLE IF NOT EXISTS task_links (parent_id TEXT, child_id TEXT);
        CREATE TABLE IF NOT EXISTS task_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, author TEXT,
            body TEXT, created_at REAL);
        CREATE TABLE IF NOT EXISTS task_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, run_id TEXT,
            kind TEXT, payload TEXT, created_at REAL);
        CREATE TABLE IF NOT EXISTS task_runs (
            id TEXT PRIMARY KEY, task_id TEXT, profile TEXT DEFAULT '',
            step_key TEXT DEFAULT '', status TEXT DEFAULT 'pending',
            claim_lock TEXT DEFAULT '', claim_expires REAL DEFAULT 0,
            worker_pid TEXT DEFAULT '', max_runtime_seconds INTEGER DEFAULT 1800,
            last_heartbeat_at REAL DEFAULT 0, started_at REAL, ended_at REAL,
            outcome TEXT DEFAULT '', summary TEXT DEFAULT '',
            metadata TEXT DEFAULT '{}', error TEXT DEFAULT ''
        );
    """)
    conns.append(conn)

# Clear existing tasks
for conn in conns:
    conn.execute("DELETE FROM tasks")
    conn.execute("DELETE FROM task_links")
    conn.execute("DELETE FROM task_comments")
    conn.execute("DELETE FROM task_events")
    conn.execute("DELETE FROM task_runs")
    conn.commit()

# ====== PHASE 1 - FOUNDATION ======

create_task(conns[0], "t_faq_expand",
    "FAQ-Expansion: 25 zu 100+ Eintraege",
    "PROJEKT-PFAD: " + PROJEKT + "\n--\nAUFGABE: Erweitere src/data/faq.json von 25 auf min. 100 FAQ-Eintraege.\nBESTEHENDE KATEGORIEN: allgemein, wandern, ski, unterkunft, gastro, anreise\nNEUE KATEGORIEN: camping, familie, wellness, kultur, events, wetter, sicherheit, mobilitaet\n--\nFORMAT: Jeder Eintrag: frage, antwort (50-150 Woerter), kategorie, tags\n--\nAKZEPTANZKRITERIEN:\n- Min 100 Eintraege\n- Alle Kategorien haben min 5 Eintraege\n- Keine Dubletten\n- JSON valide",
    "content-filler")
create_task(conns[1], "t_faq_expand",
    "FAQ-Expansion: 25 zu 100+ Eintraege",
    "PROJEKT-PFAD: " + PROJEKT + "\n--\nAUFGABE: Erweitere src/data/faq.json von 25 auf min. 100 FAQ-Eintraege.\nBESTEHENDE KATEGORIEN: allgemein, wandern, ski, unterkunft, gastro, anreise\nNEUE KATEGORIEN: camping, familie, wellness, kultur, events, wetter, sicherheit, mobilitaet\n--\nFORMAT: Jeder Eintrag: frage, antwort (50-150 Woerter), kategorie, tags\n--\nAKZEPTANZKRITERIEN:\n- Min 100 Eintraege\n- Alle Kategorien haben min 5 Eintraege\n- Keine Dubletten\n- JSON valide",
    "content-filler")

create_task(conns[0], "t_gastro_desc_b1",
    "Gastro-Beschreibungen Batch 1: 500 Eintraege",
    "PROJEKT-PFAD: " + PROJEKT + "\n--\nAUFGABE: Generiere beschreibung-Felder fuer 500 Gastro-Eintraege in src/data/gastro/\n--\nVORGEHEN:\n1. Liste alle Gastro-Dirs mit fehlender/kurzer Beschreibung\n2. Fuer jeden: schreibe 50-150 Woerter Beschreibung (HTML mit <p>-Tags, kulinarischer Fokus)\n3. Speichere direkt in index.json unter dem key 'beschreibung'\n--\nAKZEPTANZKRITERIEN:\n- 500 Eintraege mit neuer Beschreibung\n- Kein Eintrag ueberschrieben der bereits >100 Zeichen hatte\n- JSON valide nach Update",
    "content-filler")
create_task(conns[1], "t_gastro_desc_b1",
    "Gastro-Beschreibungen Batch 1: 500 Eintraege",
    "PROJEKT-PFAD: " + PROJEKT + "\n--\nAUFGABE: Generiere beschreibung-Felder fuer 500 Gastro-Eintraege in src/data/gastro/\n--\nVORGEHEN:\n1. Liste alle Gastro-Dirs mit fehlender/kurzer Beschreibung\n2. Fuer jeden: schreibe 50-150 Woerter Beschreibung (HTML mit <p>-Tags, kulinarischer Fokus)\n3. Speichere direkt in index.json unter dem key 'beschreibung'\n--\nAKZEPTANZKRITERIEN:\n- 500 Eintraege mit neuer Beschreibung\n- Kein Eintrag ueberschrieben der bereits >100 Zeichen hatte\n- JSON valide nach Update",
    "content-filler")

create_task(conns[0], "t_orte_kurzbeschr",
    "Orte-Kurzbeschreibungen: 123 Eintraege erweitern",
    "PROJEKT-PFAD: " + PROJEKT + "\n--\nAUFGABE: Erweitere 123 Orts-Kurzbeschreibungen in src/data/orte/*/index.json auf >100 Zeichen.\n--\nVORGEHEN:\n1. Finde Orte mit kurzbeschreibung < 100 Zeichen\n2. Schreibe informativere Texte (80-150 Zeichen, POI, Lage, Besonderheit)\n3. Aktualisiere nur 'kurzbeschreibung'-Feld in index.json\n--\nAKZEPTANZKRITERIEN:\n- Alle 123 Eintraege aktualisiert\n- Kein Ortsprofil ueberschrieben (nur kurzbeschreibung)\n- JSON valide",
    "content-filler")
create_task(conns[1], "t_orte_kurzbeschr",
    "Orte-Kurzbeschreibungen: 123 Eintraege erweitern",
    "PROJEKT-PFAD: " + PROJEKT + "\n--\nAUFGABE: Erweitere 123 Orts-Kurzbeschreibungen in src/data/orte/*/index.json auf >100 Zeichen.",
    "content-filler")

create_task(conns[0], "t_json_validate",
    "JSON-Schema Validierung + Data Quality Report",
    "PROJEKT-PFAD: " + PROJEKT + "\n--\nAUFGABE: Vollstaendige Data-Quality-Pruefung aller JSON-Collections.\n--\nPRUEFUNGEN:\n1. Validiere jedes index.json (fehlende Pflichtfelder)\n2. Finde Dubletten (gleicher slug in versch. Collections)\n3. Pruefe Koordinaten-Format (lat/lng plausibel)\n4. Pruefe bilder-Array (leer, fehlende Dateien)\n5. Pruefe Cross-Referenzen (ort/region existieren)\n--\nOUTPUT: src/data/_quality_report.json mit total_issues, issues[]\n--\nAKZEPTANZKRITERIEN:\n- Report existiert\n- Alle Collections gescannt\n- Schwere Issues (broken refs) extra markiert",
    "backend-dev")
create_task(conns[1], "t_json_validate",
    "JSON-Schema Validierung + Data Quality Report",
    "PROJEKT-PFAD: " + PROJEKT + "\n--\nAUFGABE: Vollstaendige Data-Quality-Pruefung aller JSON-Collections.",
    "backend-dev")

create_task(conns[0], "t_i18n_check",
    "i18n-Completion-Check: 6 Sprachen checken",
    "PROJEKT-PFAD: " + PROJEKT + "\n--\nAUFGABE: Pruefe i18n-Luecken in 6 Sprachen (en, fr, es, it, nl, zh).\n--\nVORGEHEN:\n1. Liste alle Seiten in src/pages/[locale]/\n2. Pruefe welche Seiten in welcher Sprache fehlen\n3. Pruefe src/data/*/i18n/ Uebersetzungen\n4. Pruefe ob 404/500-Seiten uebersetzt sind\n5. Pruefe meta-tags, titles in jeder Sprache\n--\nOUTPUT: Report als Task-Kommentar + Luecken-Liste\n--\nAKZEPTANZKRITERIEN:\n- Report mit konkreten Luecken (Datei, Sprache)\n- Priorisierung: kritisch vs minor\n- 404/500-Seiten muessen in ALLEN Sprachen existieren",
    "frontend-dev")
create_task(conns[1], "t_i18n_check",
    "i18n-Completion-Check: 6 Sprachen checken",
    "PROJEKT-PFAD: " + PROJEKT + "\n--\nAUFGABE: Pruefe i18n-Luecken in 6 Sprachen (en, fr, es, it, nl, zh).",
    "frontend-dev")

# T6: Build-Gate (wartet auf alle anderen)
gate_parents = ["t_faq_expand", "t_gastro_desc_b1", "t_orte_kurzbeschr", "t_json_validate", "t_i18n_check"]

create_task(conns[0], "t_build_gate",
    "QUALITY GATE: Build + Pagefind + Report",
    "PROJEKT-PFAD: " + PROJEKT + "\n--\nAUFGABE: Finaler Build-Test nach Phase 1.\n--\nSCHRITTE:\n1. npm run build (astro build + pagefind)\n2. Pruefe Exit-Code 0\n3. Zaehle generierte Seiten in dist/\n4. Pruefe pagefind-index existiert\n5. Pruefe dist/_astro/ Bundle-Groessen\n6. Kopiere quality_report.json ins dist/\n--\nAKZEPTANZKRITERIEN:\n- Build Exit-Code 0\n- Pagefind-Index vorhanden\n- Build-Statistiken Report\n- Bei Fehler: Task blocken mit Fehlerdetails",
    "integrator",
    parents=gate_parents)
create_task(conns[1], "t_build_gate",
    "QUALITY GATE: Build + Pagefind + Report",
    "PROJEKT-PFAD: " + PROJEKT + "\n--\nAUFGABE: Finaler Build-Test nach Phase 1.",
    "integrator",
    parents=gate_parents)

# Verify
for i, conn in enumerate(conns):
    cur = conn.cursor()
    cur.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
    rows = cur.fetchall()
    print(f"DB {i} ({os.path.basename(os.path.dirname(DB_PATHS[i]))}): {dict(rows)} total={sum(r[1] for r in rows)}")
    cur.execute("SELECT id, title, status, assignee FROM tasks ORDER BY priority, created_at")
    for row in cur.fetchall():
        parents_str = ""
        if row[2] == "todo":
            cur2 = conn.cursor()
            cur2.execute("SELECT parent_id FROM task_links WHERE child_id=?", (row[0],))
            parents_list = [r[0] for r in cur2.fetchall()]
            if parents_list:
                parents_str = " [parents: " + ",".join(parents_list) + "]"
        print(f"  {row[0]:20s} | {row[1][:40]:40s} | {row[2]:8s} | {row[3]:15s}{parents_str}")
    conn.close()

print("\n== Phase 1 Tasks in beiden DBs gespiegelt ==")
print("5 unabhaengige Tasks (ready) + 1 Gate (todo, wartet auf Parents)")
