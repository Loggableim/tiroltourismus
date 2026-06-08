#!/usr/bin/env python3
"""
Orte Catchup Script — Commits the 66 already-processed Orte and
resumes the pipeline for remaining ~192 Orte.

Usage:
  python scripts/orte_catchup.py              # Run full catchup
  python scripts/orte_catchup.py --commit-only # Only commit existing data
  python scripts/orte_catchup.py --batch N     # Process next N Orte
"""
import sys, json, os, time, subprocess, re, urllib.request, urllib.error, sqlite3
from pathlib import Path

BASE = Path("F:/tiroltourismus")
ORTE_DIR = BASE / "src" / "data" / "orte"
STATE_FILE = BASE / "_orte_pipeline.json"
PUBLIC_ORTE_IMG = BASE / "public" / "images" / "orte"
KANBAN_DBS = [
    Path(r"C:/HermesPortable/home/spaces/tirol-tourismus/kanban/boards/tirol-cicd/kanban.db"),
    Path(r"C:/HermesPortable/home/kanban/boards/tirol-cicd/kanban.db"),
]
LANGUAGES = ['en', 'fr', 'it', 'es', 'zh', 'nl']

ALL_SLUGS = sorted([
    d for d in os.listdir(ORTE_DIR)
    if os.path.isdir(ORTE_DIR / d)
])

print(f"📊 Total Orte in src/data/orte/: {len(ALL_SLUGS)}")

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding='utf-8'))
    return {"idx": 0, "done": []}

def save_state(s):
    STATE_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding='utf-8')

def is_enriched(slug):
    """Check if an Ort has been fully enriched by the pipeline."""
    fp = ORTE_DIR / slug / "index.json"
    if not fp.exists():
        return False
    data = json.loads(fp.read_text(encoding='utf-8'))
    has_beschreibung = bool(data.get('beschreibung'))
    has_kategorie = bool(data.get('kategorie'))
    has_hero = bool(data.get('hero_bild'))
    return has_beschreibung and has_kategorie and has_hero

def commit_slug(slug, msg_extra=""):
    """Git add, commit, and push for a single slug."""
    # Ensure git user config
    for cfg in [("user.name", "Tirol Bot"), ("user.email", "bot@tiroltourismus.com")]:
        chk = subprocess.run(["git", "config", cfg[0]], capture_output=True, text=True, cwd=str(BASE), timeout=10)
        if not chk.stdout.strip():
            subprocess.run(["git", "config", cfg[0], cfg[1]], capture_output=True, text=True, cwd=str(BASE), timeout=10)
    
    # Add files
    add_patterns = [
        f"src/data/orte/{slug}/",
        f"src/data/*/orte/{slug}/",
        f"public/images/orte/{slug}/",
    ]
    result = subprocess.run(
        ["git", "add", "-A"] + add_patterns,
        capture_output=True, text=True, cwd=str(BASE), timeout=30
    )
    if result.returncode != 0:
        print(f"  ❌ git add fehlgeschlagen: {result.stderr[:200]}")
        return False
    
    # Check if there's anything to commit
    diff_check = subprocess.run(
        ["git", "diff", "--cached", "--stat"],
        capture_output=True, text=True, cwd=str(BASE), timeout=10
    )
    if not diff_check.stdout.strip():
        print(f"  ℹ️  Keine Änderungen für {slug}")
        return False
    
    # Commit
    msg = f"[orte] ✨ {slug}: Beschreibung, Bilder & Infos"
    if msg_extra:
        msg += f" ({msg_extra})"
    result2 = subprocess.run(
        ["git", "commit", "-m", msg],
        capture_output=True, text=True, cwd=str(BASE), timeout=30
    )
    if result2.returncode != 0:
        print(f"  ❌ Commit fehlgeschlagen: {result2.stderr[:200]}")
        return False
    print(f"  ✅ Committed: {result2.stdout.split(chr(10))[0] if result2.stdout else 'ok'}")
    
    # Push
    push = subprocess.run(
        ["git", "push", "origin", "master"],
        capture_output=True, text=True, cwd=str(BASE), timeout=60
    )
    if push.returncode == 0:
        print(f"  🚀 Gepusht!")
        return True
    else:
        # Try configured branch
        branch_chk = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=str(BASE), timeout=10)
        branch = branch_chk.stdout.strip()
        if branch and branch != "master":
            push2 = subprocess.run(["git", "push", "origin", branch], capture_output=True, text=True, cwd=str(BASE), timeout=60)
            if push2.returncode == 0:
                print(f"  🚀 Gepusht auf {branch}!")
                return True
        print(f"  ⚠️  Push zurückgestellt (wird vom nächsten Tick übernommen)")
        return True  # Don't block on push failures

