#!/usr/bin/env python3
"""
process_batch_entries.py — Verarbeitet NUR die Einträge aus Batches 191-200.
"""
import json, os, sys, time, glob
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "src", "data", "unterkuenfte")
BATCH_DIR = os.path.join(BASE_DIR, "scripts", "batches")
ENV_PATH = "E:/HermesPortable/home/.env"
API_URL = "https://opencode.ai/zen/go/v1"
MODEL = "deepseek-v4-flash"

TYP_LABELS = {
    "hotel": "Hotel", "gasthof": "Gasthof", "ferienwohnung": "Ferienwohnung",
    "ferienhaus": "Ferienhaus", "jugendherberge": "Jugendherberge",
    "camping": "Campingplatz", "bauernhof": "Bauernhof"
}

def load_api_key():
    with open(ENV_PATH) as f:
        for line in f:
            if "OPENCODE_GO_API_KEY" in line:
                return line.split("=", 1)[1].strip()
    raise SystemExit("No API key found")

def generate_description(client, name, ort, typ):
    typ_label = TYP_LABELS.get(typ, typ)
    ort_str = f" in {ort}" if ort else " in Tirol"
    prompt = (
        f"Schreibe 2-3 Sätze HTML über '{name}'{ort_str}, Österreich. "
        f"Art: {typ_label}. Beschreibe die Lage, Atmosphäre und was Gäste erwartet. "
        f"Sachlich, kein Marketington, kein Superlativ. Maximal 120 Wörter. "
        f"Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"
    )
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen. Deutsch, max 120 Wörter. Antworte NUR mit dem HTML-Paragraph."},
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
        return ""

def main():
    # Alle Batch-Einträge sammeln
    batch_entries = []
    for i in range(191, 201):
        bf = os.path.join(BATCH_DIR, f"batch_{i}.json")
        if os.path.exists(bf):
            with open(bf, encoding="utf-8") as f:
                batch_entries.extend(json.load(f))
    
    print(f"Batches 191-200: {len(batch_entries)} Einträge")
    
    # Nur Einträge mit existierender Datei und fehlender Beschreibung
    key = load_api_key()
    client = OpenAI(base_url=API_URL, api_key=key)
    
    enriched = 0
    skipped = 0
    missing = 0
    failed = 0
    
    for idx, item in enumerate(batch_entries):
        filepath = item["filepath"]
        if not os.path.exists(filepath):
            print(f"  ❌ [{idx+1}] {item['name']}: Datei nicht gefunden")
            missing += 1
            continue
        
        with open(filepath, encoding="utf-8") as f:
            entry = json.load(f)
        
        if entry.get("beschreibung") and len(entry["beschreibung"].strip()) > 10:
            print(f"  ✅ [{idx+1}] {item['name']}: bereits beschrieben")
            skipped += 1
            continue
        
        print(f"  → [{idx+1}/{len(batch_entries)}] {item['name']} ({item.get('ort','?')})...", end=" ", flush=True)
        
        desc = generate_description(client, item["name"], item.get("ort", ""), item.get("typ", ""))
        
        if desc:
            entry["beschreibung"] = desc
            json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            enriched += 1
            print(f"✅ ({len(desc)} Z)")
        else:
            failed += 1
            print(f"❌")
        
        time.sleep(0.5)
    
    print(f"\n✅ {enriched} angereichert, {skipped} bereits vorhanden, {missing} fehlend, {failed} fehlgeschlagen")

if __name__ == "__main__":
    main()
