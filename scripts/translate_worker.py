#!/usr/bin/env python3
"""
Translation Worker v2 – Übersetzt deutsche JSON-Content-Dateien in Zielsprache.
Nutzung: python translate_worker.py <category> <target_lang> [--limit N] [--dry-run]

Keys: 4 Ollama API Keys (round-robin)
Model: ministral-3:14b
Parallel: max 3 Worker-Threads

Output: src/data/<target_lang>/<category>/<slug>/index.json
"""

import os, sys, json, time, threading, re
from pathlib import Path
import urllib.request, urllib.error

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "src" / "data"

OLLAMA_KEYS = [
    "51484f56e01142ddaa6b247a0f19aab5.SJw0DVBs3S-BWllxSULXM17o",
    "32d793e82978472c89ae09092c65921e.x5XpxfWOplC120yClZhx6PUz",
    "72d76965979a4861bf498130535efe12.7KCt83Wvj9tOLmm13KMAEP9o",
    "b79597dbc5af4811b051cd1dcb2e8d79.rC-MYL24L5P3NShzzn0fYszQ",
]

BASE_URL = "https://ollama.com/v1"
MODEL = "ministral-3:14b"
MAX_PARALLEL = 3

# System-Prompts pro Sprache
LANG_PROMPTS = {
    "fr": "Translate the German tourism text below into natural French. STRICT RULES: Keep HTML tags unchanged. Keep all place names (Tirol, Innsbruck, etc.) and culinary terms (Kaiserschmarrn, etc.) in their German original form. NO explanations, NO notes, NO comments. Output ONLY the translated text.\n\nText:",
    "en": "Translate the German tourism text below into natural English. STRICT RULES: Keep HTML tags unchanged. Keep all place names (Tirol, Innsbruck, etc.) and culinary terms (Kaiserschmarrn, etc.) in their German original form. NO explanations, NO notes, NO comments. Output ONLY the translated text.\n\nText:",
    "it": "Translate the German tourism text below into natural Italian. STRICT RULES: Keep HTML tags unchanged. Keep all place names (Tirol, Innsbruck, etc.) and culinary terms (Kaiserschmarrn, etc.) in their German original form. NO explanations, NO notes, NO comments. Output ONLY the translated text.\n\nText:",
    "es": "Translate the German tourism text below into natural Spanish. STRICT RULES: Keep HTML tags unchanged. Keep all place names (Tirol, Innsbruck, etc.) and culinary terms (Kaiserschmarrn, etc.) in their German original form. NO explanations, NO notes, NO comments. Output ONLY the translated text.\n\nText:",
    "zh": "Translate the German tourism text below into natural Simplified Chinese. STRICT RULES: Keep HTML tags unchanged. Keep all place names (Tirol, Innsbruck, etc.) and culinary terms (Kaiserschmarrn, etc.) in their German original form. NO explanations, NO notes, NO comments. Output ONLY the translated text.\n\nText:",
}

TAG_PROMPTS = {
    "fr": "Translate these German tourism tags into French. Return ONLY a JSON array like [\"tag1\",\"tag2\"]. NO explanations.\nTags:",
    "en": "Translate these German tourism tags into English. Return ONLY a JSON array like [\"tag1\",\"tag2\"]. NO explanations.\nTags:",
    "it": "Translate these German tourism tags into Italian. Return ONLY a JSON array like [\"tag1\",\"tag2\"]. NO explanations.\nTags:",
    "es": "Translate these German tourism tags into Spanish. Return ONLY a JSON array like [\"tag1\",\"tag2\"]. NO explanations.\nTags:",
    "zh": "Translate these German tourism tags into Chinese. Return ONLY a JSON array like [\"tag1\",\"tag2\"]. NO explanations.\nTags:",
}

TRANSLATABLE_FIELDS = {
    "gastro": ["kurzbeschreibung"],
    "unterkuenfte": ["kurzbeschreibung"],
    "camping": ["kurzbeschreibung"],
    "orte": ["kurzbeschreibung"],
    "sehenswuerdigkeiten": ["kurzbeschreibung"],
    "regionen": ["kurzbeschreibung", "beschreibung", "tipps", "empfehlungen", "umgebung"],
    "magazin": ["teaser", "inhalt", "kategorie"],
    "erlebnisse": ["kurzbeschreibung"],
    "events": ["name", "kurzbeschreibung"],
}

_key_index = 0
_key_lock = threading.Lock()

def next_key():
    global _key_index
    with _key_lock:
        k = OLLAMA_KEYS[_key_index % len(OLLAMA_KEYS)]
        _key_index += 1
        return k