def step1_commit_done_orte(state):
    """Commit all already-processed Orte that haven't been committed."""
    done = state.get("done", [])
    print(f"\n{'='*60}")
    print(f"📦 STEP 1: Committing {len(done)} already-processed Orte")
    print(f"{'='*60}")
    
    committed = 0
    for slug in done:
        if not is_enriched(slug):
            print(f"  ⏭️  {slug}: nicht vollständig angereichert, überspringe")
            continue
        print(f"\n  📍 {slug}...")
        ok = commit_slug(slug, "catchup")
        if ok:
            committed += 1
        time.sleep(1)  # Rate limit for git
    
    print(f"\n✅ STEP 1 done: {committed}/{len(done)} Orte committed")
    return committed

def step2_fix_translations(state):
    """Regenerate translation files for all done Orte."""
    done = state.get("done", [])
    print(f"\n{'='*60}")
    print(f"🌐 STEP 2: Regenerating translations for {len(done)} Orte")
    print(f"{'='*60}")
    
    fixed = 0
    for slug in done:
        fp = ORTE_DIR / slug / "index.json"
        if not fp.exists():
            continue
        data = json.loads(fp.read_text(encoding='utf-8'))
        beschreibung = data.get('beschreibung', '')
        if not beschreibung:
            continue
        
        print(f"\n  📍 {slug}...")
        for lang in LANGUAGES:
            lang_dir = BASE / "src" / "data" / lang / "orte" / slug
            lang_dir.mkdir(parents=True, exist_ok=True)
            lang_file = lang_dir / "index.json"
            
            # Build fresh translation data with enriched fields
            lang_data = {
                "name": data.get('name'),
                "slug": slug,
                "region": data.get('region'),
                "kurzbeschreibung": data.get('kurzbeschreibung'),
                "beschreibung": beschreibung,
                "hero_bild": data.get('hero_bild'),
                "koordinaten": data.get('koordinaten'),
                "hoehe": data.get('hoehe'),
                "bilder": data.get('bilder', []),
                "tags": data.get('tags', []),
                "kategorie": data.get('kategorie'),
                "bezirk": data.get('bezirk'),
                "status": "published",
            }
            lang_file.write_text(json.dumps(lang_data, indent=2, ensure_ascii=False), encoding='utf-8')
            print(f"    ✅ {lang}: index.json aktualisiert")
            fixed += 1
        
        time.sleep(0.5)
    
    print(f"\n✅ STEP 2 done: {fixed} translation files updated")
    return fixed

