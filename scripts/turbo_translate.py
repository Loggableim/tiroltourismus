#!/usr/bin/env python3
"""
🔥 Tirol Turbo Translate v2 – Hochgeschwindigkeits-Übersetzungs-Pipeline
Nutzung:  python scripts/turbo_translate.py <category> <lang> [--limit N] [--start N]

Batched: alle Felder eines Eintrags in EINEM API-Call → 2x schneller.
4 Keys Round-Robin, 3s Delay → rate-limit-sicher.
Resume-fähig (überspringt bereits übersetzte Felder).
"""

import json, os, sys, time, re, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.error

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "src" / "data"

# 4 Ollama Cloud Keys (Round-Robin)
OLLAMA_KEYS = [
    "51484f56e01142ddaa6b247a0f19aab5.SJw0DVBs3S-BWllxSULXM17o",
    "32d793e82978472c89ae09092c65921e.x5XpxfWOplC120yClZhx6PUz",
    "72d76965979a4861bf498130535efe12.7KCt83Wvj9tOLmm13KMAEP9o",
    "b79597dbc5af4811b051cd1dcb2e8d79.rC-MYL24L5P3NShzzn0fYszQ",
]

OLLAMA_BASE = "https://ollama.com/v1"
SHORT_MODEL = "ministral-3:3b"
LONG_MODEL = "ministral-3:14b"
LONG_THRESHOLD = 1200
NUM_WORKERS = 1  # nur sequentiell (rate limits)
CALL_DELAY = 3   # sekunden zwischen API-Calls

# -- Welche Felder pro Collection übersetzt werden --
TRANSLATE_FIELDS = {
    "gastro": ["kurzbeschreibung", "beschreibung"],
    "unterkuenfte": ["kurzbeschreibung", "beschreibung"],
    "camping": ["kurzbeschreibung", "beschreibung"],
    "orte": ["kurzbeschreibung"],
    "sehenswuerdigkeiten": ["kurzbeschreibung", "beschreibung"],
    "regionen": ["kurzbeschreibung", "beschreibung", "tipps", "empfehlungen", "umgebung"],
    "magazin": ["teaser", "inhalt", "kategorie"],
    "erlebnisse": ["kurzbeschreibung", "beschreibung"],
    "events": ["name", "kurzbeschreibung"],
}

LANG_NAME = {
    "en": "English", "fr": "French", "it": "Italian",
    "es": "Spanish", "nl": "Dutch", "pl": "Polish",
}

_key_index = 0
_key_lock = threading.Lock()
stats = {"ok": 0, "skip": 0, "fail": 0}

def next_key():
    global _key_index
    with _key_lock:
        k = OLLAMA_KEYS[_key_index % len(OLLAMA_KEYS)]
        _key_index += 1
        return k

def call_api(messages, timeout=120):
    """Ein API-Call mit Key-Rotation + 429-Retry"""
    key = next_key()
    
    # Textlänge checken
    total_len = sum(len(m.get("content", "")) for m in messages)
    model = LONG_MODEL if total_len > LONG_THRESHOLD else SHORT_MODEL
    
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0.1,
    }).encode()
    
    req = urllib.request.Request(
        f"{OLLAMA_BASE}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        },
        method="POST"
    )
    
    for attempt in range(3):
        try:
            t0 = time.time()
            resp = urllib.request.urlopen(req, timeout=timeout)
            result = json.loads(resp.read())
            text = result["choices"][0]["message"]["content"].strip()
            elapsed = time.time() - t0
            time.sleep(CALL_DELAY)
            return text, elapsed, model
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if e.code == 429:
                wait = 15 + (attempt * 20)
                time.sleep(wait)
                continue
            raise Exception(f"HTTP {e.code}: {body[:150]}")
        except Exception as e:
            if attempt < 2:
                time.sleep(10)
                continue
            raise Exception(str(e)[:150])
    raise Exception("Max retries exhausted")

def has_text(data, field):
    val = data.get(field)
    return isinstance(val, str) and len(val.strip()) >= 3

def needs_translation(target, field):
    if field not in target:
        return True
    val = target.get(field)
    return val is None or (isinstance(val, str) and len(val.strip()) == 0)