def api_call(system_prompt, user_text, timeout=120):
    key = next_key()
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text[:12000]}
        ],
        "max_tokens": 4096,
        "temperature": 0.15,
    }).encode()
    
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions", data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST"
    )
    
    for attempt in range(3):
        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            return json.loads(resp.read())["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if e.code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            raise Exception(f"HTTP {e.code}: {body[:200]}")
        except Exception as e:
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            raise Exception(str(e)[:200])

def translate_text(text, target_lang):
    if not text or not isinstance(text, str) or len(text.strip()) < 3:
        return text
    return api_call(LANG_PROMPTS[target_lang], text)

def translate_tags(tags, target_lang):
    if not tags:
        return tags
    try:
        result = api_call(TAG_PROMPTS[target_lang], json.dumps(tags))
        m = re.search(r'\[.*?\]', result, re.DOTALL)
        if m:
            parsed = json.loads(m.group())
            if isinstance(parsed, list) and len(parsed) == len(tags):
                return parsed
        # Fallback: try whole response as JSON
        parsed = json.loads(result.strip())
        if isinstance(parsed, list):
            return parsed
    except:
        pass
    return tags

def get_german(cat):
    d = DATA_DIR / cat
    if not d.exists(): return []
    out = []
    for item in sorted(d.iterdir()):
        if not item.is_dir(): continue
        jp = item / "index.json"
        if not jp.exists(): continue
        try:
            data = json.loads(open(jp, encoding="utf-8").read())
            if data.get("status") != "archived":
                out.append((item.name, data))
        except: pass
    return out

def get_remaining(cat, lang):
    if lang == "de": return []
    td = DATA_DIR / lang / cat
    out = []
    for slug, data in get_german(cat):
        if not (td / slug / "index.json").exists():
            out.append((slug, data))
    return out

def write_out(cat, slug, data, lang):
    d = DATA_DIR / lang / cat / slug
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "index.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("category")
    ap.add_argument("target_lang")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    
    if args.target_lang not in LANG_PROMPTS:
        print(f"❌ Unsupported: {args.target_lang}"); sys.exit(1)
    
    remaining = get_remaining(args.category, args.target_lang)
    total = len(remaining)
    if args.limit > 0: remaining = remaining[:args.limit]
    
    print(f"\n{'='*60}")
    print(f"🌍 DE → {args.target_lang.upper()} | {args.category}")
    print(f"🤖 {MODEL} | 🔑 {len(OLLAMA_KEYS)} Keys | ⚡ {MAX_PARALLEL} Workers")
    print(f"{'='*60}")
    print(f"📊 {total} remaining ({args.limit or 'unlimited'})")
    if not remaining: print("✨ Nothing to do."); return
    if args.dry_run:
        for s,_ in remaining[:5]: print(f"  • {s}/")
        return
    
    # ── Pre-translate tags ──
    # (tags are handled inline per entry via translate_entry)
    
    # ── Threaded processing ──
    class Q:
        def __init__(self, items):
            self.items = list(reversed(items))
            self.lock = threading.Lock()
        def pop(self):
            with self.lock:
                return self.items.pop() if self.items else None
    
    q = Q(remaining)
    results = []
    rlock = threading.Lock()
    
    def worker(tid):
        while True:
            item = q.pop()
            if not item: break
            slug, data = item
            try:
                print(f"  [{tid}] ⏳ {slug}...")
                # Translate translatable fields
                translatable = TRANSLATABLE_FIELDS.get(args.category, [])
                tdata = {}
                for k, v in data.items():
                    if k in translatable and isinstance(v, str):
                        tdata[k] = translate_text(v, args.target_lang)
                    elif k == "tags" and isinstance(v, list):
                        tdata[k] = translate_tags(v, args.target_lang)
                    else:
                        tdata[k] = v
                write_out(args.category, slug, tdata, args.target_lang)
                with rlock:
                    results.append(("ok", slug))
                print(f"  [{tid}] ✅ {slug}")
            except Exception as e:
                with rlock:
                    results.append(("err", slug, str(e)))
                print(f"  [{tid}] ❌ {slug}: {e}")
    
    nw = min(MAX_PARALLEL, len(remaining))
    threads = [threading.Thread(target=worker, args=(i+1,)) for i in range(nw)]
    for t in threads: t.start()
    for t in threads: t.join()
    
    ok = sum(1 for r in results if r[0]=="ok")
    err = sum(1 for r in results if r[0]=="err")
    print(f"\n{'='*60}")
    print(f"🏁 {args.category} → {args.target_lang}: {ok} OK, {err} failed")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
