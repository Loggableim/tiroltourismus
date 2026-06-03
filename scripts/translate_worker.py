#!/usr/bin/env python3
"""
Translation Worker v4 – Übersetzt deutsche JSON-Content-Dateien in Zielsprache.
Nutzung: python translate_worker.py <category> <target_lang> [--limit N] [--dry-run]

Providers (parallel, round-robin):
  - Ollama Cloud: 4 Keys, gpt-oss:20b (short) / gpt-oss:120b (long)
  - OpenRouter: 1 Key, free modèles (short/long)
Parallel: max 6 Worker-Threads (3 pro Provider)

Output: src/data/<target_lang>/<category>/<slug>/index.json
"""

import os, sys, json, time, threading, re
from pathlib import Path
import urllib.request, urllib.error

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "src" / "data"

# ── Ollama Cloud (alle 6 Keys) ─────────────────────────────────
OLLAMA_KEYS = [
    "51484f56e01142ddaa6b247a0f19aab5.SJw0DVBs3S-BWllxSULXM17o",
    "32d793e82978472c89ae09092c65921e.x5XpxfWOplC120yClZhx6PUz",
    "72d76965979a4861bf498130535efe12.7KCt83Wvj9tOLmm13KMAEP9o",
    "b79597dbc5af4811b051cd1dcb2e8d79.rC-MYL24L5P3NShzzn0fYszQ",
    "27c36e3e9cbe4acb8c0fa0dcde9f2017.SJjR",   # loggableim (manual)
    "0d8ea1db6cf64aa493a63686ca6cdcf3.v8Co",    # logga23 (manual)
]
OLLAMA_BASE_URL = "https://ollama.com/v1"
OLLAMA_SHORT_MODEL = os.getenv("OLLAMA_MODEL_SHORT", "ministral-3:3b")
OLLAMA_LONG_MODEL  = os.getenv("OLLAMA_MODEL_LONG",  "ministral-3:14b")

# ── OpenRouter (Free) ─────────────────────────────────────────
OPENROUTER_KEY      = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_SHORT    = os.getenv("OR_SHORT", "google/gemma-3-27b-it:free")
OPENROUTER_LONG     = os.getenv("OR_LONG",  "openai/gpt-oss-120b:free")

LONG_TEXT_THRESHOLD = int(os.getenv("OLLAMA_LONG_TEXT_THRESHOLD", "1200"))
MAX_PARALLEL_OLLAMA = 6
MAX_PARALLEL_OR    = 0  # kein OpenRouter-Key verfügbar (für später vorbereitet)

# ── Provider Key-Rotation ─────────────────────────────────────
_ollama_idx = 0
_or_idx     = 0
_key_lock   = threading.Lock()

def next_ollama_key():
    global _ollama_idx
    with _key_lock:
        k = OLLAMA_KEYS[_ollama_idx % len(OLLAMA_KEYS)]
        _ollama_idx += 1
        return k

OPENROUTER_KEYS = [k for k in [OPENROUTER_KEY] if k]

def next_or_key():
    global _or_idx
    if not OPENROUTER_KEYS:
        return None
    with _key_lock:
        k = OPENROUTER_KEYS[_or_idx % len(OPENROUTER_KEYS)]
        _or_idx += 1
        return k

def pick_model(user_text, force_long=False):
    if force_long or len(user_text or "") >= LONG_TEXT_THRESHOLD:
        return OLLAMA_LONG_MODEL
    return OLLAMA_SHORT_MODEL

def pick_or_model(user_text, force_long=False):
    if force_long or len(user_text or "") >= LONG_TEXT_THRESHOLD:
        return OPENROUTER_LONG
    return OPENROUTER_SHORT

