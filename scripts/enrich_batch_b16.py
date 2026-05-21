#!/usr/bin/env python3
"""
B16c: 5+ Saetze Batch 1-8 — regeneriere Beschreibungen auf mindestens 5 Sätze.

Liest Batch-Dateien aus scripts/batches/b16/batch_001..008.json,
generiert neue 5-8-sätzige Beschreibungen via deepseek-v4-flash,
schreibt sie in die jeweiligen index.json zurück.

Usage:
  python scripts/enrich_batch_b16.py
  python scripts/enrich_batch_b16.py --resume   # überspringe bereits OK-Einträge
  python scripts/enrich_batch_b16.py --batch 3  # nur Batch 3 verarbeiten
"""

import json, os, sys, time, re, ssl, urllib.request, urllib.error

# ── API-Key laden ──────────────────────────────────────────────
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
    """Zähle Sätze in einem HTML-Text (entferne Tags zuerst)."""
    text = re.sub(r'<[^>]+>', '', html_text)
    text = text.strip()
    sentences = re.split(r'[.!?](?:\s+|$)', text)
    return len([s for s in sentences if s.strip()])


def call_api(prompt):
    """Einzelner API-Aufruf. Returns (content, reasoning) or raises."""
    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Du schreibst sachliche Beschreibungen für ein Tirol-Tourismusportal. "
                    "Jede Beschreibung hat MINDESTENS 5 und maximal 8 Sätze. "
                    "Deutsch. Ausgabe als HTML-Paragraph <p>...</p>. "
                    "Antworte direkt mit dem HTML, nichts anderes."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4000,
        "temperature": 0.5,
    }

    try:
        import requests as req_lib
        resp = req_lib.post(
            API_URL,
            json=body,
            headers={"Authorization": f"Bearer {API_KEY}", "User-Agent": "curl/8.0.0"},
            timeout=120,
        )
        if resp.status_code != 200:
            raise ValueError(f"HTTP {resp.status_code}: {resp.text[:300]}")
        result = resp.json()
    except ImportError:
        req = urllib.request.Request(
            API_URL,
            data=json.dumps(body).encode(),
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
    reasoning = (msg.get("reasoning_content") or "").strip()

    if not content:
        raise ValueError(f"Empty content (reasoning: {len(reasoning)} chars)")

    # Remove markdown code fences
    if content.startswith("```"):
        lines = content.split("\n")
        clean_lines = [l for l in lines if not l.startswith("```")]
        content = "\n".join(clean_lines).strip()

    # Wrap in <p> if not already HTML
    if not content.startswith("<"):
        content = f"<p>{content}</p>"

    return content, reasoning


def generate_description(name, ort, typ_label, max_retries=5):
    """Generiere 5-8 Sätze HTML-Beschreibung mit Retry."""
    prompt = (
        f"Schreibe eine Beschreibung über '{name}'"
        + (f" in {ort}, Tirol, Österreich" if ort else " in Tirol, Österreich")
        + f".\nArt: {typ_label}.\n\n"
        f"MINDESTENS 5 Sätze, maximal 8 Sätze.\n"
        f"Sachlich, informativ, kein Marketington, keine Superlative.\n"
        f"Beschreibe die Lage, die Umgebung, die Ausstattung/Merkmale, "
        f"die Atmosphäre und für welche Gäste der Ort geeignet ist.\n"
        f"Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"
    )

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            content, reasoning = call_api(prompt)
            s = count_sentences(content)
            if s >= 5:
                return content
            else:
                raise ValueError(f"Nur {s} Sätze (brauche ≥5)")
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait = attempt * 3  # progressive backoff
                print(f"⚠️ Versuch {attempt} fehlgeschlagen ({e}). Warte {wait}s...", flush=True)
                time.sleep(wait)
            else:
                raise last_error


def entry_is_ok(filepath, min_sentences=5):
    """Check if entry already has a good description."""
    if not os.path.exists(filepath):
        return False
    try:
        entry = json.load(open(filepath, encoding="utf-8"))
        desc = entry.get("beschreibung", "")
        if not desc:
            return False
        return count_sentences(desc) >= min_sentences
    except Exception:
        return False


def process_batch(batch_path, resume=False, total_entries=None, processed_so_far=0):
    """Process a single batch file. Returns (enriched, skipped, errors)."""
    with open(batch_path, encoding="utf-8") as f:
        batch = json.load(f)

    print(f"\n{'='*60}")
    print(f"📦 Batch: {os.path.basename(batch_path)} — {len(batch)} Einträge")
    print(f"{'='*60}")

    enriched = 0
    skipped = 0
    errors = 0

    for idx, item in enumerate(batch):
        filepath = item["filepath"]
        name = item["name"]
        ort = item.get("ort", "")
        typ = item.get("typ", "")
        aktuelle_saetze = item.get("aktuelle_saetze", "?")

        global_idx = processed_so_far + idx + 1
        total_str = f"/{total_entries}" if total_entries else ""

        if not os.path.exists(filepath):
            print(f"  [{global_idx}{total_str}] ❌ Datei nicht gefunden: {filepath}")
            errors += 1
            continue

        # Resume mode: skip if already >= 5 sentences
        if resume and entry_is_ok(filepath, 5):
            print(f"  [{global_idx}{total_str}] {name} — ✅ bereits ≥5 Sätze")
            skipped += 1
            continue

        # Typ-Label
        typ_label = {
            "hotel": "Hotel", "gasthof": "Gasthof",
            "ferienwohnung": "Ferienwohnung", "ferienhaus": "Ferienhaus",
            "jugendherberge": "Jugendherberge", "camping": "Campingplatz",
            "bauernhof": "Bauernhof",
        }.get(typ, typ)

        print(f"  [{global_idx}{total_str}] {name} ({typ_label}) — aktuell {aktuelle_saetze} Sätze...", end=" ", flush=True)

        try:
            desc = generate_description(name, ort, typ_label)
            new_saetze = count_sentences(desc)

            with open(filepath, encoding="utf-8") as f:
                entry = json.load(f)
            entry["beschreibung"] = desc
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)

            status = "✅" if new_saetze >= 5 else "⚠️"
            print(f"{status} {new_saetze} Sätze")
            enriched += 1

        except Exception as e:
            print(f"❌ Fehler: {e}")
            errors += 1

        # Rate limit: 1s zwischen Requests
        if idx < len(batch) - 1:
            time.sleep(1.0)

    return enriched, skipped, errors


