#!/usr/bin/env python3
"""
Tirol CICD Kanban Dispatcher
- Queries both DBs for current status
- Dispatches pending tasks (max 2 concurrent) via delegate_task
- Updates both DBs to 'running' status after dispatching
- Gate check: t_phase3_gate only if ALL parents are 'done'
"""
import json
import sqlite3
import sys
import os
from pathlib import Path

SPACE_DB = Path("C:/HermesPortable/home/spaces/tirol-tourismus/kanban/boards/tirol-cicd/kanban.db")
GLOBAL_DB = Path("C:/HermesPortable/home/kanban/boards/tirol-cicd/kanban.db")
DUMP_FILE = Path("C:/HermesPortable/home/kanban/boards/tirol-cicd/last_dump.json")

def connect_db(path, label):
    """Connect to a kanban DB and return connection."""
    if not path.exists():
        print(f"ERROR: {label} DB not found at {path}")
        return None
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn

def get_tasks(conn):
    """Get all tasks sorted by priority DESC."""
    cur = conn.cursor()
    cur.execute("SELECT id, title, body, assignee, status, priority FROM tasks ORDER BY priority DESC")
    return [dict(row) for row in cur.fetchall()]

def get_links(conn):
    """Get all parent-child links."""
    cur = conn.cursor()
    cur.execute("SELECT parent_id, child_id FROM task_links")
    return [(row["parent_id"], row["child_id"]) for row in cur.fetchall()]

def get_parents_of(child_id, links):
    """Get all parent IDs for a given child task."""
    return [p for p, c in links if c == child_id]

def get_children_of(parent_id, links):
    """Get all child IDs for a given parent task."""
    return [c for p, c in links if p == parent_id]

def update_task_status(conn, task_id, new_status):
    """Update a task's status in the database."""
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    return cur.rowcount

def print_board_status(space_tasks, global_tasks, links):
    """Print a formatted board status report."""
    print("=" * 100)
    print("TIROL CICD KANBAN BOARD STATUS REPORT")
    print("=" * 100)
    
    # Build status map
    status_map = {t["id"]: t for t in space_tasks}
    
    print(f"\n{'ID':<30} {'TITLE':<50} {'STATUS':<12} {'PRIO':<6} {'ASSIGNEE':<18}")
    print("-" * 120)
    for t in space_tasks:
        tid = t["id"]
        title = (t["title"] or "")[:48]
        print(f"{tid:<30} {title:<50} {t['status']:<12} {t['priority']:<6} {t['assignee']:<18}")
    
    print(f"\n--- TASK LINKS ({len(links)} total) ---")
    parents_of_phase3 = get_parents_of("t_phase3_gate", links)
    print(f"\nParents of t_phase3_gate ({len(parents_of_phase3)}):")
    for pid in sorted(parents_of_phase3):
        task = status_map.get(pid, {})
        s = task.get("status", "unknown")
        icon = "✅" if s == "done" else "⏳" if s == "pending" else "❌"
        print(f"  {icon} {pid:<30} status={s}")
    
    print("\n--- GATE CHECK ---")
    all_parents_done = all(status_map.get(pid, {}).get("status") == "done" for pid in parents_of_phase3)
    if all_parents_done:
        print("✅ ALL PARENTS DONE — t_phase3_gate is READY to dispatch!")
    else:
        pending = [pid for pid in parents_of_phase3 if status_map.get(pid, {}).get("status") != "done"]
        print(f"⏳ t_phase3_gate BLOCKED — {len(pending)} parent(s) not done:")
        for pid in pending:
            task = status_map.get(pid, {})
            print(f"   ❌ {pid:<30} status={task.get('status', 'unknown')} — \"{task.get('title', '')}\"")
    
    running_tasks = [t for t in space_tasks if t["status"] == "running"]
    if running_tasks:
        print(f"\n--- RUNNING TASKS ({len(running_tasks)}) ---")
        for t in running_tasks:
            print(f"  🔄 {t['id']:<30} \"{t.get('title', '')}\"")
    
    pending_tasks = [t for t in space_tasks if t["status"] == "pending"]
    print(f"\n--- PENDING TASKS ({len(pending_tasks)}) ---")
    for t in sorted(pending_tasks, key=lambda x: x["priority"], reverse=True):
        print(f"  ⏳ {t['id']:<30} prio={t['priority']} \"{t.get('title', '')}\"")
    
    return pending_tasks, running_tasks

