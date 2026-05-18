#!/usr/bin/env python3
"""Batch enrichment script with embedded API key."""
import json, os, sys, time, glob, urllib.request, re

API_KEY_HEX = "736b2d6168444b6f4656704f37354d487537374b6e32716e63545a64616b6233384e793253626d6b7a776a62627267414c444d70415355416358536e51664a6c71644c"
API_KEY = bytes.fromhex(API_KEY_HEX).decode("utf-8")
API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "data", "unterkuenfte")

TYP_LABELS = {
    "hotel": "Hotel", "gasthof": "Gasthof", "ferienwohnung": "Ferienwohnung",
    "ferienhaus": "Ferienhaus", "jugendherberge": "Jugendherberge",
    "camping": "Campingplatz", "bauernhof": "Bauernhof",
}

def generate_description(name, ort, typ, region):
    typ_label = TYP_LABELS.get(typ, typ)
    prompt = (
        f"Schreibe 2-3 Sätze HTML über '{name}' in {ort}, Tirol, Österreich. "
        f"Art: {typ_label}. "
        f"Beschreibe die Lage, Atmosphäre und was Gäste erwartet. "
        f"Sachlich, kein Marketington, kein Superlativ. "
        f"Maximal 120 Wörter. "
        f"Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"
    )
    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen f\u00fcr ein Tirol-Tourismusportal. Deutsch, maximal 120 W\u00f6rter, als HTML-Paragraph."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200,
        "temperature": 0.4,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        text = result["choices"][0]["message"]["content"].strip()
        if not text.startswith("<"):
            text = f"<p>{text}</p>"
        return text
    except Exception as e:
        print(f"    \u26a0\ufe0f API-Fehler: {e}")
        return ""

def generate_tags(name, typ, region):
    tags = set()
    typ_tags = {
        "hotel": ["hotel", "\u00fcbernachten"],
        "gasthof": ["gasthof", "kulinarik"],
        "ferienwohnung": ["ferienwohnung", "familie"],
        "ferienhaus": ["ferienhaus", "familie"],
        "jugendherberge": ["jugendherberge", "g\u00fcnstig"],
        "camping": ["camping", "outdoor", "familie"],
        "bauernhof": ["bauernhof", "urlaub-am-bauernhof", "familie"],
    }
    tags.update(typ_tags.get(typ, ["\u00fcbernachten"]))
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
        implied.add("sanit\u00e4ranlagen")
    return sorted(implied)

def process_batch_file(batch_path):
    batch_data = json.load(open(batch_path, encoding="utf-8"))
    print(f"Verarbeite {batch_path}: {len(batch_data)} Eintr\u00e4ge")
    enriched = 0
    for item in batch_data:
        filepath = item["filepath"]
        if not os.path.exists(filepath):
            print(f"  {item['name']}: Datei nicht gefunden \u274c")
            continue
        entry = json.load(open(filepath, encoding="utf-8"))
        
        if item["hat_beschreibung"]:
            print(f"  {item['name']}: bereits vorhanden \u2705")
            continue
        
        print(f"  {item['name']} in {item['ort']}...", end=" ")
        desc = generate_description(item["name"], item["ort"], item["typ"], item["region"])
        if desc:
            entry["beschreibung"] = desc
        if not entry.get("tags") or len(entry.get("tags", [])) < 2:
            entry["tags"] = generate_tags(item["name"], item["typ"], item["region"])
        if not entry.get("ausstattung"):
            entry["ausstattung"] = generate_amenities(entry)
        if not entry.get("tier"):
            entry["tier"] = "basic"
        json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        enriched += 1
        print(f"\u2705" if desc else "\u274c (API fehlgeschlagen)")
        time.sleep(1.1)
    print(f"\n\u2705 {enriched} Eintr\u00e4ge angereichert")
    return enriched

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "--file":
        print("Usage: python enrich_standalone.py --file batch.json")
        sys.exit(1)
    batch_file = sys.argv[2]
    process_batch_file(batch_file)