def step3_process_remaining(state, batch_size=10):
    """Process remaining Orte using LLM content generation."""
    state = load_state()
    idx = state["idx"]
    done_set = set(state.get("done", []))
    
    print(f"\n{'='*60}")
    print(f"🔄 STEP 3: Processing remaining Orte (next {batch_size})")
    print(f"{'='*60}")
    print(f"Current idx: {idx}, done: {len(done_set)}, total: {len(ALL_SLUGS)}")
    
    # Find the actual next unprocessed slug
    next_idx = idx
    while next_idx < len(ALL_SLUGS):
        slug = ALL_SLUGS[next_idx]
        if slug not in done_set:
            break
        next_idx += 1
    
    if next_idx >= len(ALL_SLUGS):
        print("🎉 ALLE ORTE BEREITS VERARBEITET!")
        return 0
    
    processed = 0
    batch_count = 0
    while next_idx < len(ALL_SLUGS) and batch_count < batch_size:
        slug = ALL_SLUGS[next_idx]
        if slug in done_set:
            next_idx += 1
            continue
        
        print(f"\n{'='*50}")
        print(f"📍 ({next_idx+1}/{len(ALL_SLUGS)}) Processing: {slug}")
        print(f"{'='*50}")
        
        # Import pipeline modules
        sys.path.insert(0, str(BASE / "scripts"))
        from orte_pipeline import get_orte_data, save_orte_data, step_enrich, step_image, step_translate, step_commit
        
        data = get_orte_data(slug)
        if not data:
            print(f"⚠️  Keine Daten für {slug}, überspringe")
            next_idx += 1
            continue
        
        print(f"\n📝 Step 1: Content generieren...")
        changed, data = step_enrich(slug, data)
        
        print(f"\n🎨 Step 2: Bild generieren...")
        img_changed, data = step_image(slug, data)
        changed = changed or img_changed
        
        if changed:
            save_orte_data(slug, data)
            print(f"  ✅ DE data saved")
        
        print(f"\n🌐 Step 3: Übersetzen...")
        step_translate(slug, data)
        
        print(f"\n📦 Step 4: Committen...")
        step_commit(slug)
        
        # Update state
        state["idx"] = next_idx + 1
        state["done"].append(slug)
        save_state(state)
        
        processed += 1
        batch_count += 1
        next_idx += 1
        
        print(f"\n✅ {slug} abgeschlossen! ({len(state['done'])}/{len(ALL_SLUGS)})\n")
    
    return processed

def update_kanban():
    """Mark t_orte_pipeline as 'running' on Kanban board."""
    now = time.time()
    print(f"\n{'='*60}")
    print(f"📋 Updating Kanban board...")
    for db_path in KANBAN_DBS:
        if not db_path.exists():
            print(f"  ⚠️  Kanban-DB nicht gefunden: {db_path}")
            continue
        try:
            conn = sqlite3.connect(str(db_path))
            # Check if the task exists
            existing = conn.execute("SELECT id, status FROM tasks WHERE id='t_orte_pipeline'").fetchone()
            if existing:
                conn.execute(
                    "UPDATE tasks SET status='running', updated_at=? WHERE id='t_orte_pipeline'",
                    (now,)
                )
                print(f"  ✅ {db_path.name}: t_orte_pipeline -> running")
            else:
                print(f"  ⚠️  Task t_orte_pipeline nicht in {db_path.name}")
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"  ❌ Fehler: {e}")

def set_kanban_done(result_msg):
    """Mark t_orte_pipeline as 'done' on Kanban board."""
    now = time.time()
    print(f"\n{'='*60}")
    print(f"✅ Marking Kanban task as done...")
    for db_path in KANBAN_DBS:
        if not db_path.exists():
            print(f"  ⚠️  Kanban-DB nicht gefunden: {db_path}")
            continue
        try:
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
            print(f"  ✅ {db_path.name}/t_orte_pipeline: {after}")
            conn.close()
        except Exception as e:
            print(f"  ❌ Fehler bei {db_path}: {e}")

