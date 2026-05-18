#!/usr/bin/env python3
"""
enrich_batch.py — KI-Beschreibungen für Unterkünfte generieren (Batch-Verarbeitung)

Aufruf:
  python scripts/enrich_batch.py --start 0 --count 6
  python scripts/enrich_batch.py --file batches/batch_003.json

Liest index.json aus src/data/unterkuenfte/, generiert fehlende Felder per deepseek,
schreibt sie zurück. Rate-Limit: 1 Request pro Sekunde.
"""
import json, os, sys, time, glob, re, argparse, ssl, urllib.request

# Load .env if OPENCODE_GO_API_KEY is not yet set
env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "home", ".env")
if not os.environ.get("OPENCODE_GO_API_KEY") and os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k] = v

# Use requests if available (handles SSL/cert validation better on Windows)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "data", "unterkuenfte")
BATCH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batches")
os.makedirs(BATCH_DIR, exist_ok=True)

API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
if not API_KEY:
    # Fallback: read from Hermes .env file
    for _ep in [
        os.path.expanduser(r"~\.hermes\.env"),
        r"C:\Users\logga\.hermes\.env",
        os.path.join(os.environ.get("HERMES_HOME", ""), ".env"),
    ]:
        if os.path.exists(_ep):
            with open(_ep, "r", encoding="utf-8") as _f:
                for _line in _f:
                    _line = _line.strip()
                    if _line.startswith("OPENCODE_GO_API_KEY="):
                        API_KEY = _line.split("=", 1)[1].strip()
                        break
            if API_KEY:
                break


def load_all_entries():
    """Alle index.json aus unterkuenfte/ laden."""
    entries = []
    for f in sorted(glob.glob(os.path.join(DATA_DIR, "*", "index.json"))):
        slug = os.path.basename(os.path.dirname(f))
        try:
            data = json.load(open(f, encoding="utf-8"))
            entries.append((slug, f, data))
        except:
            pass
    return entries


def needs_enrichment(entry):
    """Braucht dieser Eintrag eine Beschreibung?"""
    return not entry.get("beschreibung") or len(entry.get("beschreibung", "").strip()) < 10


