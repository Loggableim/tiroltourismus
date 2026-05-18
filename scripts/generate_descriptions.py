#!/usr/bin/env python3
"""
generate_descriptions.py — Generiert Unterkunfts-Beschreibungen via OpenAI SDK.

Nutzung:
  python generate_descriptions.py --file scripts/batches/batch_N.json

Lädt den API-Key aus E:/HermesPortable/home/.env und generiert
HTML-Beschreibungen für Einträge, die noch keine haben.
"""
import json, os, sys, time
from openai import OpenAI

# Pfade
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BATCH_DIR = os.path.join(SCRIPT_DIR, "batches")
DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "src", "data", "unterkuenfte"))
ENV_PATH = "E:/HermesPortable/home/.env"
API_URL = "https://opencode.ai/zen/go/v1"
MODEL = "deepseek-v4-flash"

TYP_LABELS = {
    "hotel": "Hotel", "gasthof": "Gasthof", "ferienwohnung": "Ferienwohnung",
    "ferienhaus": "Ferienhaus", "jugendherberge": "Jugendherberge",
    "camping": "Campingplatz", "bauernhof": "Bauernhof"
}

def load_api_key():
    if not os.path.exists(ENV_PATH):
        print(f"❌ .env Datei nicht gefunden: {ENV_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line.startswith("OPENCODE_GO_API_KEY="):
                return line.split("=", 1)[1].strip()
    print("❌ OPENCODE_GO_API_KEY nicht in .env gefunden", file=sys.stderr)
    sys.exit(1)

def generate_description(client, name, ort, typ):
    """Generiere eine HTML-Beschreibung via API."""
    typ_label = TYP_LABELS.get(typ, typ)
    ort_str = f" in {ort}" if ort else " in Tirol"
    
    prompt = (
        f"Schreibe 2-3 Sätze HTML über '{name}'{ort_str}, Österreich. "
        f"Art: {typ_label}. "
        f"Beschreibe die Lage, Atmosphäre und was Gäste erwartet. "
        f"Sachlich, kein Marketington, kein Superlativ. "
        f"Maximal 120 Wörter. "
        f"Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"
    )
    
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph. Antworte NUR mit dem HTML-Paragraph, ohne Einleitung oder Erklärung."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=0.4,
        )
        text = (resp.choices[0].message.content or "").strip()
        if text and not text.startswith("<"):
            text = f"<p>{text}</p>"
        return text
    except Exception as e:
        print(f"    ⚠️ API-Fehler: {e}")
        return ""

def process_batch(batch_file):
    with open(batch_file, encoding="utf-8") as f:
        batch = json.load(f)
    
    print(f"Verarbeite {os.path.basename(batch_file)}: {len(batch)} Einträge")
    
    # API-Client initialisieren
    key = load_api_key()
    client = OpenAI(base_url=API_URL, api_key=key)
    
    enriched = 0
    skipped = 0
    missing = 0
    
    for idx, item in enumerate(batch):
        name = item["name"]
        ort = item.get("ort", "")
        filepath = item["filepath"]
        
        if not os.path.exists(filepath):
            print(f"  ❌ [{idx+1}] {name}: Datei nicht gefunden")
            missing += 1
            continue
        
        with open(filepath, encoding="utf-8") as f:
            entry = json.load(f)
        
        if entry.get("beschreibung") and len(entry["beschreibung"].strip()) > 20:
            print(f"  ✅ [{idx+1}] {name}: bereits beschrieben")
            skipped += 1
            continue
        
        print(f"  → [{idx+1}/{len(batch)}] {name} ({ort})...", end=" ", flush=True)
        
        desc = generate_description(client, name, ort, item.get("typ", ""))
        
        if desc:
            entry["beschreibung"] = desc
            json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            enriched += 1
            print(f"✅ ({len(desc)} Zeichen)")
        else:
            print(f"❌ (leer)")
        
        # Rate Limit
        time.sleep(1.0)
    
    print(f"\n✅ {enriched} angereichert, {skipped} übersprungen, {missing} fehlend")
    return enriched

def main():
    if len(sys.argv) != 3 or sys.argv[1] != "--file":
        print("Usage: python generate_descriptions.py --file scripts/batches/batch_N.json")
        sys.exit(1)
    
    batch_file = sys.argv[2]
    if not os.path.exists(batch_file):
        alt = os.path.join(BATCH_DIR, os.path.basename(batch_file))
        if os.path.exists(alt):
            batch_file = alt
        else:
            print(f"Datei nicht gefunden: {batch_file}")
            sys.exit(1)
    
    process_batch(batch_file)

if __name__ == "__main__":
    main()
