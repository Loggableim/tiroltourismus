#!/usr/bin/env python3
"""
🌍 Tirol Tourismus — Mehrsprachen-Übersetzungs-Engine

Verwendet:
  4 Ollama API Keys (rotierend)
  ≤600 Wörter → ministral-3:3b
  >600 Wörter → ministral-3:14b
  Sprache 'zh' → deepseek-v4-flash via opencode-go

Usage:
  python scripts/translate.py fr orte [--batch 0-9]
  python scripts/translate.py fr magazin --slug die-besten-huetten-in-tirol-zum-einkehren
  python scripts/translate.py fr singletons
  python scripts/translate.py fr status          # Zeigt Fortschritt
"""
import json, os, sys, time, re, html as html_mod
from copy import deepcopy
from collections import OrderedDict

# ── Konfiguration ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'src', 'data')

# 4 Ollama Keys rotierend
OLLAMA_KEYS = [
    ("51484f56e01142ddaa6b247a0f19aab5.SJw0DVBs3S-BWllxSULXM17o", "key0"),
    ("32d793e82978472c89ae09092c65921e.x5XpxfWOplC120yClZhx6PUz", "key1"),
    ("72d76965979a4861bf498130535efe12.7KCt83Wvj9tOLmm13KMAEP9o", "key2"),
    ("b79597dbc5af4811b051cd1dcb2e8d79.rC-MYL24L5P3NShzzn0fYszQ", "key3"),
]

OLLAMA_BASE = "https://ollama.com/v1"
OPENCODE_BASE = "https://opencode.ai/zen/go/v1"
OPENCODE_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")

# Modell-Routing
SMALL_MODEL = "ministral-3:3b"    # ≤600 Wörter
LARGE_MODEL = "ministral-3:14b"   # >600 Wörter
ZH_MODEL = "deepseek-v4-flash"    # Chinesisch via opencode
WORD_LIMIT = 600

# ── Key Rotation ───────────────────────────────────────────────
_key_index = 0
_key_lock = False

def get_next_ollama_key():
    """Round-Robin über 4 Keys"""
    global _key_index
    key, label = OLLAMA_KEYS[_key_index % len(OLLAMA_KEYS)]
    _key_index += 1
    return key, label

# ── Text-Erkennung ─────────────────────────────────────────────
TRANSLATABLE_TEXT_FIELDS = {
    # collection: [feldname, ...] – Felder die Übersetzung brauchen
    'regionen': ['titel', 'kurzbeschreibung', 'beschreibung', 'tags'],
    'unterkuenfte': ['name', 'beschreibung', 'tags'],
    'orte': ['name', 'kurzbeschreibung', 'tags'],
    'gastro': ['name', 'kurzbeschreibung', 'beschreibung', 'tags'],
    'camping': ['name', 'beschreibung', 'tags'],
    'sehenswuerdigkeiten': ['name', 'kurzbeschreibung', 'beschreibung', 'tags'],
    'erlebnisse': ['name', 'beschreibung', 'tags'],
    'events': ['name', 'beschreibung', 'tags'],
    'magazin': ['titel', 'teaser', 'inhalt', 'kategorie', 'tags'],
}

SINGLETON_FILES = {
    'einstellungen.json': ['site_description'],
    'homepage.json': None,  # spezialbehandlung (tief verschachtelt)
    'home.json': ['hero_titel', 'hero_sub', 'hero_cta'],
    'faq.json': None,  # spezialbehandlung (array von {frage, antwort})
}

# ── Word Count ─────────────────────────────────────────────────
def word_count(text):
    """Zählt Wörter in einem Text (HTML-Tags werden ignoriert)"""
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return len(clean.split())

def total_word_count(entry, fields):
    """Summiert Wörter aller relevanten Felder"""
    total = 0
    for f in fields:
        val = entry.get(f)
        if isinstance(val, str):
            total += word_count(val)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    total += word_count(item)
    return total

# ── API Calls ──────────────────────────────────────────────────
def call_ollama(messages, model, key):
    """Ruft Ollama Chat Completions auf"""
    import urllib.request, urllib.error
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0.3,
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_BASE}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=180)
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Ollama HTTP {e.code}: {body[:200]}")
    except Exception as e:
        raise RuntimeError(f"Ollama Fehler: {str(e)[:200]}")

