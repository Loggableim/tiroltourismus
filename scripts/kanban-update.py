#!/usr/bin/env python3
"""Update tirol-cicd Kanban board for t_seo_hreflang task."""
import sqlite3
from datetime import datetime, timezone

DB = r"C:\HermesPortable\home\spaces\tirol-tourismus\kanban\boards\tirol-cicd\kanban.db"

def set_running():
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE tasks SET status='running' WHERE id='t_seo_hreflang'")
    conn.commit()
    conn.close()
    print("✓ Task t_seo_hreflang set to 'running'")

def set_done():
    conn = sqlite3.connect(DB)
    ts = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE tasks SET status='done', completed_at=? WHERE id='t_seo_hreflang'",
        (ts,)
    )
    conn.commit()
    conn.close()
    print(f"✓ Task t_seo_hreflang set to 'done' at {ts}")

def check_status():
    conn = sqlite3.connect(DB)
    row = conn.execute(
        "SELECT id, status, completed_at FROM tasks WHERE id='t_seo_hreflang'"
    ).fetchone()
    conn.close()
    if row:
        print(f"  Task: {row[0]}, Status: {row[1]}, Completed: {row[2]}")
    else:
        print("  Task t_seo_hreflang not found in DB")

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "running":
        set_running()
    elif cmd == "done":
        set_done()
    else:
        check_status()