def process_entry(slug, de_data, lang):
    """Übersetzt ALLE fehlenden Felder eines Eintrags in EINEM API-Call"""
    try:
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
        
        # Prüfen, welche Felder noch übersetzt werden müssen
        to_translate = []
        for field in fields:
            if has_text(de_data, field) and needs_translation(target, field):
                to_translate.append(field)
        
        if not to_translate:
            return (slug, "skip", "fertig")
        
        # Batch-Translate: ALLE fehlenden Felder in EINEM Call
        # Prompt: sende strukturierte JSON-Outputs
        field_descriptions = {
            "kurzbeschreibung": "short description (1-2 sentences)",
            "beschreibung": "full description (3-5 sentences, HTML <p> tags)",
            "name": "name/title",
            "teaser": "teaser text (1 sentence)",
            "inhalt": "full article content (HTML)",
            "kategorie": "category",
            "tipps": "tips section",
            "empfehlungen": "recommendations",
            "umgebung": "surrounding area",
        }
        
        fields_text = "\n".join(
            f"- {f}: {field_descriptions.get(f, f)}"
            for f in to_translate
        )
        
        source_texts = "\n\n".join(
            f"=== {f} ===\n{de_data.get(f, '')}"
            for f in to_translate
        )
        
        system_prompt = (
            f"You are a professional tourism translator, translating German content "
            f"to {LANG_NAME.get(lang, 'English')} for a Tyrol tourism website.\n\n"
            f"RULES:\n"
            f"- Keep ALL HTML tags unchanged\n"
            f"- Keep ALL place names (Tirol, Innsbruck, Ötztal, Zillertal, Kitzbühel, etc.) in German\n"
            f"- Keep culinary terms (Kaiserschmarrn, Knödel, etc.) in German\n"
            f"- Keep ALL proper names unchanged\n"
            f"- Translate naturally, as if written by a native {LANG_NAME.get(lang, lang)} speaker\n"
            f"- NO explanations, NO notes, NO comments in your response\n\n"
            f"Translate these fields:\n{fields_text}"
        )
        
        user_prompt = f"Translate these German fields to {LANG_NAME.get(lang, lang)}:\n\n{source_texts}"
        
        result_text, elapsed, model = call_api([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt[:8000]}
        ])
        
        # Parse result: split by "=== field ===" markers
        current_field = None
        for line in result_text.split("\n"):
            m = re.match(r'^===\s*(.+?)\s*===', line)
            if m:
                current_field = m.group(1).strip()
                continue
            if current_field and current_field in to_translate:
                if target.get(current_field) is None or not target[current_field]:
                    if target.get(current_field) is None:
                        target[current_field] = ""
                    target[current_field] = (target.get(current_field, "") + "\n" + line).strip()
        
        # Fallback: if parsing didn't work, try assigning sequentially
        if all(target.get(f) is None or not target.get(f) for f in to_translate):
            # Simple approach: split by double newline and assign in order
            parts = re.split(r'\n===|\n---', result_text)
            text_only = result_text
            # Remove section markers
            for f in to_translate:
                text_only = re.sub(rf'^===\s*{re.escape(f)}\s*===\s*$', '', text_only, flags=re.MULTILINE)
            text_only = text_only.strip()
            
            if text_only and len(to_translate) == 1:
                target[to_translate[0]] = text_only
            elif text_only:
                # Split by double newline as fallback
                paragraphs = [p.strip() for p in re.split(r'\n\n+', text_only) if p.strip()]
                for i, f in enumerate(to_translate):
                    if i < len(paragraphs):
                        target[f] = paragraphs[i]
        
        # Write
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file.write_text(
            json.dumps(target, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        return (slug, "ok", f"{len(to_translate)} fields, {model}")
    
    except Exception as e:
        return (slug, "fail", str(e)[:100])

def get_pending(cat, lang):
    """Listet alle noch zu übersetzenden Einträge auf"""
    de_dir = DATA_DIR / cat
    if not de_dir.exists():
        print(f"❌ Collection '{cat}' nicht gefunden")
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
                has_text(de_data, f) and needs_translation(target, f)
                for f in fields
            )
            if not needs_work:
                continue
        
        items.append((item.name, de_data))
    
    return items

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("category", help="z.B. gastro, camping, unterkuenfte")
    ap.add_argument("lang", default="en", help="Zielsprache")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    
    cat = args.category
    lang = args.lang
    
    # Set cat for process_entry
    process_entry.cat = cat
    
    print(f"{'='*60}")
    print(f"🔥 TURBO TRANSLATE v2: DE → {lang.upper()} | {cat}")
    print(f"🤖 {len(OLLAMA_KEYS)} Keys | Modelle: {SHORT_MODEL}/{LONG_MODEL}")
    print(f"⚡ Batched: alle Felder pro Eintrag in 1 API-Call")
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
            print(f"  ... und {len(pending)-5} weitere")
        sys.exit(0)
    
    if not pending:
        print("✅ Nichts zu tun!")
        sys.exit(0)
    
    t_start = time.time()
    done_count = 0
    
    for slug, de_data in pending:
        result = process_entry(slug, de_data, lang)
        done_count += 1
        elapsed = time.time() - t_start
        rate = done_count / (elapsed / 60) if elapsed > 0 else 0
        
        if result[1] == "ok":
            stats["ok"] += 1
            icon = "✅"
        elif result[1] == "skip":
            stats["skip"] += 1
            icon = "⏭️"
        else:
            stats["fail"] += 1
            icon = "❌"
        
        eta_min = (total - done_count) / rate if rate > 0 else 0
        print(f"  [{done_count:>4}/{total}] {icon} {result[0]} ({result[2]}) [{rate:.0f}/min, ETA {eta_min:.0f}min]")
    
    elapsed = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"🏁 Fertig! {stats['ok']} übersetzt, {stats['skip']} übersprungen, {stats['fail']} ❌")
    print(f"⏱️ {elapsed/60:.1f} min ({total/(elapsed/60):.0f} Einträge/min)")
    print(f"{'='*60}")
