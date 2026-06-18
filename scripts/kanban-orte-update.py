#!/usr/bin/env python3
"""Update Kanban board for t_orte_pipeline task."""
import sqlite3
import time
from pathlib import Path

KANBAN_DBS = [
    Path(r"C:/HermesPortable/home/spaces/tirol-tourismus/kanban/boards/tirol-cicd/kanban.db"),
    Path(r"C:/HermesPortable/home/kanban/boards/tirol-cicd/kanban.db"),
]

def mark_running():
    now = time.time()
    for db_path in KANBAN_DBS:
        if not db_path.exists():
            print(f"⚠️  DB not found: {db_path}")
            continue
        conn = sqlite3.connect(str(db_path))
        cur = conn.execute("SELECT id, status FROM tasks WHERE id='t_orte_pipeline'")
        row = cur.fetchone()
        if row:
            conn.execute("UPDATE tasks SET status='running', updated_at=? WHERE id='t_orte_pipeline'", (now,))
            conn.commit()
            print(f"✅ {db_path.name}: t_orte_pipeline -> running")
        else:
            print(f"⚠️  Task t_orte_pipeline not found in {db_path.name}")
        conn.close()

def mark_done(result_msg="Pipeline completed successfully"):
    now = time.time()
    for db_path in KANBAN_DBS:
        if not db_path.exists():
            print(f"⚠️  DB not found: {db_path}")
            continue
        conn = sqlite3.connect(str(db_path))
        cols = {row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()}
        sets = ["status=?"]
        vals = ["done"]
        if "updated_at" in cols:
            sets.append("updated_at=?")
            vals.append(now)
        if "completed_at" in cols:
            sets.append("completed_at=?")
            vals.append(now)
        if "result" in cols:
            sets.append("result=?")
            vals.append(result_msg)
        vals.append("t_orte_pipeline")
        conn.execute(f"UPDATE tasks SET {', '.join(sets)} WHERE id=?", vals)
        conn.commit()
        after = conn.execute("SELECT id, status FROM tasks WHERE id='t_orte_pipeline'").fetchone()
        print(f"✅ {db_path.name}/t_orte_pipeline: {after}")
        conn.close()

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "running":
        mark_running()
    elif cmd == "done":
        mark_done()
    else:
        for db_path in KANBAN_DBS:
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                row = conn.execute("SELECT id, status FROM tasks WHERE id='t_orte_pipeline'").fetchone()
                print(f"{db_path.name}: {row}" if row else f"{db_path.name}: task not found")
                conn.close()
