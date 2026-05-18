#!/usr/bin/env python3
"""
B16: Beschreibungen auf MINDESTENS 5 Sätze regenerieren (Batches 41-48)
via deepseek-v4-flash.

Aufruf:
  python scripts/b16_run_batch.py <batch_num>
  python scripts/b16_run_batch.py all   # alle 8 Batches
"""
import json, os, sys, time, glob, re, urllib.request

# --- API Setup (kopiert aus enrich_batch.py) ---
for env_file_candidate in [
    "E:/HermesPortable/home/.env",
    os.path.expanduser(r"~\.hermes\.env"),
    os.path.join(os.environ.get("HERMES_HOME", ""), ".env"),
    os.path.join(os.path.dirname(os.environ.get("HERMES_HOME", "")), ".env"),
]:
    if env_file_candidate and os.path.exists(env_file_candidate):
        with open(env_file_candidate) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ[k] = v
        if os.environ.get("OPENCODE_GO_API_KEY"):
            break

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
if not API_KEY:
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

PROJECT_DIR = "F:/tiroltourismus"
BATCH_DIR = os.path.join(PROJECT_DIR, "scripts", "batches", "b16")


def count_german_sentences(text):
    """Zähle Sätze im deutschen Text (einfache Heuristik)."""
    # Clean HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Split on sentence endings
    sentences = [s.strip() for s in re.split(r'[.!?]+', clean) if s.strip()]
    return len(sentences)


def generate_description_5plus(name, ort, typ, region):
    """Generiere 5-8 Sätze HTML via deepseek-v4-flash."""
    typ_label = {"hotel": "Hotel", "gasthof": "Gasthof", "ferienwohnung": "Ferienwohnung",
                 "ferienhaus": "Ferienhaus", "jugendherberge": "Jugendherberge",
                 "camping": "Campingplatz", "bauernhof": "Bauernhof"}.get(typ, typ)

    prompt = (
        f"Beschreibe '{name}' in {ort}, Tirol, Österreich. "
        f"Art der Unterkunft: {typ_label}. "
        f"Schreibe MINDESTENS 5 SÄTZE, maximal 8 Sätze. "
        f"Gehe auf folgende Aspekte ein: Lage und Umgebung, "
        f"Ausstattung und Zimmermerkmale, kulinarisches Angebot (falls vorhanden), "
        f"Freizeitmöglichkeiten in der Nähe, und die besondere Atmosphäre des Hauses. "
        f"Sachlich, informativ, kein Marketington. "
        f"Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"
    )

    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "Du schreibst sachliche, informative Beschreibungen für ein Tirol-Tourismusportal. DEUTSCH. Mindestens 5 Sätze, maximal 8 Sätze. Verwende HTML-Paragraphen mit <strong>-Hervorhebungen. Antworte direkt mit dem HTML, ohne nachzudenken oder deine Ausgabe zu kommentieren."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096,
        "temperature": 0.4,
    }

    text = ""
    if HAS_REQUESTS:
        text = _generate_via_requests(body)
    else:
        text = _generate_via_urllib(body)

    # Validate sentence count
    sentences = count_german_sentences(text)
    if sentences < 5:
        print(f"    ⚠️ Nur {sentences} Sätze, versuche erneut mit strengerem Prompt...", flush=True)
        body["messages"][1]["content"] = prompt.replace(
            "MINDESTENS 5 SÄTZE, maximal 8 Sätze.",
            "MINDESTENS 5 SÄTZE, maximal 8 Sätze. Ich wiederhole: MINDESTENS FÜNF VOLLSTÄNDIGE SÄTZE."
        )
        body["temperature"] = 0.5
        time.sleep(2)
        if HAS_REQUESTS:
            text = _generate_via_requests(body)
        else:
            text = _generate_via_urllib(body)

        sentences = count_german_sentences(text)
        if sentences < 5:
            print(f"    ⚠️ Auch nach Retry nur {sentences} Sätze. Akzeptiere trotzdem.", flush=True)

    return text


def _generate_via_requests(body):
    import requests as req_lib
    try:
        resp = req_lib.post(
            API_URL,
            json=body,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            timeout=180,
        )
        if resp.status_code != 200:
            raise ValueError(f"HTTP {resp.status_code}: {resp.text[:300]}")
        result = resp.json()
        text = result["choices"][0]["message"]["content"].strip()
        if not text:
            raise ValueError("Empty content from API")
        if not text.startswith("<"):
            text = f"<p>{text}</p>"
        return text
    except Exception as e:
        print(f"    ⚠️ API-Fehler (requests): {e}", flush=True)
        try:
            time.sleep(3)
            resp = req_lib.post(
                API_URL,
                json=body,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
                timeout=180,
            )
            if resp.status_code != 200:
                raise ValueError(f"HTTP {resp.status_code}: {resp.text[:300]}")
            result = resp.json()
            text = result["choices"][0]["message"]["content"].strip()
            if not text:
                raise ValueError("Empty content on retry")
            if not text.startswith("<"):
                text = f"<p>{text}</p>"
            return text
        except Exception as e2:
            print(f"    ⚠️ Retry auch fehlgeschlagen: {e2}", flush=True)
            return ""


