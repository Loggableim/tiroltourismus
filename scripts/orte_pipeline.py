#!/usr/bin/env python3
"""
Orte-Pipeline: Enrichment + Bilder + Übersetzung in einem Durchgang.
Läuft als no_agent Cron — 1 Ort pro Tick, dann Commit + Push.
VISUAL FALLBACK: SVG Gradient Placeholder statt SDXL (kein GPU nötig).
"""
import sys, json, os, time, subprocess, re, urllib.request, urllib.error, hashlib, sqlite3
from pathlib import Path

BASE = Path("F:/tiroltourismus")
ORTE_DIR = BASE / "src" / "data" / "orte"
STATE_FILE = BASE / "_orte_pipeline.json"
PUBLIC_IMG = BASE / "public" / "images" / "orte"
PUBLIC_ORTE_IMG = BASE / "public" / "images" / "orte"
KANBAN_DBS = [
    Path(r"C:/HermesPortable/home/spaces/tirol-tourismus/kanban/boards/tirol-cicd/kanban.db"),
    Path(r"C:/HermesPortable/home/kanban/boards/tirol-cicd/kanban.db"),
]

# Visual Fallback mode — skip SDXL image gen, use SVG gradient placeholders
# This makes the pipeline much faster and eliminates GPU/CUDA dependencies
VISUAL_FALLBACK = True

# Alle 258 Orte slugs
ALL_SLUGS = sorted([
    d for d in os.listdir(ORTE_DIR)
    if os.path.isdir(ORTE_DIR / d)
])

LANGUAGES = ['en', 'fr', 'it', 'es', 'zh', 'nl']

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding='utf-8'))
    return {"idx": 0, "done": []}

def save_state(s):
    STATE_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding='utf-8')

def mark_kanban_task_done(task_id, result):
    """Markiert einen tirol-cicd Task in beiden DBs als done (idempotent)."""
    now = time.time()
    for db in KANBAN_DBS:
        if not db.exists():
            print(f"  ⚠️  Kanban-DB fehlt: {db}")
            continue
        try:
            conn = sqlite3.connect(str(db))
            cols = {row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()}
            sets = ["status=?"]
            vals = ["done"]
            if "updated_at" in cols:
                sets.append("updated_at=?"); vals.append(now)
            if "completed_at" in cols:
                sets.append("completed_at=?"); vals.append(now)
            if "result" in cols:
                sets.append("result=?"); vals.append(result)
            vals.append(task_id)
            conn.execute(f"UPDATE tasks SET {', '.join(sets)} WHERE id=?", vals)
            conn.commit()
            after = conn.execute("SELECT id, status FROM tasks WHERE id=?", (task_id,)).fetchone()
            conn.close()
            print(f"  ✅ Kanban {db.name}/{task_id}: {after}")
        except Exception as e:
            print(f"  ⚠️  Kanban-Update Fehler {db}: {e}")

def get_orte_data(slug):
    fp = ORTE_DIR / slug / "index.json"
    if not fp.exists():
        return None
    return json.loads(fp.read_text(encoding='utf-8'))

def save_orte_data(slug, data):
    fp = ORTE_DIR / slug / "index.json"
    fp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

def _load_env_key(key_name):
    """Load a key from environment or .env files."""
    val = os.environ.get(key_name, "")
    if val:
        return val
    env_paths = [
        "C:/HermesPortable/home/.env",
        "E:/HermesPortable/home/.env",
        os.path.expanduser("~/.hermes/.env"),
    ]
    for ep in env_paths:
        if os.path.exists(ep):
            for line in open(ep):
                if line.startswith(f"{key_name}="):
                    val = line.strip().split("=", 1)[1]
                    return val
    return ""