# ── API Calls ─────────────────────────────────────────────────
def api_call(system_prompt, user_text, timeout=120, model=None, provider="ollama"):
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_text[:12000]}
        ],
        "max_tokens": 4096,
        "temperature": 0.15,
    }).encode()

    if provider == "ollama":
        key = next_ollama_key()
        url = f"{OLLAMA_BASE_URL}/chat/completions"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    elif provider == "openrouter":
        key = next_or_key()
        if not key:
            raise Exception("No OpenRouter key")
        url = f"{OPENROUTER_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "HTTP-Referer": "https://tiroltourismus.com",
            "X-Title": "Tirol Tourismus i18n",
        }
    else:
        raise ValueError(f"Unknown provider: {provider}")

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    for attempt in range(3):
        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            return json.loads(resp.read())["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if e.code == 429:
                wait = 5 * (attempt + 1) + (threading.get_ident() % 3) * 2
                time.sleep(wait)
                continue
            raise Exception(f"HTTP {e.code}: {body[:200]}")
        except Exception as e:
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            raise Exception(str(e)[:200])

def smart_call(system_prompt, user_text, force_long=False, provider="ollama"):
    """Wählt Modell je nach Textlänge und Provider."""
    if provider == "ollama":
        model = pick_model(user_text, force_long)
    else:
        model = pick_or_model(user_text, force_long)
    return api_call(system_prompt, user_text, model=model, provider=provider)

# ── System-Prompts ────────────────────────────────────────────
LANG_PROMPTS = {
    "fr": "Translate the German tourism text below into natural French. STRICT RULES: Keep HTML tags unchanged. Keep all place names (Tirol, Innsbruck, etc.) and culinary terms (Kaiserschmarrn, etc.) in their German original form. NO explanations, NO notes, NO comments. Output ONLY the translated text.\n\nText:",
    "en": "Translate the German tourism text below into natural English. STRICT RULES: Keep HTML tags unchanged. Keep all place names (Tirol, Innsbruck, etc.) and culinary terms (Kaiserschmarrn, etc.) in their German original form. NO explanations, NO notes, NO comments. Output ONLY the translated text.\n\nText:",
    "it": "Translate the German tourism text below into natural Italian. STRICT RULES: Keep HTML tags unchanged. Keep all place names (Tirol, Innsbruck, etc.) and culinary terms (Kaiserschmarrn, etc.) in their German original form. NO explanations, NO notes, NO comments. Output ONLY the translated text.\n\nText:",
    "es": "Translate the German tourism text below into natural Spanish. STRICT RULES: Keep HTML tags unchanged. Keep all place names (Tirol, Innsbruck, etc.) and culinary terms (Kaiserschmarrn, etc.) in their German original form. NO explanations, NO notes, NO comments. Output ONLY the translated text.\n\nText:",
    "zh": "Translate the German tourism text below into natural Simplified Chinese. STRICT RULES: Keep HTML tags unchanged. Keep all place names (Tirol, Innsbruck, etc.) and culinary terms (Kaiserschmarrn, etc.) in their German original form. NO explanations, NO notes, NO comments. Output ONLY the translated text.\n\nText:",
    "nl": "Translate the German tourism text below into natural Dutch. STRICT RULES: Keep HTML tags unchanged. Keep all place names (Tirol, Innsbruck, etc.) and culinary terms (Kaiserschmarrn, etc.) in their German original form. NO explanations, NO notes, NO comments. Output ONLY the translated text.\n\nText:",
    "cs": "Translate the German tourism text below into natural Czech. STRICT RULES: Keep HTML tags unchanged. Keep all place names (Tirol, Innsbruck, etc.) and culinary terms (Kaiserschmarrn, etc.) in their German original form. NO explanations, NO notes, NO comments. Output ONLY the translated text.\n\nText:",
    "pl": "Translate the German tourism text below into natural Polish. STRICT RULES: Keep HTML tags unchanged. Keep all place names (Tirol, Innsbruck, etc.) and culinary terms (Kaiserschmarrn, etc.) in their German original form. NO explanations, NO notes, NO comments. Output ONLY the translated text.\n\nText:",
    "hu": "Translate the German tourism text below into natural Hungarian. STRICT RULES: Keep HTML tags unchanged. Keep all place names (Tirol, Innsbruck, etc.) and culinary terms (Kaiserschmarrn, etc.) in their German original form. NO explanations, NO notes, NO comments. Output ONLY the translated text.\n\nText:",
    "sk": "Translate the German tourism text below into natural Slovak. STRICT RULES: Keep HTML tags unchanged. Keep all place names (Tirol, Innsbruck, etc.) and culinary terms (Kaiserschmarrn, etc.) in their German original form. NO explanations, NO notes, NO comments. Output ONLY the translated text.\n\nText:",
    "ru": "Translate the German tourism text below into natural Russian. STRICT RULES: Keep HTML tags unchanged. Keep all place names (Tirol, Innsbruck, etc.) and culinary terms (Kaiserschmarrn, etc.) in their German original form. NO explanations, NO notes, NO comments. Output ONLY the translated text.\n\nText:",
}

TAG_PROMPTS = {
    "fr": "Translate these German tourism tags into French. Return ONLY a JSON array like [\"tag1\",\"tag2\"]. NO explanations.\nTags:",
    "en": "Translate these German tourism tags into English. Return ONLY a JSON array like [\"tag1\",\"tag2\"]. NO explanations.\nTags:",
    "it": "Translate these German tourism tags into Italian. Return ONLY a JSON array like [\"tag1\",\"tag2\"]. NO explanations.\nTags:",
    "es": "Translate these German tourism tags into Spanish. Return ONLY a JSON array like [\"tag1\",\"tag2\"]. NO explanations.\nTags:",
    "zh": "Translate these German tourism tags into Chinese. Return ONLY a JSON array like [\"tag1\",\"tag2\"]. NO explanations.\nTags:",
    "nl": "Translate these German tourism tags into Dutch. Return ONLY a JSON array like [\"tag1\",\"tag2\"]. NO explanations.\nTags:",
    "cs": "Translate these German tourism tags into Czech. Return ONLY a JSON array like [\"tag1\",\"tag2\"]. NO explanations.\nTags:",
    "pl": "Translate these German tourism tags into Polish. Return ONLY a JSON array like [\"tag1\",\"tag2\"]. NO explanations.\nTags:",
    "hu": "Translate these German tourism tags into Hungarian. Return ONLY a JSON array like [\"tag1\",\"tag2\"]. NO explanations.\nTags:",
    "sk": "Translate these German tourism tags into Slovak. Return ONLY a JSON array like [\"tag1\",\"tag2\"]. NO explanations.\nTags:",
    "ru": "Translate these German tourism tags into Russian. Return ONLY a JSON array like [\"tag1\",\"tag2\"]. NO explanations.\nTags:",
}

TRANSLATABLE_FIELDS = {
    "gastro":             ["kurzbeschreibung", "beschreibung"],
    "unterkuenfte":       ["kurzbeschreibung"],
    "camping":            ["kurzbeschreibung"],
    "orte":               ["kurzbeschreibung"],
    "sehenswuerdigkeiten":["kurzbeschreibung"],
    "regionen":           ["kurzbeschreibung", "beschreibung", "tipps", "empfehlungen", "umgebung"],
    "magazin":            ["teaser", "inhalt", "kategorie"],
    "erlebnisse":         ["kurzbeschreibung"],
    "events":             ["name", "kurzbeschreibung"],
}

# ── Translation Functions ─────────────────────────────────────
def translate_text(text, target_lang, provider="ollama"):
    if not text or not isinstance(text, str) or len(text.strip()) < 3:
        return text
    prompt = LANG_PROMPTS.get(target_lang, LANG_PROMPTS["en"])
    return smart_call(prompt, text, provider=provider)

def translate_tags(tags, target_lang, provider="ollama"):
    if not tags:
        return tags
    try:
        prompt = TAG_PROMPTS.get(target_lang, TAG_PROMPTS["en"])
        result = api_call(prompt, json.dumps(tags), model=pick_model(""), provider=provider)
        m = re.search(r'\[.*?\]', result, re.DOTALL)
        if m:
            parsed = json.loads(m.group())
            if isinstance(parsed, list) and len(parsed) == len(tags):
                return parsed
        parsed = json.loads(result.strip())
        if isinstance(parsed, list):
            return parsed
    except:
        pass
    return tags

# ── Data Helpers ──────────────────────────────────────────────
def get_german(cat):
    d = DATA_DIR / cat
    if not d.exists():
        return []
    out = []
    for item in sorted(d.iterdir()):
        if not item.is_dir():
            continue
        jp = item / "index.json"
        if not jp.exists():
            continue
        try:
            data = json.loads(open(jp, encoding="utf-8").read())
            if data.get("status") != "archived":
                out.append((item.name, data))
        except:
            pass
    return out

def load_target(path):
    """Lädt bestehende Ziel-JSONs, damit fehlende Felder ergänzt statt Metadaten überschrieben werden."""
    try:
        data = json.loads(open(path, encoding="utf-8").read())
        return data if isinstance(data, dict) else None
    except:
        return None

def has_source_text(data, field):
    val = data.get(field, "")
    return isinstance(val, str) and len(val.strip()) >= 3

def is_missing_target_text(data, field):
    if not isinstance(data, dict) or field not in data:
        return True
    val = data.get(field)
    return val is None or (isinstance(val, str) and len(val.strip()) == 0)

def needs_field_translation(cat, source, target):
    """True, wenn ein existierendes Ziel-JSON übersetzbare Quelltexte noch leer/missing hat."""
    fields = TRANSLATABLE_FIELDS.get(cat, ["kurzbeschreibung"])
    return any(has_source_text(source, field) and is_missing_target_text(target, field) for field in fields)

def get_remaining(cat, lang):
    if lang == "de":
        return []
    td = DATA_DIR / lang / cat
    out = []
    for slug, data in get_german(cat):
        target_path = td / slug / "index.json"
        if not target_path.exists():
            out.append((slug, data, None))
            continue
        target_data = load_target(target_path)
        if target_data is None or needs_field_translation(cat, data, target_data):
            out.append((slug, data, target_data))
    return out

def write_out(cat, slug, data, lang):
    d = DATA_DIR / lang / cat / slug
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "index.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_provider(thread_id):
    """Nur Ollama (kein OpenRouter-Key verfügbar)"""
    return "ollama"

# ── Main ──────────────────────────────────────────────────────
def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("category")
    ap.add_argument("target_lang")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    target_lang = args.target_lang
    cat = args.category

    remaining = get_remaining(cat, target_lang)
    if args.limit:
        remaining = remaining[:args.limit]

    total = len(remaining)
    if total == 0:
        print(f"✅ {cat} → {target_lang}: nichts zu übersetzen")
        return

    print(f"{'='*60}")
    print(f"🌍 DE → {target_lang.upper()} | {cat}")
    print(f"🤖 Ollama={OLLAMA_SHORT_MODEL}/{OLLAMA_LONG_MODEL} + OR={OPENROUTER_SHORT}/{OPENROUTER_LONG}")
    print(f"🔑 {len(OLLAMA_KEYS)} Ollama Keys + {len(OPENROUTER_KEYS)} OR Keys | ⚡ {MAX_PARALLEL_OLLAMA+MAX_PARALLEL_OR} Workers")
    print(f"📋 {total} Einträge offen")

    done = 0
    failed = 0

    def worker(tid, items):
        nonlocal done, failed
        provider = get_provider(tid)
        for slug, data, target_data in items:
            try:
                fields = TRANSLATABLE_FIELDS.get(cat, ["kurzbeschreibung"])
                translated = dict(target_data) if isinstance(target_data, dict) else dict(data)
                for field in fields:
                    if has_source_text(data, field) and (target_data is None or is_missing_target_text(translated, field)):
                        translated[field] = translate_text(data.get(field, ""), target_lang, provider=provider)
                tags = data.get("tags")
                if tags and (target_data is None or "tags" not in translated):
                    translated["tags"] = translate_tags(tags, target_lang, provider=provider)
                if not args.dry_run:
                    write_out(cat, slug, translated, target_lang)
                done += 1
                status = "✅"
            except Exception as e:
                failed += 1
                status = f"❌ {e}"
            print(f"  [{provider[:2].upper()}] {status} {slug}")

    # Threads starten
    threads = []
    n_threads = MAX_PARALLEL_OLLAMA + MAX_PARALLEL_OR
    chunk = (total + n_threads - 1) // n_threads
    for i in range(n_threads):
        items = remaining[i*chunk:(i+1)*chunk]
        if not items:
            continue
        t = threading.Thread(target=worker, args=(i, items))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print(f"\n{'='*60}")
    print(f"🏁 {cat} → {target_lang}: {done} OK, {failed} failed")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