def generate_description(name, ort, typ, region):
    """Generiere eine kurze HTML-Beschreibung via deepseek."""
    typ_label = {"hotel": "Hotel", "gasthof": "Gasthof", "ferienwohnung": "Ferienwohnung",
                 "ferienhaus": "Ferienhaus", "jugendherberge": "Jugendherberge",
                 "camping": "Campingplatz", "bauernhof": "Bauernhof"}.get(typ, typ)

    prompt = (
        f"Schreibe 2-3 Sätze HTML über '{name}' in {ort}, Tirol, Österreich. "
        f"Art: {typ_label}. "
        f"Beschreibe die Lage, Atmosphäre und was Gäste erwartet. "
        f"Sachlich, kein Marketington, kein Superlativ. "
        f"Maximal 120 Wörter. "
        f"Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"
    )

    body = {
        "model": "minimax-m2.7",
        "messages": [
            {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph. Antworte direkt mit dem HTML, ohne nachzudenken."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2000,
        "temperature": 0.4,
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "User-Agent": "curl/8.0.0",
        },
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read())
        text = result["choices"][0]["message"]["content"].strip()
        if not text:
            raise ValueError("Empty content from API")
        # Clean up - ensure it's wrapped in <p>
        if not text.startswith("<"):
            text = f"<p>{text}</p>"
        return text
    except Exception as e:
        print(f"    ⚠️ API-Fehler: {e}")
        # Retry once after a short wait
        try:
            time.sleep(3)
            resp = urllib.request.urlopen(req, timeout=120)
            result = json.loads(resp.read())
            text = result["choices"][0]["message"]["content"].strip()
            if not text:
                raise ValueError("Empty content on retry")
            if not text.startswith("<"):
                text = f"<p>{text}</p>"
            return text
        except Exception as e2:
            print(f"    ⚠️ Retry auch fehlgeschlagen: {e2}")
            return ""


def generate_tags(name, typ, region):
    """Generiere passende Tags basierend auf Name + Typ + Region."""
    tags = set()
    # Typ-basiert
    typ_tags = {
        "hotel": ["hotel", "übernachten"],
        "gasthof": ["gasthof", "kulinarik"],
        "ferienwohnung": ["ferienwohnung", "familie"],
        "ferienhaus": ["ferienhaus", "familie"],
        "jugendherberge": ["jugendherberge", "günstig"],
        "camping": ["camping", "outdoor", "familie"],
        "bauernhof": ["bauernhof", "urlaub-am-bauernhof", "familie"],
    }
    tags.update(typ_tags.get(typ, ["übernachten"]))
    # Keyword-basiert
    kw_map = {
        "wellness": ["wellness", "entspannung"], "spa": ["wellness", "entspannung"],
        "sauna": ["wellness", "sauna"], "pool": ["pool", "schwimmen"],
        "berg": ["berg", "wandern"], "alm": ["alm", "natur"],
        "ski": ["ski", "winter"], "sport": ["sport", "aktiv"],
        "golf": ["golf", "sport"], "see": ["see", "wasser"],
        "bio": ["bio", "nachhaltig"], "familie": ["familie", "kinder"],
        "romantik": ["romantik", "paare"], "design": ["design", "modern"],
        "schloss": ["schloss", "historisch"], "luxus": ["luxus", "premium"],
    }
    name_lower = name.lower()
    for kw, taglist in kw_map.items():
        if kw in name_lower:
            tags.update(taglist)
    return sorted(tags)[:6]


def generate_amenities(entry):
    """Leite Ausstattung aus Name + Kontext ab."""
    name_lower = entry.get("name", "").lower()
    implied = set()
    if any(w in name_lower for w in ["wellness", "spa", "sauna"]):
        implied.add("sauna")
    if any(w in name_lower for w in ["pool", "bad", "schwimm"]):
        implied.add("pool")
    if any(w in name_lower for w in ["golf"]):
        implied.add("golfplatz")
    if any(w in name_lower for w in ["camping"]):
        implied.add("stromanschluss")
        implied.add("sanitäranlagen")
    return sorted(implied)


def process_batch(entries, start, count):
    """Verarbeite `count` Einträge ab Index `start`."""
    batch = entries[start:start+count]
    enriched = 0
    total = len(batch)

    for idx, (slug, filepath, entry) in enumerate(batch):
        if not needs_enrichment(entry):
            print(f"  [{start+idx+1}] {entry.get('name','?')}: bereits vorhanden ✅")
            continue

        print(f"  [{start+idx+1}/{start+total}] {entry.get('name','?')} in {entry.get('ort','?')}...", end=" ")

        # Beschreibung generieren
        desc = generate_description(
            entry.get("name", ""),
            entry.get("ort", ""),
            entry.get("typ", ""),
            entry.get("region", ""),
        )
        if desc and len(desc.strip("<>p/ ")) >= 10:
            entry["beschreibung"] = desc

        # Tags generieren (wenn keine existieren)
        if not entry.get("tags") or len(entry.get("tags", [])) < 2:
            entry["tags"] = generate_tags(entry.get("name", ""), entry.get("typ", ""), entry.get("region", ""))

        # Ausstattung ableiten
        if not entry.get("ausstattung"):
            entry["ausstattung"] = generate_amenities(entry)

        # tier auf basic lassen (wird später gesetzt)
        if not entry.get("tier"):
            entry["tier"] = "basic"

        # Schreiben
        json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        enriched += 1
        print(f"✅ Beschreibung={'✅' if entry.get('beschreibung') and len(entry['beschreibung']) > 10 else '❌'} Tags={'✅' if entry.get('tags') else '❌'}")

        # Rate Limit: 1 Request pro Sekunde
        time.sleep(1.1)

    return enriched


def create_batch_file(batch_num, start, count, entries):
    """Erstelle eine Batch-JSON-Datei für spätere Verarbeitung."""
    batch = entries[start:start+count]
    batch_data = []
    for idx, (slug, filepath, entry) in enumerate(batch):
        batch_data.append({
            "batch": batch_num,
            "batch_idx": idx,
            "slug": slug,
            "filepath": filepath,
            "name": entry.get("name", ""),
            "ort": entry.get("ort", ""),
            "typ": entry.get("typ", ""),
            "region": entry.get("region", ""),
            "hat_beschreibung": bool(entry.get("beschreibung") and len(entry.get("beschreibung","").strip()) >= 10),
        })

    batch_file = os.path.join(BATCH_DIR, f"batch_{batch_num:03d}.json")
    json.dump(batch_data, open(batch_file, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    return batch_file


def main():
    parser = argparse.ArgumentParser(description="Batch-Verarbeitung für Unterkunfts-Beschreibungen")
    parser.add_argument("--start", type=int, default=0, help="Start-Index")
    parser.add_argument("--count", type=int, default=6, help="Anzahl Einträge")
    parser.add_argument("--batch-num", type=int, help="Batch-Nummer (erstellt Batch-Datei)")
    parser.add_argument("--create-batches", action="store_true", help="Alle Batch-Dateien erstellen (6er-Gruppen)")
    parser.add_argument("--file", help="Batch-JSON-Datei verarbeiten")
    parser.add_argument("--list-pending", action="store_true", help="Zeige Anzahl unbearbeiteter Einträge")
    args = parser.parse_args()

    all_entries = load_all_entries()

    if args.list_pending:
        pending = sum(1 for _, _, e in all_entries if needs_enrichment(e))
        print(f"Gesamt: {len(all_entries)} Unterkünfte")
        print(f"Benötigen Beschreibung: {pending}")
        print(f"Batches à 6: {(pending + 5) // 6}")
        return

    if args.create_batches:
        batch_size = 6
        pending = [(s, f, e) for s, f, e in all_entries if needs_enrichment(e)]
        total_batches = (len(pending) + batch_size - 1) // batch_size
        print(f"Erstelle {total_batches} Batch-Dateien für {len(pending)} Einträge...")
        for b in range(total_batches):
            start = b * batch_size
            bf = create_batch_file(b + 1, start, batch_size, pending)
            print(f"  Batch {b+1:03d}/{total_batches}: {bf}")
        print(f"\nFertig! {total_batches} Batches in {BATCH_DIR}/")
        return

    if args.file:
        # Verarbeite eine Batch-Datei
        batch_data = json.load(open(args.file, encoding="utf-8"))
        print(f"Verarbeite {args.file}: {len(batch_data)} Einträge")
        enriched = 0
        for item in batch_data:
            if item["hat_beschreibung"]:
                print(f"  {item['name']}: bereits vorhanden ✅")
                continue
            filepath = item["filepath"]
            if not os.path.exists(filepath):
                print(f"  {item['name']}: Datei nicht gefunden ❌")
                continue
            entry = json.load(open(filepath, encoding="utf-8"))
            print(f"  {item['name']} in {item['ort']}...", end=" ")
            desc = generate_description(item["name"], item["ort"], item["typ"], item["region"])
            if desc and len(desc.strip("<>p/ ")) >= 10:
                entry["beschreibung"] = desc
            if not entry.get("tags") or len(entry.get("tags", [])) < 2:
                entry["tags"] = generate_tags(item["name"], item["typ"], item["region"])
            if not entry.get("ausstattung"):
                entry["ausstattung"] = generate_amenities(entry)
            if not entry.get("tier"):
                entry["tier"] = "basic"
            json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            enriched += 1
            print(f"✅")
            time.sleep(1.1)
        print(f"\n✅ {enriched} Einträge angereichert")
        return

    # Direkte Index-Verarbeitung
    print(f"Verarbeite Einträge {args.start} bis {args.start+args.count-1}...")
    enriched = process_batch(all_entries, args.start, args.count)
    print(f"\n✅ {enriched} Einträge angereichert")


if __name__ == "__main__":
    main()