def dispatch_task(conn_space, conn_global, task_id, title, status_map):
    """Dispatch a task by writing a JSON dispatch command and updating DBs."""
    print(f"\n{'='*60}")
    print(f"DISPATCHING: {task_id} — \"{title}\"")
    
    # Write dispatch command file
    dispatch_dir = Path("C:/HermesPortable/home/kanban/boards/tirol-cicd/dispatches")
    dispatch_dir.mkdir(parents=True, exist_ok=True)
    dispatch_file = dispatch_dir / f"{task_id}.dispatch.json"
    
    dispatch_cmd = {
        "task_id": task_id,
        "title": title,
        "action": "dispatch",
        "toolsets": ["file", "terminal", "web"],
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }
    
    dispatch_file.write_text(json.dumps(dispatch_cmd, indent=2))
    print(f"  📝 Dispatch command written: {dispatch_file}")
    
    # Update space DB
    rc1 = update_task_status(conn_space, task_id, "running")
    print(f"  🗄️  Space DB updated: {rc1} row(s) changed to 'running'")
    
    # Update global DB
    rc2 = update_task_status(conn_global, task_id, "running")
    print(f"  🗄️  Global DB updated: {rc2} row(s) changed to 'running'")
    
    print(f"  ✅ DISPATCHED: {task_id}")
    return True

def main():
    print("=== TIROL CICD KANBAN DISPATCHER ===")
    print(f"Time: {__import__('datetime').datetime.now().isoformat()}")
    print()
    
    # Connect to both DBs
    conn_space = connect_db(SPACE_DB, "Space")
    conn_global = connect_db(GLOBAL_DB, "Global")
    
    if not conn_space or not conn_global:
        print("ERROR: Cannot connect to one or both databases")
        sys.exit(1)
    
    # Get tasks and links (use space DB as authoritative for display)
    space_tasks = get_tasks(conn_space)
    global_tasks = get_tasks(conn_global)
    links = get_links(conn_space)
    
    status_map = {t["id"]: t for t in space_tasks}
    
    # Print full board status
    pending_tasks, running_tasks = print_board_status(space_tasks, global_tasks, links)
    
    # Check for already running tasks
    already_running = len(running_tasks)
    print(f"\n\nAlready running: {already_running}")
    max_new = max(0, 2 - already_running)
    print(f"Can dispatch up to {max_new} new task(s)")
    
    if max_new <= 0:
        print("⏸️  Already at max concurrent tasks (2). Skipping dispatch.")
        print()
        print("=== SUMMARY ===")
        print(f"Total tasks: {len(space_tasks)}")
        pending_count = len(pending_tasks)
        done_count = len([t for t in space_tasks if t["status"] == "done"])
        running_count = already_running
        print(f"Done: {done_count} | Running: {running_count} | Pending: {pending_count}")
        conn_space.close()
        conn_global.close()
        return
    
    # Determine dispatch candidates
    # PRIORITY ORDER: highest priority first, then by dependency readiness
    dispatchable = []
    
    for t in sorted(pending_tasks, key=lambda x: x["priority"], reverse=True):
        tid = t["id"]
        
        if tid == "t_phase3_gate":
            # Gate: check ALL parents are done
            parents = get_parents_of(tid, links)
            all_done = all(status_map.get(pid, {}).get("status") == "done" for pid in parents)
            if all_done:
                dispatchable.append(t)
                print(f"\n✅ GATE CHECK PASSED: t_phase3_gate — all {len(parents)} parents done!")
            else:
                pending_parents = [pid for pid in parents if status_map.get(pid, {}).get("status") != "done"]
                print(f"\n⏳ GATE CHECK FAILED: t_phase3_gate — {len(pending_parents)} parent(s) still pending")
                for pp in pending_parents:
                    print(f"   ❌ {pp}: {status_map.get(pp, {}).get('status', 'unknown')}")
        else:
            # Regular task: can dispatch if no blocking conditions
            dispatchable.append(t)
    
    # Take max `max_new` tasks
    to_dispatch = dispatchable[:max_new]
    
    if not to_dispatch:
        print("\nNo tasks ready to dispatch.")
    else:
        print(f"\n\n{'='*60}")
        print(f"DISPATCHING {len(to_dispatch)} TASK(S):")
        for t in to_dispatch:
            print(f"  ➡️  {t['id']:<30} prio={t['priority']} \"{t.get('title', '')[:50]}\"")
        
        for t in to_dispatch:
            dispatch_task(conn_space, conn_global, t["id"], t.get("title", ""), status_map)
    
    print()
    print("=== FINAL SUMMARY ===")
    # Re-read to get updated counts
    space_tasks = get_tasks(conn_space)
    done_count = len([t for t in space_tasks if t["status"] == "done"])
    running_count = len([t for t in space_tasks if t["status"] == "running"])
    pending_count = len([t for t in space_tasks if t["status"] == "pending"])
    print(f"Total tasks: {len(space_tasks)}")
    print(f"Done: {done_count} | Running: {running_count} | Pending: {pending_count}")
    print(f"Dispatched this run: {len(to_dispatch)}")
    
    conn_space.close()
    conn_global.close()
    print("\nDone.")

if __name__ == "__main__":
    main()