def call_opencode(messages, model=ZH_MODEL):
    """Ruft opencode deepseek auf (für Chinesisch)"""
    import urllib.request, urllib.error
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0.3,
    }).encode()
    req = urllib.request.Request(
        f"{OPENCODE_BASE}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENCODE_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=300)
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"OpenCode HTTP {e.code}: {body[:200]}")
    except Exception as e:
        raise RuntimeError(f"OpenCode Fehler: {str(e)[:200]}")

def translate_text(text, target_lang, context_hint="", is_tags=False):
    """Übersetzt einen einzelnen Text"""
    if not text or not text.strip():
        return text
    
    wc = word_count(text)
    is_zh = target_lang == 'zh'
    
    if is_tags:
        # Tags sind kurz, immer small model
        model = ZH_MODEL if is_zh else SMALL_MODEL
        system = f"Übersetze die folgenden Tags/Keywords ins {LANG_NAMES.get(target_lang, target_lang)}. Gib NUR die übersetzte Liste zurück, ein Tag pro Zeile. Keine Erklärungen."
        user = f"Tags:\n{text}"
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
    else:
        if is_zh:
            model = ZH_MODEL
            system = "Übersetze den folgenden Text ins Chinesische (Vereinfacht). Behalte alle HTML-Tags (<p>, <strong>, <a>, etc.) exakt bei. Übersetze KEINE URLs oder Pfade. WICHTIG: Füge KEINE Informationen hinzu, die nicht im Original stehen. Übersetze exakt was da steht, nicht mehr."
        else:
            model = SMALL_MODEL if wc <= WORD_LIMIT else LARGE_MODEL
            system = (
                f"Übersetze den folgenden deutschen Text ins {LANG_NAMES.get(target_lang, target_lang)}. "
                f"Behalte alle HTML-Tags (<p>, <strong>, <a href=...>, <em>, etc.) exakt bei und unverändert. "
                f"Übersetze KEINE URLs, Pfade (/orte/..., /images/...), oder numerische Werte. "
                f"Übersetze natürlich und idiomatisch.\n\n"
                f"⚠️ WICHTIGE REGEL: Füge KEINE Informationen, Beschreibungen, Ortsangaben oder Details hinzu, die nicht im Originaltext stehen. "
                f"Wenn der Originaltext nur ein Name oder ein kurzer Satz ist, übersetze nur diesen. "
                f"Erfinde nichts dazu. Übersetze exakt das, was dasteht."
            )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ]
    
    if is_zh:
        result = call_opencode(messages)
    else:
        key, label = get_next_ollama_key()
        result = call_ollama(messages, model, key)
    
    if is_tags:
        # Parse tags result
        translated = [t.strip().strip('"').strip('-').strip() for t in result.strip().split('\n') if t.strip()]
        return translated
    return result.strip()

# ── Entry Translation ──────────────────────────────────────────
LANG_NAMES = {
    'en': 'Englische',
    'fr': 'Französische',
    'it': 'Italienische',
    'es': 'Spanische',
    'zh': 'Chinesische (Vereinfacht)',
}