def _llm_call(url, api_key, model, body, system, prompt, timeout=60):
    """Single LLM API call with error handling."""
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Mozilla/5.0")
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        return resp["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        code, msg = e.code, e.read().decode()[:150]
        print(f"  ⚠️  LLM-API {code}: {msg}")
        return None
    except Exception as e:
        print(f"  ⚠️  LLM-Fehler: {e}")
        return None

def call_llm(prompt, system="Du bist ein Tirol-Reiseexperte. Antworte präzise auf Deutsch."):
    """Ruft LLM API für Content-Generierung auf (Multi-Provider Fallback).
    
    Fallback-Kette:
      1. OpenRouter (deepseek-v4-flash) — primär
      2. OpenCode Go (deepseek-v4-flash) — fallback
      3. Cerebras (llama3.1-8b) — last resort
    """
    body = json.dumps({
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.7,
    }).encode()
    
    providers = [
        ("OpenRouter", "https://openrouter.ai/api/v1/chat/completions",
         _load_env_key("OPENROUTER_API_KEY"), "deepseek-v4-flash"),
        ("OpenCode Go", "https://opencode.ai/zen/go/v1/chat/completions",
         _load_env_key("OPENCODE_GO_API_KEY"), "deepseek-v4-flash"),
        ("Cerebras", "https://api.cerebras.ai/v1/chat/completions",
         _load_env_key("CEREBRAS_API_KEY"), "llama3.1-8b"),
    ]
    
    for name, url, api_key, model in providers:
        if not api_key:
            continue
        # Use correct model name per provider
        if model != "deepseek-v4-flash":
            body = json.dumps({
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1024,
                "temperature": 0.7,
            }).encode()
        print(f"  🔄 LLM via {name} ({model})...")
        result = _llm_call(url, api_key, model, body, system, prompt)
        if result:
            return result
        print(f"  ⏭️  {name} fehlgeschlagen, nächster Provider...")
    
    print("⚠️  Alle LLM-Provider fehlgeschlagen — überspringe LLM-Schritt")
    return None

def generate_svg_image(slug, name, region, farbe="#006400"):
    """Generates an SVG gradient placeholder image instead of SDXL.
    Visual Fallback: creates a beautiful gradient with the ort's color."""
    img_dir = PUBLIC_ORTE_IMG / slug
    img_dir.mkdir(parents=True, exist_ok=True)
    hero_path = img_dir / "hero_1.png"
    
    if hero_path.exists() and hero_path.stat().st_size > 100:
        print(f"  ✅ Bild existiert bereits")
        return f"/images/orte/{slug}/hero_1.png"
    
    # Use the ort's farbe if available, otherwise derive from slug
    if not farbe or farbe == "#000000":
        # Derive a nice color from the slug hash
        h = abs(hash(slug)) % 360
        farbe = f"hsl({h}, 60%, 35%)"
    
    # Generate an SVG gradient with the ort's theme color
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{farbe};stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1a1a2e;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="mountains" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:{farbe};stop-opacity:0.3" />
      <stop offset="100%" style="stop-color:{farbe};stop-opacity:0.1" />
    </linearGradient>
  </defs>
  <rect width="1024" height="1024" fill="url(#bg)" />
  <!-- Simplified mountain silhouette -->
  <polygon points="0,700 200,450 350,580 500,350 700,550 850,400 1024,600 1024,1024 0,1024" 
           fill="url(#mountains)" opacity="0.6"/>
  <polygon points="0,800 150,600 300,700 450,550 600,680 800,520 1024,680 1024,1024 0,1024" 
           fill="{farbe}" opacity="0.3"/>
  <!-- Sun/moon circle -->
  <circle cx="750" cy="280" r="60" fill="#ffd700" opacity="0.3"/>
  <!-- Ort name watermark -->
  <text x="512" y="900" text-anchor="middle" font-family="Georgia, serif" 
        font-size="48" fill="white" opacity="0.15">{name}</text>
</svg>'''
    
    tmp_svg = img_dir / "_hero_temp.svg"
    tmp_svg.write_text(svg, encoding='utf-8')
    
    # Convert SVG to PNG using cairosvg if available, otherwise keep as SVG
    try:
        import cairosvg
        cairosvg.svg2png(url=str(tmp_svg), write_to=str(hero_path), output_width=1024, output_height=1024)
        tmp_svg.unlink(missing_ok=True)
        kb = hero_path.stat().st_size / 1024
        print(f"  ✅ SVG→PNG Gradient ({kb:.0f} KB)")
        return f"/images/orte/{slug}/hero_1.png"
    except ImportError:
        # cairosvg not available — serve SVG directly
        hero_svg = img_dir / "hero_1.svg"
        tmp_svg.rename(hero_svg)
        print(f"  ✅ SVG Gradient (cairosvg not available, using .svg)")
        return f"/images/orte/{slug}/hero_1.svg"
    except Exception as e:
        print(f"  ⚠️ SVG→PNG failed ({e}), keeping SVG")
        hero_svg = img_dir / "hero_1.svg"
        tmp_svg.rename(hero_svg)
        return f"/images/orte/{slug}/hero_1.svg"

def translate_text(text, target_lang):
    """Übersetzt einen Text in die Zielsprache."""
    # Nutzt den existierenden translation worker
    # Für MVP: einfacher Prompt
    if not text or len(text.strip()) < 10:
        return text
    
    lang_names = {'en': 'English', 'fr': 'French', 'it': 'Italian', 
                  'es': 'Spanish', 'zh': 'Chinese', 'nl': 'Dutch'}
    lang_name = lang_names.get(target_lang, target_lang)
    
    prompt = f"""Translate this German tourism text into {lang_name}:
STRICT RULES:
- Keep ALL place names in original German (Tirol, Innsbruck, Achensee, etc.)
- NO explanations, NO notes, NO comments
- Output ONLY the translated text, nothing else

Text: {text}"""
    
    return call_llm(prompt, "You are a professional tourism translator.")

# ═══════════════════════════════════════════
# PIPELINE STEPS
# ═══════════════════════════════════════════

def step_enrich(slug, data):
    """Step 1: Beschreibung, Sehenswürdigkeiten, Kategorie, Website, Fläche generieren"""
    name = data.get('name', slug)
    kurz = data.get('kurzbeschreibung', '')
    region = data.get('region', '')
    bezirk = data.get('bezirk', '')
    hoehe = data.get('hoehe', '')
    tags = data.get('tags', [])
    
    # Fix: hoehe sometimes has " m" suffix
    hoehe_str = str(hoehe).replace(' m', '').replace('m', '').strip()
    try:
        hoehe_int = int(float(hoehe_str))
    except:
        hoehe_int = 800
    
    changed = False
    
    # 1a: Lange Beschreibung generieren
    if not data.get('beschreibung'):
        prompt = f"""Schreibe eine reichhaltige, einladende Beschreibung (150-250 Wörter) für {name} in Tirol.
Infos: Höhe {hoehe_int}m, Bezirk {bezirk}, Region {region}, Tags: {', '.join(tags)}.
Kurzbeschreibung: {kurz}

Format: Reiner HTML-Text mit <p>-Tags. Keine Überschriften. Nenne Besonderheiten, 
landschaftliche Highlights, was den Ort besonders macht. Lockend und informativ."""
        
        desc = call_llm(prompt)
        if desc and len(desc) > 100:
            data['beschreibung'] = desc
            changed = True
            print(f"  ✅ beschreibung generiert ({len(desc)} Zeichen)")
    
    # 1b: Sehenswürdigkeiten
    if not data.get('sehenswuerdigkeiten'):
        prompt = f"""Liste 3-5 konkrete Sehenswürdigkeiten in und um {name} in Tirol auf.
Gib jede als JSON-Objekt mit: name (string), beschreibung (1 Satz), typ (natur/kultur/ausflug).
Antworte NUR mit dem JSON-Array, nichts anderem.

Beispiel: [{{"name": "Schloss Landeck", "beschreibung": "Mittelalterliche Burg mit Museum und Panoramablick.", "typ": "kultur"}}]"""
        
        result = call_llm(prompt)
        if result:
            # Try to parse JSON from response
            import re
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                try:
                    sights = json.loads(json_match.group())
                    data['sehenswuerdigkeiten'] = sights
                    changed = True
                    print(f"  ✅ {len(sights)} Sehenswürdigkeiten gefunden")
                except:
                    print(f"  ⚠️  JSON-Parsing fehlgeschlagen: {result[:100]}")
    
    # 1c: Kategorie
    if not data.get('kategorie'):
        # Determine from data
        if bezirk and bezirk != 'innsbruck':
            cat = 'dorf' if hoehe_int > 800 else 'marktgemeinde'
        else:
            cat = 'dorf'
        # Simple heuristic — could be smarter
        lower_name = name.lower()
        tag_str = ' '.join(tags).lower()
        
        if 'stadt' in tag_str or name in ['Innsbruck', 'Landeck', 'Kufstein', 'Hall in Tirol', 'Schwaz']:
            cat = 'stadt'
        elif 'bergdorf' in tag_str or hoehe_int > 1200:
            cat = 'bergdorf'
        elif 'see' in tag_str or 'see' in lower_name:
            cat = 'seeort'
        
        data['kategorie'] = cat
        changed = True
        print(f"  ✅ Kategorie: {cat}")
    
    return changed, data

def step_image(slug, data):
    """Step 2: Hero-Bild generieren (Visual Fallback: SVG Gradient)
    Skip SDXL — use beautiful CSS/SVG gradient placeholders."""
    if data.get('hero_bild'):
        return False, data  # Already has image
    
    name = data.get('name', slug)
    region = data.get('region', '')
    farbe = data.get('farbe', '#006400')
    
    hero_path = generate_svg_image(slug, name, region, farbe)
    if hero_path:
        data['hero_bild'] = hero_path
        ext = hero_path.split('.')[-1]
        data['bilder'] = [{"url": hero_path, "alt": f"{name} — Visual"}]
        print(f"  ✅ Visual Fallback: hero_bild={hero_path}")
        return True, data
    
    return False, data

def step_translate(slug, data):
    """Step 3: Beschreibung in alle Sprachen übersetzen (überschreibt bestehende Dateien)"""
    beschreibung = data.get('beschreibung', '')
    if not beschreibung:
        print("  ℹ️  Keine Beschreibung zum Übersetzen vorhanden")
        return
    
    for lang in LANGUAGES:
        lang_dir = BASE / "src" / "data" / lang / "orte" / slug
        lang_file = lang_dir / "index.json"
        
        # Create directory (overwrite existing files)
        lang_dir.mkdir(parents=True, exist_ok=True)
        
        # Translate beschreibung
        trans = translate_text(beschreibung, lang)
        if trans:
            lang_data = {
                "name": data.get('name'),
                "slug": slug,
                "region": data.get('region'),
                "kurzbeschreibung": translate_text(data.get('kurzbeschreibung', ''), lang) or data.get('kurzbeschreibung'),
                "beschreibung": trans,
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
            print(f"  ✅ {lang}: übersetzt")
        else:
            print(f"  ⚠️  {lang}: Übersetzung fehlgeschlagen — überspringe")

def step_commit(slug):
    """Step 4: Git Commit für diesen Ort"""
    # Ensure git is configured
    for cfg in [("user.name", "Tirol Bot"), ("user.email", "bot@tiroltourismus.com")]:
        chk = subprocess.run(["git", "config", cfg[0]], capture_output=True, text=True, cwd=str(BASE), timeout=10)
        if not chk.stdout.strip():
            subprocess.run(["git", "config", cfg[0], cfg[1]], capture_output=True, text=True, cwd=str(BASE), timeout=10)
            print(f"  🔧 Git {cfg[0]} gesetzt: {cfg[1]}")
    
    # Add ALL related files — DE source + translations + images
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
        print(f"  ⚠️  git add Fehler: {result.stderr[:300]}")
        return False
    staged_count = len([l for l in result.stdout.split(chr(10)) if l.strip()]) if result.stdout.strip() else 0
    if staged_count > 0:
        print(f"  ✅ git add: {staged_count} datei(en)")
    
    result2 = subprocess.run(
        ["git", "commit", "-m", f"[orte] ✨ {slug}: Beschreibung, Bilder & Infos"],
        capture_output=True, text=True, cwd=str(BASE), timeout=30
    )
    
    if "nothing to commit" in result2.stdout + result2.stderr:
        print("  ℹ️  Nichts zu committen (keine Änderungen)")
        return False
    
    if result2.returncode != 0:
        print(f"  ⚠️  Commit-Fehler: {result2.stderr[:300]}")
        diff = subprocess.run(["git", "diff", "--cached", "--stat"], capture_output=True, text=True, cwd=str(BASE), timeout=10)
        print(f"  📊 Staged: {diff.stdout.strip() or 'nichts'}")
        return False
    
    print(f"  ✅ Commit: {result2.stdout.split(chr(10))[0] if result2.stdout else 'ok'}")
    
    # Push with optional GITHUB_TOKEN for HTTPS auth
    push_cmd = ["git", "push", "origin", "master"]
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        # Try loading from .env
        env_path = BASE / ".env"
        if env_path.exists():
            for line in env_path.read_text().split(chr(10)):
                if line.startswith("GITHUB_TOKEN="):
                    token = line.strip().split("=", 1)[1]
    
    if token:
        # Rewrite remote URL to include token for auth
        remote_url = "https://Loggableim:" + token + "@github.com/Loggableim/tiroltourismus.git"
        subprocess.run(["git", "remote", "set-url", "origin", remote_url],
                       capture_output=True, text=True, cwd=str(BASE), timeout=10)
        print(f"  🔑 GITHUB_TOKEN konfiguriert für Push")
    
    push = subprocess.run(push_cmd, capture_output=True, text=True, cwd=str(BASE), timeout=60)
    
    if push.returncode == 0:
        print(f"  🚀 Gepusht!")
        return True
    else:
        print(f"  ⚠️  Push-Fehler: {push.stderr[:300]}")
        # Try to detect the branch name and retry
        branch_chk = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=str(BASE), timeout=10)
        branch = branch_chk.stdout.strip()
        if branch and branch != "master":
            print(f"  🔄 Versuche Push zu '{branch}' statt 'master'...")
            push2 = subprocess.run(["git", "push", "origin", branch], capture_output=True, text=True, cwd=str(BASE), timeout=60)
            if push2.returncode == 0:
                print(f"  🚀 Gepusht auf {branch}!")
                return True
            print(f"  ⚠️  Push auf {branch} auch fehlgeschlagen: {push2.stderr[:200]}")
        return False

# ═══════════════════════════════════════════
# MAIN LOOP — 1 Ort pro Aufruf
# ═══════════════════════════════════════════

def main():
    state = load_state()
    idx = state["idx"]
    
    if idx >= len(ALL_SLUGS):
        print(f"🎉 ALLE {len(ALL_SLUGS)} ORTE FERTIG!")
        mark_kanban_task_done("t_orte_pipeline", f"Orte-Pipeline abgeschlossen: {len(ALL_SLUGS)}/{len(ALL_SLUGS)} Orte angereichert")
        return
    
    slug = ALL_SLUGS[idx]
    print(f"\n{'='*60}")
    print(f"📍 ({idx+1}/{len(ALL_SLUGS)}) {slug}")
    print(f"{'='*60}")
    
    data = get_orte_data(slug)
    if not data:
        print(f"⚠️  Keine Daten für {slug}, überspringe")
        state["idx"] = idx + 1
        save_state(state)
        return
    
    # Step 1: Enrich
    print(f"\n📝 Step 1/4: Content generieren...")
    changed, data = step_enrich(slug, data)
    
    # Step 2: Image
    print(f"\n🎨 Step 2/4: Bild generieren...")
    img_changed, data = step_image(slug, data)
    changed = changed or img_changed
    
    # Save DE data
    if changed:
        save_orte_data(slug, data)
    
    # Step 3: Translate
    print(f"\n🌐 Step 3/4: Übersetzen...")
    step_translate(slug, data)
    
    # Step 4: Commit
    print(f"\n📦 Step 4/4: Committen...")
    step_commit(slug)
    
    # Advance
    state["idx"] = idx + 1
    state["done"].append(slug)
    save_state(state)
    
    print(f"\n✅ {slug} abgeschlossen! ({len(state['done'])}/{len(ALL_SLUGS)})")
    remaining = len(ALL_SLUGS) - len(state["done"])
    print(f"⏱️  Nächster Ort in 5 Minuten: {ALL_SLUGS[idx+1] if idx+1 < len(ALL_SLUGS) else '—'}")
    print(f"📊 Noch {remaining} Orte (~{remaining * 2 // 60}h bei 2min-Takt)")
    if VISUAL_FALLBACK:
        print(f"🎨 Visual Fallback aktiv (kein SDXL) — deutlich schneller")
    
    if remaining > 0 and remaining % 12 == 0:
        print(f"📈 Meilenstein: {len(state['done'])}/{len(ALL_SLUGS)} Orte fertig!")
    if VISUAL_FALLBACK:
        print(f"🎨 Visual Fallback aktiv (kein SDXL)")

if __name__ == "__main__":
    main()