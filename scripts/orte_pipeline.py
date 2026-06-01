#!/usr/bin/env python3
"""
Orte-Pipeline: Enrichment + Bilder + Übersetzung in einem Durchgang.
Läuft als no_agent Cron — 1 Ort pro Tick, dann Commit + Push.
SDXL Watercolor-Bilder via diffusers.
"""
import sys, json, os, time, subprocess, re, urllib.request, urllib.error, hashlib
from pathlib import Path
import torch
from diffusers import StableDiffusionXLPipeline

BASE = Path("F:/tiroltourismus")
ORTE_DIR = BASE / "src" / "data" / "orte"
STATE_FILE = BASE / "_orte_pipeline.json"
PUBLIC_IMG = BASE / "public" / "images" / "orte"

# SDXL Setup
MODEL_PATH = Path(r"C:/HermesPortable/ComfyUI/models/checkpoints/sd_xl_base_1.0.safetensors")
WATERCOLOR = "Watercolor painting, soft washes, paper texture, loose brush strokes, transparent colors, artistic painterly, beautiful composition"
NEG = "photo, comic, 3d, sharp lines, digital art, graphic, neon, overexposed, oversaturated, cartoon, illustration"
PIPE = None  # Lazy-loaded SDXL

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
    req.add_header("User-Agent", "Mozilla/5.0")
    
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
        return resp["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"⚠️  Rate Limited — warte 5s...")
            time.sleep(5)
            try:
                resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
                return resp["choices"][0]["message"]["content"]
            except:
                print(f"⚠️  Auch nach Retry fehlgeschlagen")
                return None
        print(f"⚠️  HTTP {e.code}: {e.read().decode()[:100]}")
        return None
    except Exception as e:
        print(f"⚠️  LLM-Fehler: {e}")
        return None

def ensure_sdxl():
    """Lazy-load SDXL pipeline (einmal pro Prozess)"""
    global PIPE
    if PIPE is not None:
        return True
    
    if not MODEL_PATH.exists():
        print(f"  ⚠️  SDXL Model nicht gefunden: {MODEL_PATH}")
        return False
    
    try:
        # SSL fix for git-bash
        os.environ.setdefault("REQUESTS_CA_BUNDLE", 
            "C:/HermesPortable/venv/Lib/site-packages/certifi/cacert.pem")
        
        print(f"  🎨 Lade SDXL...")
        PIPE = StableDiffusionXLPipeline.from_single_file(
            str(MODEL_PATH), torch_dtype=torch.float16
        )
        PIPE.to("cuda")
        PIPE.vae.enable_slicing()
        vram = torch.cuda.memory_allocated() / 1024**3
        print(f"  ✅ SDXL geladen ({vram:.1f} GB VRAM)")
        return True
    except Exception as e:
        print(f"  ⚠️  SDXL Fehler: {e}")
        return False

def generate_image(slug, prompt_text):
    """Generiert SDXL Watercolor-Bild für einen Ort."""
    img_dir = PUBLIC_IMG / slug
    img_dir.mkdir(parents=True, exist_ok=True)
    hero_path = img_dir / "hero_1.png"
    
    if hero_path.exists() and hero_path.stat().st_size > 1000:
        print(f"  ✅ Bild existiert bereits")
        return f"/images/orte/{slug}/hero_1.png"
    
    if not ensure_sdxl():
        return None
    
    prompt = f"{prompt_text}. {WATERCOLOR}"
    seed = abs(hash(slug)) % 100000 + 42
    gen = torch.Generator(device="cuda").manual_seed(seed)
    
    try:
        print(f"  🖌️  Generiere Bild (Seed {seed})...")
        img = PIPE(
            prompt=prompt, negative_prompt=NEG,
            height=1024, width=1024,
            guidance_scale=7.0, num_inference_steps=25, generator=gen,
        ).images[0]
        img.save(hero_path)
        kb = hero_path.stat().st_size / 1024
        print(f"  ✅ Bild gespeichert ({kb:.0f} KB)")
        return f"/images/orte/{slug}/hero_1.png"
    except Exception as e:
        print(f"  ⚠️  Bildgenerierung fehlgeschlagen: {e}")
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
    """Step 2: Hero-Bild generieren (SDXL Watercolor)"""
    if data.get('hero_bild'):
        return False, data  # Already has image
    
    name = data.get('name', slug)
    kurz = data.get('kurzbeschreibung', '')[:120]
    hoehe = data.get('hoehe', '')
    region = data.get('region', '')
    
    prompt_text = f"Beautiful Tyrolean village of {name} in the {region} region, {hoehe}m elevation, {kurz}"
    
    hero_path = generate_image(slug, prompt_text)
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
    remaining = len(ALL_SLUGS) - len(state["done"])
    print(f"⏱️  Nächster Ort in 5 Minuten: {ALL_SLUGS[idx+1] if idx+1 < len(ALL_SLUGS) else '—'}")
    print(f"📊 Noch {remaining} Orte (~{remaining * 5 // 60}h bei 5min-Takt)")
    print(f"🎨 SDXL: ~50s pro Bild (Laden 30s + Generate 18s)")
    
    if remaining > 0 and remaining % 12 == 0:
        print(f"📈 Meilenstein: {len(state['done'])}/{len(ALL_SLUGS)} Orte fertig!")

if __name__ == "__main__":
    main()