def check_git_status():
    """Check git status and print summary."""
    print(f"\n{'='*60}")
    print(f"🔍 Git Status Check")
    print(f"{'='*60}")
    
    # Check if it's a git repo
    git_dir = BASE / ".git"
    if not git_dir.exists():
        print("❌ Kein Git-Repository gefunden!")
        return False
    
    # Check git status
    status = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=str(BASE), timeout=10)
    print(f"Git Status ({len(status.stdout.strip().split(chr(10))) if status.stdout.strip() else 0} Änderungen):")
    if status.stdout.strip():
        for line in status.stdout.strip().split(chr(10)):
            print(f"  {line}")
    
    # Check remote
    remote = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True, cwd=str(BASE), timeout=10)
    if remote.stdout.strip():
        print(f"\nRemote:")
        for line in remote.stdout.strip().split(chr(10)):
            print(f"  {line}")
    else:
        print(f"\n⚠️  Kein Remote konfiguriert!")
    
    # Check git config
    user_name = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True, cwd=str(BASE), timeout=10)
    user_email = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True, cwd=str(BASE), timeout=10)
    print(f"\nGit Config:")
    print(f"  user.name: {user_name.stdout.strip() or '❌ NICHT GESETZT'}")
    print(f"  user.email: {user_email.stdout.strip() or '❌ NICHT GESETZT'}")
    
    branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=str(BASE), timeout=10)
    print(f"  branch: {branch.stdout.strip() or '❌ UNKNOWN'}")
    
    return True

def analyze_enriched():
    """Analyze which Orte are enriched vs not."""
    enriched = []
    not_enriched = []
    for slug in ALL_SLUGS:
        if is_enriched(slug):
            enriched.append(slug)
        else:
            not_enriched.append(slug)
    print(f"\n📊 Enrichment Status:")
    print(f"  ✅ Enriched: {len(enriched)}")
    print(f"  ⬜ Not enriched: {len(not_enriched)}")
    return enriched, not_enriched

def main():
    print("=" * 60)
    print("🏔️  ORTE PIPELINE CATCHUP & FIX")
    print(f"   Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    state = load_state()
    print(f"\nState: idx={state['idx']}, done={len(state.get('done', []))}")
    
    # Step 0: Check git
    git_ok = check_git_status()
    
    # Step 0.5: Analyze enrichment status
    enriched, not_enriched = analyze_enriched()
    
    # Step 1: Update Kanban to running
    update_kanban()
    
    # Step 2: Fix translation files (update with enriched data)
    step2_fix_translations(state)
    
    # Step 3: Commit all done Orte
    step1_commit_done_orte(state)
    
    # Step 4: Process remaining batch
    args = sys.argv[1:]
    batch_size = 10
    if "--batch" in args:
        idx = args.index("--batch")
        if idx + 1 < len(args):
            batch_size = int(args[idx + 1])
    
    if "--commit-only" not in args:
        processed = step3_process_remaining(state, batch_size)
        if processed > 0:
            print(f"\n✅ Processed {processed} new Orte")
    
    # Final summary
    state = load_state()
    enriched_now, not_enriched_now = analyze_enriched()
    print(f"\n{'='*60}")
    print(f"📊 FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"  Total Orte: {len(ALL_SLUGS)}")
    print(f"  In state done: {len(state.get('done', []))}")
    print(f"  Enriched (DE data complete): {len(enriched_now)}")
    print(f"  Remaining to enrich: {len(not_enriched_now)}")
    print(f"  State idx: {state['idx']}")
    print(f"  Next to process: {ALL_SLUGS[state['idx']] if state['idx'] < len(ALL_SLUGS) else 'ALL DONE'}")
    
    # If all done, mark Kanban as done
    if state["idx"] >= len(ALL_SLUGS):
        print(f"\n🎉 ALLE {len(ALL_SLUGS)} ORTE FERTIG!")
        set_kanban_done(f"Orte-Pipeline abgeschlossen: {len(ALL_SLUGS)}/{len(ALL_SLUGS)} Orte angereichert")
    else:
        print(f"\n⏱️  Pipeline läuft weiter. Nächster Cron-Tick verarbeitet {ALL_SLUGS[state['idx']]}")
    
    print(f"\n✅ Catchup complete at {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
