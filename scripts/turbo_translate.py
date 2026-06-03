#!/usr/bin/env python3
"""
🔥 Tirol Turbo Translate v3 – 3 Provider parallel

Nutzung:  python scripts/turbo_translate.py <category> <lang> [--limit N]

Provider (Round-Robin):
  1. Groq (FREE) — llama-3.3-70b-versatile, schnell
  2. OpenRouter (FREE) — meta-llama/llama-3.3-70b-instruct:free
  3. Ollama Cloud — ministral-3:3b / ministral-3:14b (2 Keys)

Resume-fähig, Batched (alle Felder in 1 Call).
"""

import json, os, sys, time, re, threading, subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.error

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "src" / "data"

# ── Provider 1: OpenRouter (FREE, primär) ───
def _get_or_key():
    r = subprocess.run(
        ['powershell.exe', '-Command', '[System.Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY","User")'],
        capture_output=True, text=True, timeout=10
    )
    return r.stdout.strip()

OR_KEY = _get_or_key()
OR_BASE = "https://openrouter.ai/api/v1"
OR_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-4-31b-it:free",
    "qwen/qwen3-coder:free",
]

# ── Provider 2: Ollama Cloud ───
OLLAMA_KEYS = [
    "32d793e82978472c89ae09092c65921e.x5XpxfWOplC120yClZhx6PUz",
    "72d76965979a4861bf498130535efe12.7KCt83Wvj9tOLmm13KMAEP9o",
]
OLLAMA_BASE = "https://ollama.com/v1"
OLLAMA_MODEL = "ministral-3:3b"

# ── Config ───
NUM_WORKERS = 1  # sequential (rate limits auf Free-Tier sind streng)
TRANSLATE_FIELDS = {
    "gastro": ["kurzbeschreibung", "beschreibung"],
    "unterkuenfte": ["kurzbeschreibung", "beschreibung"],
    "camping": ["kurzbeschreibung", "beschreibung"],
    "orte": ["kurzbeschreibung"],
    "sehenswuerdigkeiten": ["kurzbeschreibung", "beschreibung"],
    "regionen": ["kurzbeschreibung", "beschreibung", "tipps", "empfehlungen", "umgebung"],
    "magazin": ["teaser", "inhalt", "kategorie"],
    "erlebnisse": ["kurzbeschreibung", "beschreibung"],
    "events": ["name", "titel", "kurzbeschreibung", "beschreibung"],
}

LANG_NAME = {
    "en": "English", "fr": "French", "it": "Italian",
    "es": "Spanish", "nl": "Dutch", "pl": "Polish",
}

# ── Stats ───
stats = {"ok": 0, "skip": 0, "fail": 0}
_stats_lock = threading.Lock()

# ── API Router ───
_provider_idx = 0
_provider_lock = threading.Lock()

def next_provider():
    """Round-Robin: Groq → OpenRouter → Ollama → Groq → ..."""
    global _provider_idx
    providers = []
    if OR_KEY and len(OR_KEY) > 20:
        providers.append("openrouter")
    providers.append("ollama")  # fallback
    
    with _provider_lock:
        p = providers[_provider_idx % len(providers)]
        _provider_idx += 1
        return p

