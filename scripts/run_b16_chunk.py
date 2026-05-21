#!/usr/bin/env python3
"""
B16c: 5+ Saetze Batch 1-8 — run one chunk of batches.

Usage:
  python scripts/run_b16_chunk.py 1 4   # batches 1-4
  python scripts/run_b16_chunk.py 5 8   # batches 5-8
  
Output is flushed immediately.
"""

import json, os, sys, time, re, ssl, urllib.request, urllib.error

# Unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# ── API-Key laden ──
API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
if not API_KEY:
    for env_file in [
        "E:/HermesPortable/home/.env",
        os.path.expanduser(r"~\.hermes\.env"),
        os.path.join(os.environ.get("HERMES_HOME", ""), ".env"),
    ]:
        if env_file and os.path.exists(env_file):
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        os.environ[k] = v
            if os.environ.get("OPENCODE_GO_API_KEY"):
                break
    API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")

if not API_KEY:
    print("❌ OPENCODE_GO_API_KEY nicht gefunden")
    sys.exit(1)

API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BATCH_DIR = os.path.join(BASE_DIR, "batches", "b16")


def count_sentences(html_text):
    text = re.sub(r'<[^>]+>', '', html_text)
    text = text.strip()
    sentences = re.split(r'[.!?](?:\s+|$)', text)
    return len([s for s in sentences if s.strip()])


def call_api(prompt):
    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {
                "role": "system",
                "content": "Du schreibst sachliche Beschreibungen für ein Tirol-Tourismusportal. Jede Beschreibung hat MINDESTENS 5 und maximal 8 Sätze. Deutsch. Ausgabe als HTML-Paragraph <p>...</p>. Antworte direkt mit dem HTML, nichts anderes."
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4000,
        "temperature": 0.5,
    }

    try:
        import requests as req_lib
        resp = req_lib.post(
            API_URL, json=body,
            headers={"Authorization": f"Bearer {API_KEY}", "User-Agent": "curl/8.0.0"},
            timeout=120,
        )
        if resp.status_code != 200:
            raise ValueError(f"HTTP {resp.status_code}: {resp.text[:300]}")
        result = resp.json()
    except ImportError:
        req = urllib.request.Request(
            API_URL, data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            method="POST",
        )
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            resp = urllib.request.urlopen(req, timeout=120, context=ctx)
            result = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise ValueError(f"HTTP {e.code}: {e.read().decode()[:300]}")

    msg = result["choices"][0]["message"]
    content = (msg.get("content") or "").strip()
    if not content:
        raise ValueError(f"Empty content (reasoning: {len(msg.get('reasoning_content',''))} chars)")

    if content.startswith("```"):
        lines = content.split("\n")
        clean_lines = [l for l in lines if not l.startswith("```")]
        content = "\n".join(clean_lines).strip()
    if not content.startswith("<"):
        content = f"<p>{content}</p>"
    return content


def generate_description(name, ort, typ_label, max_retries=5):
    prompt = (
        f"Schreibe eine Beschreibung über '{name}'"
        + (f" in {ort}, Tirol, Österreich" if ort else " in Tirol, Österreich")
        + f".\nArt: {typ_label}.\n\n"
        f"MINDESTENS 5 Sätze, maximal 8 Sätze.\n"
        f"Sachlich, informativ, kein Marketington, keine Superlative.\n"
        f"Beschreibe Lage, Umgebung, Ausstattung/Merkmale, Atmosphäre und Zielpublikum.\n"
        f"Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"
    )

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            content = call_api(prompt)
            s = count_sentences(content)
            if s >= 5:
                return content
            else:
                raise ValueError(f"Nur {s} Sätze (brauche ≥5)")
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait = attempt * 3
                print(f"    ⚠️ Versuch {attempt} fehlgeschlagen ({e}). Warte {wait}s...", flush=True)
                time.sleep(wait)
            else:
                raise last_error


def entry_is_ok(filepath):
    if not os.path.exists(filepath):
        return False
    try:
        entry = json.load(open(filepath, encoding="utf-8"))
        desc = entry.get("beschreibung", "")
        return desc and count_sentences(desc) >= 5
    except Exception:
        return False


def process_batch(batch_path, total_entries, processed_so_far):
    with open(batch_path, encoding="utf-8") as f:
        batch = json.load(f)

    print(f"\n{'='*60}", flush=True)
    print(f"📦 Batch: {os.path.basename(batch_path)} — {len(batch)} Einträge", flush=True)
    print(f"{'='*60}", flush=True)

    enriched = 0
    errors = 0

    for idx, item in enumerate(batch):
        filepath = item["filepath"]
        name = item["name"]
        ort = item.get("ort", "")
        typ = item.get("typ", "")

        global_idx = processed_so_far + idx + 1

        if not os.path.exists(filepath):
            print(f"  [{global_idx}/{total_entries}] ❌ Datei nicht gefunden: {filepath}", flush=True)
            errors += 1
            continue

        # Skip if already >=5 sentences (resume mode)
        if entry_is_ok(filepath):
            print(f"  [{global_idx}/{total_entries}] {name} — ✅ bereits ≥5 Sätze", flush=True)
            enriched += 1  # count as done
            continue

        typ_label = {"hotel":"Hotel","gasthof":"Gasthof","ferienwohnung":"Ferienwohnung",
                     "ferienhaus":"Ferienhaus","jugendherberge":"Jugendherberge",
                     "camping":"Campingplatz","bauernhof":"Bauernhof"}.get(typ, typ)

        print(f"  [{global_idx}/{total_entries}] {name} ({typ_label})...", end=" ", flush=True)

        try:
            desc = generate_description(name, ort, typ_label)
            new_saetze = count_sentences(desc)

            with open(filepath, encoding="utf-8") as f:
                entry = json.load(f)
            entry["beschreibung"] = desc
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)

            print(f"✅ {new_saetze} Sätze", flush=True)
            enriched += 1
        except Exception as e:
            print(f"❌ Fehler: {e}", flush=True)
            errors += 1

        if idx < len(batch) - 1:
            time.sleep(1.0)

    return enriched, errors


def main():
    start_batch = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end_batch = int(sys.argv[2]) if len(sys.argv) > 2 else 8

    batch_files = []
    for i in range(start_batch, end_batch + 1):
        bf = os.path.join(BATCH_DIR, f"batch_{i:03d}.json")
        if os.path.exists(bf):
            batch_files.append(bf)

    if not batch_files:
        print(f"❌ Keine Batch-Dateien {start_batch}-{end_batch} in {BATCH_DIR}")
        sys.exit(1)

    total_entries = sum(len(json.load(open(bf, encoding="utf-8"))) for bf in batch_files)
    print(f"🚀 B16c Batches {start_batch}-{end_batch}: {len(batch_files)} Batches, {total_entries} Einträge", flush=True)

    total_enriched = 0
    total_errors = 0
    processed = 0

    for bf in batch_files:
        enriched, errors = process_batch(bf, 48, processed)  # 48 = total across all 8 batches
        total_enriched += enriched
        total_errors += errors
        processed += len(json.load(open(bf, encoding="utf-8")))

    print(f"\n{'='*60}", flush=True)
    print(f"✅ Chunk {start_batch}-{end_batch}: {total_enriched} OK, {total_errors} Fehler", flush=True)
    print(f"{'='*60}", flush=True)


if __name__ == "__main__":
    main()
