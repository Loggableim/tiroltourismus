#!/usr/bin/env python3
"""Process the 2 remaining entries: Camping Resort Zugspitze and Camping Riffler."""
import json, os, ssl, urllib.request, time

# Load API key
API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
if not API_KEY:
    for env_file in [
        "E:/HermesPortable/home/.env",
        os.path.expanduser("~/.hermes/.env"),
    ]:
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        os.environ[k] = v
            if os.environ.get("OPENCODE_GO_API_KEY"):
                API_KEY = os.environ["OPENCODE_GO_API_KEY"]
                break

import requests

DATA_DIR = "F:/tiroltourismus/src/data/unterkuenfte"
API_URL = "https://opencode.ai/zen/go/v1/chat/completions"

entries_to_fix = [
    {
        "slug": "camping-resort-zugspitze",
        "name": "Camping Resort Zugspitze",
        "ort": "",
        "typ": "camping",
        "region": "",
    },
    {
        "slug": "camping-riffler",
        "name": "Camping Riffler",
        "ort": "Landeck",
        "typ": "camping",
        "region": "landeck",
    },
]

for item in entries_to_fix:
    filepath = os.path.join(DATA_DIR, item["slug"], "index.json")
    if not os.path.exists(filepath):
        print(f"{item['name']}: Datei nicht gefunden ❌")
        continue

    with open(filepath, "r", encoding="utf-8") as f:
        entry = json.load(f)

    print(f"\n{item['name']} in {item['ort'] or '(unbekannt)'}...")

    # Generate description
    typ_label = {"hotel": "Hotel", "gasthof": "Gasthof", "ferienwohnung": "Ferienwohnung",
                 "ferienhaus": "Ferienhaus", "jugendherberge": "Jugendherberge",
                 "camping": "Campingplatz", "bauernhof": "Bauernhof"}.get(item["typ"], item["typ"])

    prompt = (
        f"Schreibe 2-3 Sätze HTML über '{item['name']}' in Tirol, Österreich. "
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
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 2000,
        "temperature": 0.4,
    }

    # Try requests with retry
    desc = ""
    for attempt in range(2):
        try:
            resp = requests.post(
                API_URL,
                json=body,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "User-Agent": "curl/8.0.0",
                },
                timeout=120,
            )
            if resp.status_code != 200:
                print(f"  ⚠️ HTTP {resp.status_code}: {resp.text[:200]}")
                time.sleep(3)
                continue
            result = resp.json()
            text = result["choices"][0]["message"]["content"].strip()
            if not text:
                print("  ⚠️ Empty content from API")
                time.sleep(3)
                continue
            if not text.startswith("<"):
                text = f"<p>{text}</p>"
            desc = text
            break
        except Exception as e:
            print(f"  ⚠️ API-Fehler: {e}")
            time.sleep(3)

    if desc and len(desc.strip("<>p/ ")) >= 10:
        entry["beschreibung"] = desc
        print(f"  ✅ Beschreibung ({len(desc)} chars)")
    else:
        print(f"  ❌ Beschreibung fehlgeschlagen")

    # Generate tags
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
    tags.update(typ_tags.get(item["typ"], ["übernachten"]))
    entry["tags"] = sorted(tags)[:6]
    print(f"  ✅ Tags: {entry['tags']}")

    # Generate amenities
    amenities = set()
    name_lower = item["name"].lower()
    if item["typ"] == "camping":
        amenities.add("stromanschluss")
        amenities.add("sanitäranlagen")
    if "see" in name_lower:
        amenities.add("seenähe")
    entry["ausstattung"] = sorted(amenities)
    print(f"  ✅ Ausstattung: {entry['ausstattung']}")

    # tier
    if not entry.get("tier"):
        entry["tier"] = "basic"

    # Write
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)
    print(f"  ✅ Geschrieben nach {filepath}")
    time.sleep(1.1)

print("\n✅ Fertig! 2 Einträge verarbeitet.")