def _generate_via_urllib(body):
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=180)
        result = json.loads(resp.read())
        text = result["choices"][0]["message"]["content"].strip()
        if not text:
            raise ValueError("Empty content from API")
        if not text.startswith("<"):
            text = f"<p>{text}</p>"
        return text
    except Exception as e:
        print(f"    ⚠️ API-Fehler (urllib): {e}", flush=True)
        try:
            time.sleep(3)
            resp = urllib.request.urlopen(req, timeout=180)
            result = json.loads(resp.read())
            text = result["choices"][0]["message"]["content"].strip()
            if not text:
                raise ValueError("Empty content on retry")
            if not text.startswith("<"):
                text = f"<p>{text}</p>"
            return text
        except Exception as e2:
            print(f"    ⚠️ Retry auch fehlgeschlagen: {e2}", flush=True)
            return ""


def process_batch(batch_num, dry_run=False):
    """Verarbeite einen einzelnen Batch."""
    batch_file = os.path.join(BATCH_DIR, f"batch_{batch_num:03d}.json")
    if not os.path.exists(batch_file):
        print(f"❌ Batch-Datei nicht gefunden: {batch_file}")
        return 0, 0

    batch_data = json.load(open(batch_file, encoding="utf-8"))
    total = len(batch_data)
    enriched = 0
    skipped = 0
    errors = 0

    print(f"\n{'='*60}")
    print(f"  Batch {batch_num:03d}: {total} Einträge")
    print(f"  Modell: deepseek-v4-flash")
    print(f"{'='*60}")

    for idx, item in enumerate(batch_data):
        name = item["name"]
        ort = item.get("ort", "")
        typ = item.get("typ", "")
        filepath = item["filepath"]
        old_saetze = item.get("aktuelle_saetze", 0)

        print(f"\n  [{idx+1}/{total}] {name}", end="")
        if ort:
            print(f" in {ort}", end="")
        print(f" (bisher: {old_saetze} Sätze, Typ: {typ})", flush=True)

        if not os.path.exists(filepath):
            print(f"    ❌ Datei nicht gefunden: {filepath}")
            errors += 1
            continue

        if dry_run:
            print(f"    → würde Beschreibung generieren (DRY RUN)")
            skipped += 1
            continue

        # Lese aktuellen Eintrag
        entry = json.load(open(filepath, encoding="utf-8"))

        # Generiere neue Beschreibung
        print(f"    → Generiere Beschreibung...", flush=True)
        desc = generate_description_5plus(name, ort, typ, item.get("region", ""))

        if desc:
            saetze = count_german_sentences(desc)
            print(f"    → {saetze} Sätze generiert", flush=True)
            entry["beschreibung"] = desc
        else:
            print(f"    ❌ Keine Beschreibung generiert (behalte alte)", flush=True)
            errors += 1
            continue

        # Tags setzen falls nötig
        if not entry.get("tags") or len(entry.get("tags", [])) < 2:
            entry["tags"] = _generate_tags(name, typ, item.get("region", ""))

        # Ausstattung setzen falls nötig
        if not entry.get("ausstattung"):
            entry["ausstattung"] = _generate_amenities(entry)

        if not entry.get("tier"):
            entry["tier"] = "basic"

        # Schreiben
        json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        enriched += 1
        print(f"    ✅ Geschrieben ({len(desc)} Zeichen, {saetze} Sätze)", flush=True)

        # Rate Limit
        time.sleep(1.1)

    print(f"\n  Batch {batch_num:03d} Ergebnis: {enriched} angereichert, {skipped} übersprungen, {errors} Fehler")
    return enriched, errors


def _generate_tags(name, typ, region):
    tags = set()
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


def _generate_amenities(entry):
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


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="B16: Beschreibungen auf 5+ Sätze regenerieren")
    parser.add_argument("batches", nargs="+", help="Batch-Nummern (z.B. 41 42 43) oder 'all' für 41-48")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nicht schreiben")
    parser.add_argument("--start-at", type=int, default=0, help="Eintrag-Startindex innerhalb des Batches")

    args = parser.parse_args()

    if "all" in args.batches:
        batch_nums = list(range(41, 49))
    else:
        batch_nums = [int(b) for b in args.batches]

    total_enriched = 0
    total_errors = 0

    for bn in batch_nums:
        enriched, errors = process_batch(bn, dry_run=args.dry_run)
        total_enriched += enriched
        total_errors += errors

    print(f"\n{'='*60}")
    print(f"  FERTIG: {len(batch_nums)} Batches verarbeitet")
    print(f"  Angereichert: {total_enriched}")
    print(f"  Fehler: {total_errors}")
    print(f"{'='*60}")