def main():
    import argparse
    parser = argparse.ArgumentParser(description="B16c: 5+ Sätze für Unterkunfts-Beschreibungen")
    parser.add_argument("--resume", action="store_true", help="Überspringe bereits OK-Einträge (≥5 Sätze)")
    parser.add_argument("--batch", type=int, help="Nur eine bestimmte Batch-Nummer verarbeiten (1-8)")
    parser.add_argument("--heartbeat-every", type=int, default=10, help="Alle N Einträge Heartbeat senden")
    args = parser.parse_args()

    if args.batch:
        batch_nums = [args.batch]
    else:
        batch_nums = list(range(1, 9))

    batch_files = []
    for i in batch_nums:
        bf = os.path.join(BATCH_DIR, f"batch_{i:03d}.json")
        if os.path.exists(bf):
            batch_files.append(bf)
        else:
            print(f"⚠️ Batch batch_{i:03d}.json nicht gefunden")

    if not batch_files:
        print(f"❌ Keine Batch-Dateien in {BATCH_DIR} gefunden")
        sys.exit(1)

    total_entries = 0
    for bf in batch_files:
        with open(bf, encoding="utf-8") as f:
            total_entries += len(json.load(f))

    print(f"🚀 B16c: 5+ Sätze — {len(batch_files)} Batches, {total_entries} Einträge")
    print(f"   API: deepseek-v4-flash | Resume: {args.resume}")

    total_enriched = 0
    total_skipped = 0
    total_errors = 0
    processed = 0

    for bf in batch_files:
        enriched, skipped, errors = process_batch(
            bf, resume=args.resume, total_entries=total_entries, processed_so_far=processed
        )
        total_enriched += enriched
        total_skipped += skipped
        total_errors += errors
        processed += len(json.load(open(bf, encoding="utf-8")))

        # — Heartbeat alle batches (damit der Dispatcher weiss wir leben noch)
        try:
            from hermes_tools import kanban_heartbeat
            kanban_heartbeat(note=f"Batch {os.path.basename(bf)}: {enriched} enriched, {skipped} skipped, {errors} errors | {processed}/{total_entries} entries done")
        except ImportError:
            pass

    print(f"\n{'='*60}")
    print(f"✅ FERTIG: {total_enriched} angereichert, {total_skipped} übersprungen, {total_errors} Fehler")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