def translate_entry(entry, collection, target_lang):
    """Übersetzt alle relevanten Textfelder eines Entries"""
    fields = TRANSLATABLE_TEXT_FIELDS.get(collection, [])
    if not fields:
        fields = [k for k, v in entry.items() if isinstance(v, str) and word_count(v) > 3]
    
    # Set von Feldern die typischerweise Eigennamen enthalten (Orte, Betriebe)
    NAME_FIELDS = {'name', 'titel'}
    
    result = deepcopy(entry)
    
    for field in fields:
        if field not in entry:
            continue
        
        val = entry[field]
        
        if field == 'tags':
            if isinstance(val, list) and len(val) > 0:
                tags_text = '\n'.join(val)
                try:
                    translated_tags = translate_text(tags_text, target_lang, is_tags=True)
                    if isinstance(translated_tags, list) and len(translated_tags) == len(val):
                        result['tags'] = translated_tags
                except Exception as e:
                    print(f"   ⚠️ Tag-Übersetzung fehlgeschlagen: {e}")
            continue
        
        if isinstance(val, str) and val.strip():
            # Eigennamen (1-2 Wörter, großgeschrieben) NICHT übersetzen
            if field in NAME_FIELDS:
                words = val.strip().split()
                if len(words) <= 3 and all(w[0].isupper() if w else True for w in words):
                    # Typischer Eigenname - übersetze nur wenn es offensichtlich ein
                    # deutscher Satz ist (enthält Artikel, Präpositionen klein geschrieben)
                    has_german_patterns = any(w.lower() in ['der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einen', 'einem', 'eines', 'am', 'im', 'zum', 'zur', 'vom', 'beim', 'ins', 'durch', 'für', 'auf', 'mit', 'von', 'in', 'und', 'oder', 'aber', 'bei', 'nach', 'aus', 'an'] for w in words)
                    if not has_german_patterns:
                        # Ist ein Eigenname (Ort, Hotelname, etc.) - nicht übersetzen
                        continue
            
            try:
                translated = translate_text(val, target_lang, context_hint=collection, is_tags=False)
                result[field] = translated
            except Exception as e:
                print(f"   ⚠️ Feld '{field}' fehlgeschlagen: {str(e)[:100]}")
    
    return result

def translate_singleton(name, target_lang):
    """Übersetzt Singleton-JSONs (homepage.json, faq.json, etc.)"""
    src_path = os.path.join(DATA_DIR, name)
    if not os.path.exists(src_path):
        return False
    
    with open(src_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"   Übersetze Singleton: {name}")
    
    if name == 'faq.json':
        # Array von {frage, antwort}
        translated = []
        for item in data:
            new_item = deepcopy(item)
            try:
                if item.get('frage'):
                    new_item['frage'] = translate_text(item['frage'], target_lang, is_tags=False)
                if item.get('antwort'):
                    new_item['antwort'] = translate_text(item['antwort'], target_lang, is_tags=False)
            except Exception as e:
                print(f"   ⚠️ FAQ-Eintrag fehlgeschlagen: {e}")
                new_item = item
            translated.append(new_item)
        data = translated
    
    elif name == 'homepage.json':
        data = translate_homepage_json(data, target_lang)
    
    else:
        # Einfache Singletons: übersetze alle String-Felder
        data = translate_simple_json(data, target_lang)
    
    return data

def translate_simple_json(data, target_lang):
    """Übersetzt alle String-Werte in einem flachen JSON"""
    result = deepcopy(data)
    for k, v in data.items():
        if isinstance(v, str) and word_count(v) > 2:
            try:
                result[k] = translate_text(v, target_lang, is_tags=False)
            except Exception as e:
                print(f"   ⚠️ Feld '{k}' fehlgeschlagen: {e}")
    return result

def translate_homepage_json(data, target_lang):
    """Tiefe Übersetzung der homepage.json (verschachtelt)"""
    result = deepcopy(data)
    
    # Strings rekursiv übersetzen
    def translate_value(val, depth=0):
        if isinstance(val, str):
            if word_count(val) > 2:
                try:
                    return translate_text(val, target_lang, is_tags=False)
                except:
                    return val
            return val
        elif isinstance(val, dict):
            return {k: translate_value(v, depth+1) for k, v in val.items()}
        elif isinstance(val, list):
            return [translate_value(item, depth+1) for item in val]
        return val
    
    return translate_value(data)

# ── File Operations ────────────────────────────────────────────
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def write_translated_json(data, target_path):
    """Schreibt übersetztes JSON mit deutscher Sortierung"""
    temp_path = target_path + '.tmp'
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(temp_path, target_path)