def call_api(messages, timeout=120):
    """Ruft einen API-Provider auf, mit Round-Robin + Retry"""
    provider = next_provider()
    total_len = sum(len(m.get("content", "")) for m in messages)
    
    if provider == "openrouter":
        if total_len > 2000:
            model = OR_MODELS[1]  # gemma-4 für lange Texte
        else:
            model = OR_MODELS[0]  # llama-3.3-70b für kurze
        url = f"{OR_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {OR_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://tiroltourismus.com",
            "X-Title": "Tirol Tourismus",
        }
        call_timeout = min(90, timeout)
    else:  # ollama
        model = OLLAMA_MODEL
        url = f"{OLLAMA_BASE}/chat/completions"
        key = OLLAMA_KEYS[hash(str(messages)) % len(OLLAMA_KEYS)]
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        }
        call_timeout = min(90, timeout)
    
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0.1,
    }).encode()
    
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    
    for attempt in range(3):
        try:
            t0 = time.time()
            resp = urllib.request.urlopen(req, timeout=call_timeout)
            result = json.loads(resp.read())
            text = result["choices"][0]["message"]["content"].strip()
            elapsed = time.time() - t0
            time.sleep(1.5)  # delay between calls
            return text, elapsed, f"{provider}/{model}"
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if e.code == 429:
                wait = 5 + (attempt * 10)
                time.sleep(wait)
                continue
            raise Exception(f"{provider} HTTP {e.code}: {body[:100]}")
        except Exception as e:
            if attempt < 2:
                time.sleep(5)
                continue
            raise Exception(f"{provider}: {str(e)[:100]}")
    raise Exception(f"{provider} max retries")

# ── Translation Logic ───
def has_text(data, field):
    val = data.get(field)
    return isinstance(val, str) and len(val.strip()) >= 3

def needs_translation(target, field, source_text=None):
    if field not in target:
        return True
    val = target.get(field)
    if val is None:
        return True
    if isinstance(val, str) and len(val.strip()) == 0:
        return True
    if source_text and isinstance(val, str) and isinstance(source_text, str):
        if val.strip() == source_text.strip():
            return True
        if isinstance(val, str) and len(val) > 20:
            german = ['der ', 'die ', 'das ', 'ist ', 'und ', 'sind ', 'für ', 'mit ']
            score = sum(1 for w in german if w in val.lower()[:200])
            if score >= 4:
                return True
    return False

PROMPT_TEMPLATE = """You are a professional tourism translator. Translate German tourism content to {lang}.

STRICT RULES:
- Keep HTML tags exactly as-is
- Keep ALL place names (Tirol, Innsbruck, Ötztal, Zillertal, etc.) in original German
- Keep ALL proper names, business names, and culinary terms in German
- Translate naturally, as if written by a native {lang} speaker
- OUTPUT ONLY THE TRANSLATED TEXT. No explanations, no notes.

Translate these fields (output each field preceded by === fieldname ===):
{fields}"""

