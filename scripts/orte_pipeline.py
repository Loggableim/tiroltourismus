#!/usr/bin/env python3
"""
Orte-Pipeline: Enrichment + Bilder + Übersetzung in einem Durchgang.
Läuft als no_agent Cron — 1 Ort pro Tick, dann Commit + Push.
"""
import json, os, sys, time, subprocess, re, urllib.request, urllib.error
from pathlib import Path

BASE = Path("F:/tiroltourismus")
ORTE_DIR = BASE / "src" / "data" / "orte"
STATE_FILE = BASE / "_orte_pipeline.json"
PUBLIC_IMG = BASE / "public" / "images" / "orte"

# Alle 258 Orte slugs
ALL_SLUGS = sorted([
    d for d in os.listdir(ORTE_DIR)
    if os.path.isdir(ORTE_DIR / d)
])

# Zielsprachen für Übersetzung (ausgenommen DE)
LANGUAGES = ['en', 'fr', 'it', 'es', 'zh', 'nl']

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding='utf-8'))
    return {"idx": 0, "done": []}

def save_state(s):
    STATE_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding='utf-8')

def get_orte_data(slug):
    fp = ORTE_DIR / slug / "index.json"
    if not fp.exists():
        return None
    return json.loads(fp.read_text(encoding='utf-8'))

def save_orte_data(slug, data):
    fp = ORTE_DIR / slug / "index.json"
    fp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

def call_llm(prompt, system="Du bist ein Tirol-Reiseexperte. Antworte präzise auf Deutsch."):
    """Ruft OpenCode Go API für Content-Generierung auf."""
    # OpenCode Go API via hermes
    url = "https://opencode.ai/zen/go/v1/chat/completions"
    api_key = os.environ.get("OPENCODE_GO_API_KEY", "")
    if not api_key:
        # Try .env
        env_paths = [
            "E:/HermesPortable/home/.env",
            os.path.expanduser("~/.hermes/.env"),
        ]
        for ep in env_paths:
            if os.path.exists(ep):
                for line in open(ep):
                    if line.startswith("OPENCODE_GO_API_KEY="):
                        api_key = line.strip().split("=", 1)[1]
                        break
                if api_key:
                    break
    
    if not api_key:
        print("⚠️  Kein API-Key — überspringe LLM-Schritt")
        return None
    
    body = json.dumps({
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.7,
    }).encode()
    
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"⚠️  LLM-Fehler: {e}")
        return None

def generate_image(slug, prompt):
    """Generiert SDXL-Bild — via ComfyUI oder diffusers."""
    # Prüfe ob schon vorhanden
    img_dir = PUBLIC_IMG / slug
    img_dir.mkdir(parents=True, exist_ok=True)
    hero_path = img_dir / "hero_1.png"
    
    if hero_path.exists() and hero_path.stat().st_size > 1000:
        print(f"  ✅ Bild existiert bereits: {hero_path}")
        return f"/images/orte/{slug}/hero_1.png"
    
    # Hier kommt der SDXL/diffusers Batch-Call rein
    # Für den MVP: Platzhalter — echtes SDXL später
    print(f"  🖼️  Bild müsste generiert werden: {slug}")
    print(f"     Prompt: {prompt}")
    return None

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
    
    changed = False
    
    # 1a: Lange Beschreibung generieren
    if not data.get('beschreibung'):
        prompt = f"""Schreibe eine reichhaltige, einladende Beschreibung (150-250 Wörter) für {name} in Tirol.
Infos: Höhe {hoehe}m, Bezirk {bezirk}, Region {region}, Tags: {', '.join(tags)}.
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
            cat = 'dorf' if int(hoehe) > 800 else 'marktgemeinde'
        else:
            cat = 'dorf'
        # Simple heuristic — could be smarter
        lower_name = name.lower()
        tag_str = ' '.join(tags).lower()
        
        if 'stadt' in tag_str or name in ['Innsbruck', 'Landeck', 'Kufstein', 'Hall in Tirol', 'Schwaz']:
            cat = 'stadt'
        elif 'bergdorf' in tag_str or int(hoehe) > 1200:
            cat = 'bergdorf'
        elif 'see' in tag_str or 'see' in lower_name:
            cat = 'seeort'
        
        data['kategorie'] = cat
        changed = True
        print(f"  ✅ Kategorie: {cat}")
    
    return changed, data

def step_image(slug, data):
    """Step 2: Hero-Bild generieren"""
    if data.get('hero_bild'):
        return False, data  # Already has image
    
    name = data.get('name', slug)
    kurz = data.get('kurzbeschreibung', '')[:100]
    
    prompt = f"Watercolor painting of {name}, Tirol, Austria. {kurz} Watercolor, soft washes, paper texture, loose brush strokes, transparent colors, artistic painterly, beautiful composition"
    
    hero_path = generate_image(slug, prompt)
    if hero_path:
        data['hero_bild'] = hero_path
        data['bilder'] = [{"url": hero_path, "alt": f"{name} — Aquarell"}]
        return True, data
    
    return False, data

def step_translate(slug, data):
    """Step 3: Beschreibung in alle Sprachen übersetzen"""
    beschreibung = data.get('beschreibung', '')
    if not beschreibung:
        return
    
    for lang in LANGUAGES:
        lang_dir = BASE / "src" / "data" / lang / "orte" / slug
        lang_file = lang_dir / "index.json"
        
        if lang_file.exists():
            continue  # Skip if already translated
        
        # Translate beschreibung
        trans = translate_text(beschreibung, lang)
        if trans:
            lang_dir.mkdir(parents=True, exist_ok=True)
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

def step_commit(slug):
    """Step 4: Git Commit für diesen Ort"""
    result = subprocess.run(
        ["git", "add", "-A", f"src/data/*/orte/{slug}/", f"public/images/orte/{slug}/"],
        capture_output=True, text=True, cwd=str(BASE), timeout=30
    )
    
    result2 = subprocess.run(
        ["git", "commit", "-m", f"[orte] ✨ {slug}: Beschreibung, Bilder & Infos"],
        capture_output=True, text=True, cwd=str(BASE), timeout=30
    )
    
    if "nothing to commit" in result2.stdout + result2.stderr:
        print("  ℹ️  Nichts zu committen")
        return False
    
    push = subprocess.run(
        ["git", "push", "origin", "master"],
        capture_output=True, text=True, cwd=str(BASE), timeout=60
    )
    
    if push.returncode == 0:
        print(f"  🚀 Gepusht!")
        return True
    else:
        print(f"  ⚠️  Push-Fehler: {push.stderr[:200]}")
        return False

# ═══════════════════════════════════════════
# MAIN LOOP — 1 Ort pro Aufruf
# ═══════════════════════════════════════════

def main():
    state = load_state()
    idx = state["idx"]
    
    if idx >= len(ALL_SLUGS):
        print(f"🎉 ALLE {len(ALL_SLUGS)} ORTE FERTIG!")
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
    print(f"⏱️  Nächster Ort in 5 Minuten: {ALL_SLUGS[idx+1] if idx+1 < len(ALL_SLUGS) else '—'}")
    
    # Summary
    remaining = len(ALL_SLUGS) - len(state["done"])
    hours = remaining * 5 / 60
    print(f"📊 Noch {remaining} Orte (~{hours:.0f}h bei 5min-Takt)")

if __name__ == "__main__":
    main()