# ── Batch Processing ───────────────────────────────────────────
def process_collection(collection, target_lang, batch_idx=None):
    """Übersetzt eine Collection in Batches"""
    src_dir = os.path.join(DATA_DIR, collection)
    tgt_dir = os.path.join(DATA_DIR, target_lang, collection)
    
    if not os.path.exists(src_dir):
        print(f"❌ Collection '{collection}' nicht gefunden in {src_dir}")
        return
    
    # Alle Einträge einsammeln
    entries = []
    for item in sorted(os.listdir(src_dir)):
        item_path = os.path.join(src_dir, item)
        if not os.path.isdir(item_path):
            continue
        json_path = os.path.join(item_path, 'index.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    entries.append((item, data))
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON-Fehler in {json_path}: {e}")
    
    print(f"📦 Collection '{collection}': {len(entries)} Einträge gefunden")
    
    # Batch-Aufteilung (10er Batches)
    BATCH_SIZE = 10
    total_batches = (len(entries) + BATCH_SIZE - 1) // BATCH_SIZE
    
    if batch_idx is not None:
        start = batch_idx * BATCH_SIZE
        end = min(start + BATCH_SIZE, len(entries))
        batches = [(batch_idx, entries[start:end])]
        print(f"   → Batch {batch_idx}: Einträge {start+1}-{end}")
    else:
        batches = []
        for i in range(0, len(entries), BATCH_SIZE):
            batch_num = i // BATCH_SIZE
            batches.append((batch_num, entries[i:i+BATCH_SIZE]))
        print(f"   → {total_batches} Batches a {BATCH_SIZE}")
    
    stats = {'ok': 0, 'skip': 0, 'fail': 0}
    
    for batch_num, batch_entries in batches:
        print(f"\n   ── Batch {batch_num+1}/{total_batches} ({len(batch_entries)} Einträge) ──")
        
        for slug, entry in batch_entries:
            tgt_entry_path = os.path.join(tgt_dir, slug, 'index.json')
            
            # Prüfen ob bereits übersetzt
            if os.path.exists(tgt_entry_path):
                try:
                    existing = json.load(open(tgt_entry_path, 'r', encoding='utf-8'))
                    # Prüfe ob alle Felder da sind
                    src_fields = set(entry.keys())
                    tgt_fields = set(existing.keys())
                    if src_fields.issubset(tgt_fields):
                        print(f"   ⏭️  {slug} — bereits übersetzt")
                        stats['skip'] += 1
                        continue
                except:
                    pass
            
            try:
                wc = total_word_count(entry, TRANSLATABLE_TEXT_FIELDS.get(collection, []))
                model_hint = ZH_MODEL if target_lang == 'zh' else (SMALL_MODEL if wc <= WORD_LIMIT else LARGE_MODEL)
                print(f"   🔄 {slug} ({wc} Wörter → {model_hint})", end='')
                
                translated = translate_entry(entry, collection, target_lang)
                
                ensure_dir(os.path.dirname(tgt_entry_path))
                write_translated_json(translated, tgt_entry_path)
                print(f" ✅")
                stats['ok'] += 1
                
            except Exception as e:
                print(f" ❌ {str(e)[:80]}")
                stats['fail'] += 1
    
    print(f"\n   📊 Ergebnis: {stats['ok']} ✅ | {stats['skip']} ⏭️ | {stats['fail']} ❌")
    return stats

def process_singletons(target_lang):
    """Übersetzt alle Singleton-Dateien"""
    print(f"\n📄 Übersetze Singletons → {target_lang}")
    tgt_dir = os.path.join(DATA_DIR, target_lang)
    ensure_dir(tgt_dir)
    
    stats = {'ok': 0, 'skip': 0, 'fail': 0}
    
    for name in sorted(SINGLETON_FILES.keys()):
        src_path = os.path.join(DATA_DIR, name)
        tgt_path = os.path.join(tgt_dir, name)
        
        if not os.path.exists(src_path):
            continue
        
        # Prüfen ob bereits übersetzt
        if os.path.exists(tgt_path):
            print(f"   ⏭️  {name} — bereits übersetzt")
            stats['skip'] += 1
            continue
        
        print(f"   🔄 {name}", end='')
        try:
            data = translate_singleton(name, target_lang)
            write_translated_json(data, tgt_path)
            print(f" ✅")
            stats['ok'] += 1
        except Exception as e:
            print(f" ❌ {str(e)[:80]}")
            stats['fail'] += 1
    
    return stats

def show_status(target_lang):
    """Zeigt Übersetzungs-Status für eine Sprache"""
    print(f"\n📊 Status: {target_lang.upper()}")
    print(f"{'='*60}")
    
    total_de = 0
    total_translated = 0
    
    for collection in sorted(TRANSLATABLE_TEXT_FIELDS.keys()):
        src = os.path.join(DATA_DIR, collection)
        tgt = os.path.join(DATA_DIR, target_lang, collection)
        
        de_count = 0
        tgt_count = 0
        if os.path.exists(src):
            de_count = len([d for d in os.listdir(src) if os.path.isdir(os.path.join(src, d)) and os.path.exists(os.path.join(src, d, 'index.json'))])
        if os.path.exists(tgt):
            tgt_count = len([d for d in os.listdir(tgt) if os.path.isdir(os.path.join(tgt, d)) and os.path.exists(os.path.join(tgt, d, 'index.json'))])
        
        pct = (tgt_count / de_count * 100) if de_count > 0 else 0
        bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
        print(f"   {collection:20s} [{bar}] {tgt_count:4d}/{de_count} ({pct:5.1f}%)")
        total_de += de_count
        total_translated += tgt_count
    
    # Singletons
    src_singletons = sum(1 for n in SINGLETON_FILES if os.path.exists(os.path.join(DATA_DIR, n)))
    tgt_singletons = sum(1 for n in SINGLETON_FILES if os.path.exists(os.path.join(DATA_DIR, target_lang, n)))
    pct = (tgt_singletons / src_singletons * 100) if src_singletons > 0 else 0
    bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
    print(f"   {'singletons':20s} [{bar}] {tgt_singletons}/{src_singletons} ({pct:5.1f}%)")
    
    total_pct = (total_translated / total_de * 100) if total_de > 0 else 0
    print(f"\n   {'GESAMT':20s}   {total_translated:4d}/{total_de} ({total_pct:5.1f}%)")

# ── Main ───────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    target_lang = sys.argv[1]
    
    if target_lang == 'status':
        # Zeige Status für alle Sprachen
        for lang in ['fr', 'en', 'it', 'es', 'zh']:
            show_status(lang)
        return
    
    if len(sys.argv) < 3:
        print("❌ Bitte Collection angeben (oder 'singletons' oder 'status')")
        sys.exit(1)
    
    collection = sys.argv[2]
    
    batch_idx = None
    if '--batch' in sys.argv:
        idx = sys.argv.index('--batch')
        if idx + 1 < len(sys.argv):
            batch_idx = int(sys.argv[idx + 1])
    
    slug_filter = None
    if '--slug' in sys.argv:
        idx = sys.argv.index('--slug')
        if idx + 1 < len(sys.argv):
            slug_filter = sys.argv[idx + 1]
    
    print(f"\n{'='*60}")
    print(f"🌍 Übersetzung: DE → {LANG_NAMES.get(target_lang, target_lang).upper()}")
    print(f"{'='*60}")
    
    if collection == 'singletons':
        stats = process_singletons(target_lang)
    elif collection == 'all':
        # Alle Collections nacheinander
        overall = {'ok': 0, 'skip': 0, 'fail': 0}
        for coll in sorted(TRANSLATABLE_TEXT_FIELDS.keys()):
            s = process_collection(coll, target_lang, batch_idx)
            if s:
                for k in overall:
                    overall[k] += s.get(k, 0)
        s = process_singletons(target_lang)
        if s:
            for k in overall:
                overall[k] += s.get(k, 0)
        print(f"\n{'='*60}")
        print(f"🏁 ALLES ERLEDIGT: {overall['ok']} ✅ | {overall['skip']} ⏭️ | {overall['fail']} ❌")
    elif collection in TRANSLATABLE_TEXT_FIELDS:
        stats = process_collection(collection, target_lang, batch_idx)
    else:
        print(f"❌ Unbekannte Collection: {collection}")
        print(f"   Verfügbar: {', '.join(sorted(TRANSLATABLE_TEXT_FIELDS.keys()))}, singletons, all, status")
        sys.exit(1)

if __name__ == '__main__':
    main()
