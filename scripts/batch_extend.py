#!/usr/bin/env python3
"""
batch_extend.py — Schnelle Batch-Verarbeitung für Beschreibungs-Erweiterung
Verarbeitet 3 Einträge pro API-Call (bündelt die Prompts).

Aufruf:
  python scripts/batch_extend.py unterkuenfte --start 0 --count 300
  python scripts/batch_extend.py unterkuenfte --resume
  python scripts/batch_extend.py camping --all
"""

import json, os, sys, time, re, glob, argparse

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "data")
API_URL = "https://opencode.ai/zen/go/v1/chat/completions"

# API-Key laden
API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
if not API_KEY:
    for env_file in [
        "E:/HermesPortable/home/.env",
        os.path.expanduser(r"~\.hermes\.env"),
    ]:
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    if line.startswith("OPENCODE_GO_API_KEY="):
                        API_KEY = line.split("=", 1)[1].strip()
                        break
            if API_KEY:
                break

try:
    import requests as req_lib
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

BATCH_SIZE = 3  # Entries per API call

def count_sentences(text):
    clean = re.sub(r'<[^>]+>', '', text).replace('\n', ' ').strip()
    return len([s for s in re.split(r'(?<=[.!?])\s+', clean) if s.strip()])

def load_entries(collection):
    path = os.path.join(DATA_DIR, collection)
    entries = []
    for slug in sorted(os.listdir(path)):
        idx_path = os.path.join(path, slug, "index.json")
        if not os.path.exists(idx_path):
            continue
        with open(idx_path, encoding="utf-8") as f:
            data = json.load(f)
        
        beschreibung = data.get("beschreibung", "")
        sents = count_sentences(beschreibung)
        
        entries.append({
            "slug": slug,
            "filepath": idx_path,
            "collection": collection,
            "name": data.get("name", slug),
            "ort": data.get("ort", ""),
            "region": data.get("region", ""),
            "typ": data.get("kategorie", data.get("typ", "")),
            "beschreibung": beschreibung,
            "data": data,
            "sentences": sents,
        })
    return entries

COLLECTION_LABELS = {
    "sehenswuerdigkeiten": "Sehenswürdigkeit",
    "unterkuenfte": "Unterkunft/Unterkünfte/Gasthof/Hotel/Ferienwohnung",
    "camping": "Campingplatz/Camping",
}

def build_batch_prompt(batch_entries):
    """Build prompt for 3 entries."""
    lines = []
    for i, entry in enumerate(batch_entries):
        label = COLLECTION_LABELS.get(entry["collection"], entry["collection"])
        lines.append(f"=== ENTRY {i+1} ===")
        lines.append(f"Name: {entry['name']}")
        lines.append(f"Ort: {entry['ort']}, Tirol, Österreich")
        lines.append(f"Typ/Kategorie: {entry['typ']} ({label})")
        lines.append("")
    
    prompt = (
        "Schreibe für jede der folgenden Einträge eine sachlich-informative Beschreibung "
        "mit genau 5 bis 8 Sätzen.\n\n"
        + "\n".join(lines) +
        "\nWICHTIG: Antworte EXAKT in diesem Format, getrennt durch '---NÄCHSTER EINTRAG---':\n"
        "<p>Beschreibung für Entry 1...</p>\n"
        "---NÄCHSTER EINTRAG---\n"
        "<p>Beschreibung für Entry 2...</p>\n"
        "---NÄCHSTER EINTRAG---\n"
        "<p>Beschreibung für Entry 3...</p>\n\n"
        "Jede Beschreibung: 5-8 Sätze, sachlich, informativ, HTML mit <strong>Hervorhebungen</strong>.\n"
        "Kein Marketing-Jargon, keine Superlative, keine Wiederholungen."
    )
    return prompt

def call_api(prompt):
    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "Du schreibst sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch. Antworte NUR mit den Beschreibungen im geforderten Format, keine Denkprozesse oder Einleitungen."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096,
        "temperature": 0.3,
    }

    if HAS_REQUESTS:
        try:
            resp = req_lib.post(API_URL, json=body, headers={
                "Authorization": f"Bearer {API_KEY}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }, timeout=180)
            if resp.status_code == 200:
                result = resp.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                print(f"    ⚠️ HTTP {resp.status_code}")
                time.sleep(5)
                resp = req_lib.post(API_URL, json=body, headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                }, timeout=180)
                if resp.status_code == 200:
                    result = resp.json()
                    return result["choices"][0]["message"]["content"].strip()
                else:
                    raise ValueError(f"HTTP {resp.status_code} after retry")
        except Exception as e:
            print(f"    ⚠️ API Error: {e}")
            return ""
    else:
        import urllib.request
        req = urllib.request.Request(API_URL, data=json.dumps(body).encode(), headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }, method="POST")
        try:
            resp = urllib.request.urlopen(req, timeout=180)
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"    ⚠️ API Error: {e}")
            time.sleep(5)
            try:
                resp = urllib.request.urlopen(req, timeout=180)
                result = json.loads(resp.read())
                return result["choices"][0]["message"]["content"].strip()
            except Exception as e2:
                print(f"    ⚠️ Retry failed: {e2}")
                return ""