def process_entry(slug, de_data, lang):
    cat = getattr(process_entry, 'cat', 'gastro')
    fields = TRANSLATE_FIELDS.get(cat, ["kurzbeschreibung"])
    
    target_dir = DATA_DIR / lang / cat / slug
    target_file = target_dir / "index.json"
    
    if target_file.exists():
        try:
            target = json.loads(target_file.read_text(encoding="utf-8"))
        except:
            target = {}
    else:
        target = dict(de_data)
        for f in fields:
            target[f] = None
    
    to_translate = []
    for field in fields:
        source = de_data.get(field, "")
        if has_text(de_data, field) and needs_translation(target, field, source):
            to_translate.append(field)
    
    if not to_translate:
        return (slug, "skip", "done")
    
    field_desc = {
        "kurzbeschreibung": "short description (1-2 sentences)",
        "beschreibung": "full description (3-5 sentences, can include HTML <p> tags)",
        "name": "name/title",
        "titel": "title/heading",
        "teaser": "teaser text (1-2 sentences)",
        "inhalt": "full article content (can include HTML)",
        "kategorie": "category",
    }
    
    fields_text = "\n".join(f"- {f}: {field_desc.get(f, f)}" for f in to_translate)
    source_texts = "\n\n".join(f"=== {f} ===\n{de_data.get(f, '')}" for f in to_translate)
    
    system_prompt = PROMPT_TEMPLATE.format(
        lang=LANG_NAME.get(lang, "English"),
        fields=fields_text
    )
    user_prompt = f"Translate these German fields to {LANG_NAME.get(lang, lang)}:\n\n{source_texts}"
    
    result_text, elapsed, model = call_api([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt[:8000]}
    ])
    
    # Parse section markers
    for f in to_translate:
        pattern = rf'^===\s*{re.escape(f)}\s*===\s*$'
        parts = re.split(pattern, result_text, flags=re.MULTILINE)
        if len(parts) > 1:
            idx = list(fields).index(f) + 1
            if idx < len(parts):
                target[f] = parts[idx].strip()
    
    # Fallback: if single field, use whole text
    if len(to_translate) == 1 and (target.get(to_translate[0]) is None or not target[to_translate[0]]):
        target[to_translate[0]] = result_text
    
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file.write_text(
        json.dumps(target, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    return (slug, "ok", f"{len(to_translate)}f/{model.split('/')[-1][:15]}")

def get_pending(cat, lang):
    de_dir = DATA_DIR / cat
    if not de_dir.exists():
        return []
    
    items = []
    for item in sorted(de_dir.iterdir()):
        if not item.is_dir():
            continue
        de_file = item / "index.json"
        if not de_file.exists():
            continue
        try:
            de_data = json.loads(de_file.read_text(encoding="utf-8"))
            if de_data.get("status") == "archived":
                continue
        except:
            continue
        
        target_dir = DATA_DIR / lang / cat / item.name
        target_file = target_dir / "index.json"
        if target_file.exists():
            try:
                target = json.loads(target_file.read_text(encoding="utf-8"))
            except:
                target = {}
            fields = TRANSLATE_FIELDS.get(cat, ["kurzbeschreibung"])
            needs_work = any(
                has_text(de_data, f) and needs_translation(target, f, de_data.get(f, ""))
                for f in fields
            )
            if not needs_work:
                continue
        
        items.append((item.name, de_data))
    return items

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("category")
    ap.add_argument("lang", default="en")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    
    cat = args.category
    lang = args.lang
    NUM_WORKERS = args.workers
    process_entry.cat = cat
    
    providers = []
    if OR_KEY and len(OR_KEY) > 20: providers.append("OpenRouter")
    providers.append("Ollama")
    
    print(f"{'='*60}")
    print(f"🔥 TURBO TRANSLATE v3: DE → {lang.upper()} | {cat}")
    print(f"🤖 {', '.join(providers)} | {NUM_WORKERS} Workers")
    print(f"{'='*60}")
    
    pending = get_pending(cat, lang)
    total = len(pending)
    
    if args.start:
        pending = pending[args.start:]
    if args.limit:
        pending = pending[:args.limit]
    
    print(f"📋 {total} offen, {len(pending)} in diesem Durchlauf")
    
    if args.dry_run:
        for slug, _ in pending[:5]:
            print(f"  ⏳ {slug}")
        if len(pending) > 5:
            print(f"  ... +{len(pending)-5}")
        sys.exit(0)
    
    if not pending:
        print("✅ Nichts zu tun!")
        sys.exit(0)
    
    t_start = time.time()
    done_count = 0
    
    for slug, de_data in pending:
        try:
            result = process_entry(slug, de_data, lang)
            done_count += 1
            elapsed = time.time() - t_start
            rate = done_count / (elapsed / 60) if elapsed > 0 else 0
            eta = (len(pending) - done_count) / rate if rate > 0 else 0
            
            if result[1] == "ok":
                stats["ok"] += 1
                icon = "✅"
            elif result[1] == "skip":
                stats["skip"] += 1
                icon = "⏭️"
            else:
                stats["fail"] += 1
                icon = "❌"
            
            print(f"  [{done_count:>4}/{len(pending)}] {icon} {result[0]} ({result[2]}) [{rate:.0f}/min ETA {eta:.0f}min]")
        except Exception as e:
            print(f"  [{done_count:>4}/{len(pending)}] ❌ {slug}: {e}")
            stats["fail"] += 1
    
    elapsed = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"🏁 {stats['ok']} übersetzt, {stats['skip']} skipped, {stats['fail']} failed")
    print(f"⏱️ {elapsed/60:.1f}min ({stats['ok']/(elapsed/60):.0f}/min)")
    print(f"{'='*60}")
