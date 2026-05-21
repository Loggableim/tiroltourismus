#!/usr/bin/env python3
"""
batch_extend_v3.py — Batch description extension with persistent progress tracking.
Processes 3 entries per API call for efficiency. Saves progress after each batch.
Can resume if interrupted.

Usage:
  python scripts/batch_extend_v3.py unterkuenfte [--resume]
  python scripts/batch_extend_v3.py camping [--resume]
"""
import json, os, sys, time, re, glob, argparse

# ── Config ──
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "data")
API_URL = "https://opencode.ai/zen/go/v1/chat/completions"

API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
if not API_KEY:
    for env_file in ["E:/HermesPortable/home/.env", os.path.expanduser("~/.hermes/.env")]:
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

COLLECTION_LABELS = {
    "unterkuenfte": "Unterkunft/Gasthof/Hotel/Ferienwohnung/Gästezimmer",
    "camping": "Campingplatz/Camping",
}

# ── Helpers ──

def count_sentences(text):
    clean = re.sub(r'<[^>]+>', '', text).replace('\n', ' ').strip()
    return len([s for s in re.split(r'(?<=[.!?])\s+', clean) if s.strip()])

def load_entries_needing_update(collection):
    """Return entries with <5 sentences."""
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
        if sents < 5:
            entries.append({
                "slug": slug,
                "filepath": idx_path,
                "collection": collection,
                "name": data.get("name", slug),
                "ort": data.get("ort", ""),
                "region": data.get("region", ""),
                "typ": data.get("kategorie", data.get("typ", "")),
                "data": data,
                "sentences": sents,
            })
    return entries

def build_prompt(batch):
    """Build prompt for up to 3 entries."""
    lines = []
    label = COLLECTION_LABELS.get(batch[0]["collection"], batch[0]["collection"])
    for i, entry in enumerate(batch):
        lines.append(f"=== ENTRY {i+1}: {entry['name']} ===")
        lines.append(f"Location: {entry['ort']}, Tirol, Austria")
        lines.append(f"Type: {entry['typ']} ({label})")
        lines.append("")
    
    prompt = (
        "Write a factual, informative description in German for EACH of the following tourism entries. "
        "Each description must be exactly 5 to 8 sentences long. Use HTML paragraphs with <strong> for key terms.\n\n"
        + "\n".join(lines) +
        "\nIMPORTANT: Respond EXACTLY in this format, separated by '---NEXT---':\n"
        "<p>Description for entry 1...</p>\n"
        "---NEXT---\n"
        "<p>Description for entry 2...</p>\n"
        "---NEXT---\n"
        "<p>Description for entry 3...</p>\n\n"
        "Style: factual, informative, no marketing jargon, no superlatives. "
        "Describe location, offerings, features, and what visitors can expect."
    )
    return prompt

def call_api(prompt):
    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "You write factual German descriptions for a Tirol tourism portal. Respond ONLY with the HTML descriptions in the requested format. No thinking, no introductions."},
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
                return resp.json()["choices"][0]["message"]["content"].strip()
            else:
                print(f"  ⚠️ HTTP {resp.status_code}, retrying...")
                time.sleep(5)
                resp = req_lib.post(API_URL, json=body, headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                }, timeout=180)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"].strip()
                raise ValueError(f"HTTP {resp.status_code}")
        except Exception as e:
            print(f"  ⚠️ API Error: {e}")
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
            return json.loads(resp.read())["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"  ⚠️ API Error: {e}")
            time.sleep(5)
            try:
                resp = urllib.request.urlopen(req, timeout=180)
                return json.loads(resp.read())["choices"][0]["message"]["content"].strip()
            except Exception as e2:
                print(f"  ⚠️ Retry failed: {e2}")
                return ""

def parse_descriptions(text, expected_count):
    """Split API response into individual descriptions."""
    parts = re.split(r'---NEXT---', text)
    results = []
    for part in parts[:expected_count]:
        part = part.strip()
        part = re.sub(r'^```(?:html)?\s*', '', part)
        part = re.sub(r'\s*```$', '', part)
        part = part.strip()
        if part and not part.startswith("<"):
            part = f"<p>{part}</p>"
        results.append(part)
    # Pad if less than expected
    while len(results) < expected_count:
        results.append("")
    return results

# ── Main processing function (callable) ──

def process_collection(collection, resume=False, max_batches=None):
    BATCH_SIZE = 3
    entries = load_entries_needing_update(collection)
    total = len(entries)
    
    print(f"{collection}: {total} entries need update")
    
    if total == 0:
        print("  ✅ All done!")
        return 0, 0
    
    # Load progress
    progress_file = os.path.join(os.path.dirname(__file__), f".progress_{collection}.json")
    done_slugs = set()
    if resume and os.path.exists(progress_file):
        try:
            done_slugs = set(json.load(open(progress_file)))
            print(f"  Resuming: {len(done_slugs)} already done")
        except:
            pass
    
    # Filter
    remaining = [e for e in entries if e["slug"] not in done_slugs]
    print(f"  Remaining: {len(remaining)}")
    
    if max_batches:
        # Limit to first N batches for testing
        limit = max_batches * BATCH_SIZE
        remaining = remaining[:limit]
    
    enriched = 0
    failed = 0
    total_batches = (len(remaining) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for batch_idx in range(0, len(remaining), BATCH_SIZE):
        batch = remaining[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1
        names = ", ".join([f"{e['name']}({e['ort']})" for e in batch])
        print(f"  [{batch_num}/{total_batches}] {names}", end="", flush=True)
        
        if len(batch) == 1:
            entry = batch[0]
            label = COLLECTION_LABELS.get(collection, collection)
            prompt = (
                f"Write a factual German description of 5-8 sentences about "
                f"the {label} '{entry['name']}' in {entry['ort']}, Tirol, Austria. "
                f"Type: {entry['typ']}. Describe location, offerings, features. "
                f"Factual, informative. "
                f"Format: <p>Text with <strong>highlights</strong>.</p>"
            )
            text = call_api(prompt)
            descs = [text] if text else [""]
        else:
            prompt = build_prompt(batch)
            text = call_api(prompt)
            descs = parse_descriptions(text, len(batch)) if text else [""] * len(batch)
        
        for i, entry in enumerate(batch):
            desc = descs[i] if i < len(descs) else ""
            if desc and len(desc.strip("<>p/ ")) >= 20:
                sents = count_sentences(desc)
                if sents >= 5:
                    entry["data"]["beschreibung"] = desc
                    with open(entry["filepath"], "w", encoding="utf-8") as f:
                        json.dump(entry["data"], f, indent=2, ensure_ascii=False)
                    enriched += 1
                    done_slugs.add(entry["slug"])
                    print(f" ✅{sents}", end="", flush=True)
                else:
                    failed += 1
                    print(f" ⚠️{sents}s", end="", flush=True)
            else:
                failed += 1
                print(f" ❌", end="", flush=True)
        
        # Save progress
        with open(progress_file, "w") as f:
            json.dump(list(done_slugs), f)
        
        print()
        time.sleep(1.5)
    
    print(f"\n  ✅ Result: {enriched} enriched, {failed} failed")
    return enriched, failed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("collection", choices=["unterkuenfte", "camping"])
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--test", type=int, help="Process only N batches for testing")
    args = parser.parse_args()
    
    enriched, failed = process_collection(args.collection, resume=args.resume, max_batches=args.test)
    print(f"Total: {enriched} enriched, {failed} failed")


if __name__ == "__main__":
    main()