def parse_batch_response(text):
    """Split the API response into individual descriptions."""
    parts = re.split(r'---NÄCHSTER EINTRAG---', text)
    descriptions = []
    for part in parts:
        part = part.strip()
        # Clean markdown code fences if present
        part = re.sub(r'^```(?:html)?\s*', '', part)
        part = re.sub(r'\s*```$', '', part)
        part = part.strip()
        # Ensure HTML wrapper
        if part and not part.startswith("<"):
            part = f"<p>{part}</p>"
        descriptions.append(part)
    return descriptions

def process_collection(collection, start=0, count=None, resume=False):
    print(f"\n{'='*60}")
    print(f"📂 Processing {collection}")
    print(f"{'='*60}")
    
    entries = load_entries(collection)
    
    # Filter to entries with <5 sentences
    needs_work = [e for e in entries if e["sentences"] < 5]
    print(f"  {len(needs_work)} entries need <5 sentences (of {len(entries)} total)")
    
    if count:
        needs_work = needs_work[start:start+count]
    elif start:
        needs_work = needs_work[start:]
    
    if not needs_work:
        print("  ✅ All done!")
        return
    
    total = len(needs_work)
    enriched = 0
    failed = 0
    
    # Process in batches of BATCH_SIZE
    for batch_idx in range(0, total, BATCH_SIZE):
        batch = needs_work[batch_idx:batch_idx + BATCH_SIZE]
        actual_size = len(batch)
        
        items_str = ", ".join([f"{e['name']}({e['ort']})" for e in batch])
        print(f"\n  Batch {batch_idx//BATCH_SIZE + 1}/{(total + BATCH_SIZE - 1)//BATCH_SIZE}: {items_str}")
        sys.stdout.flush()
        
        if actual_size == 1:
            # Single entry - use simple prompt
            entry = batch[0]
            label = COLLECTION_LABELS.get(entry["collection"], entry["collection"])
            prompt = (
                f"Schreibe eine sachlich-informative Beschreibung von 5 bis 8 Sätzen "
                f"über {label} '{entry['name']}' in {entry['ort']}, Tirol, Österreich. "
                f"Typ: {entry['typ']}. "
                f"Beschreibe Lage, Angebote, Besonderheiten. "
                f"Sachlich, informativ. "
                f"Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"
            )
            
            text = call_api(prompt)
            descriptions = [text] if text else [""]
        else:
            prompt = build_batch_prompt(batch)
            text = call_api(prompt)
            if text:
                descriptions = parse_batch_response(text)
            else:
                descriptions = [""] * actual_size
        
        # Process descriptions
        for i, entry in enumerate(batch):
            desc = descriptions[i] if i < len(descriptions) else ""
            
            if desc and len(desc.strip("<>p/ ")) >= 20:
                sents = count_sentences(desc)
                if sents >= 5:
                    entry["data"]["beschreibung"] = desc
                    try:
                        with open(entry["filepath"], "w", encoding="utf-8") as f:
                            json.dump(entry["data"], f, indent=2, ensure_ascii=False)
                        print(f"    ✅ {entry['name']}: {sents} Sätze")
                        enriched += 1
                    except Exception as e:
                        print(f"    ❌ {entry['name']}: Schreibfehler - {e}")
                        failed += 1
                else:
                    print(f"    ⚠️ {entry['name']}: Nur {sents} Sätze")
                    failed += 1
            else:
                print(f"    ❌ {entry['name']}: Leer/zu kurz")
                failed += 1
            
            sys.stdout.flush()
        
        # Rate limit
        time.sleep(1.5)
    
    print(f"\n  ✅ {collection}: {enriched} enriched, {failed} failed")
    return enriched


def main():
    parser = argparse.ArgumentParser(description="Batch description extension (3 entries per API call)")
    parser.add_argument("collection", choices=["sehenswuerdigkeiten", "unterkuenfte", "camping"])
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int, help="Entries to process")
    parser.add_argument("--resume", action="store_true", help="Resume from last progress")
    parser.add_argument("--all", action="store_true", help="Process all entries")
    args = parser.parse_args()
    
    if args.all:
        process_collection(args.collection, resume=args.resume)
    elif args.count:
        process_collection(args.collection, start=args.start, count=args.count, resume=args.resume)
    else:
        process_collection(args.collection, start=args.start, resume=args.resume)

if __name__ == "__main__":
    main()
