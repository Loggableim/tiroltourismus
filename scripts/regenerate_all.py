#!/usr/bin/env python3
"""
regenerate_all.py — Generiert fehlende Beschreibungen für ALLE Unterkünfte.

Liest alle index.json Dateien aus src/data/unterkuenfte/ und generiert
fehlende Beschreibungen via deepseek-v4-flash API.

Nutzung:
  python scripts/regenerate_all.py [--batch N]
"""
import json, os, sys, time, glob
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "src", "data", "unterkuenfte")
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
    raise SystemExit("OPENCODE_GO_API_KEY nicht gefunden")

def generate_description(client, name, ort, typ):
    typ_label = TYP_LABELS.get(typ, typ)
    ort_str = f" in {ort}" if ort else ""
    prompt = (
        f"Schreibe 2-3 Sätze HTML über '{name}'{ort_str}, Tirol, Österreich. "
        f"Art: {typ_label}. Beschreibe die Lage, Atmosphäre und was Gäste erwartet. "
        f"Sachlich, kein Marketington, kein Superlativ. Maximal 120 Wörter. "
        f"Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"
    )
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph. Antworte NUR mit dem HTML-Paragraph, ohne Einleitung."},
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
    # Lade alle index.json Einträge
    entries = []
    for fpath in sorted(glob.glob(os.path.join(DATA_DIR, "*", "index.json"))):
        slug = os.path.basename(os.path.dirname(fpath))
        try:
            entry = json.load(open(fpath, encoding="utf-8"))
            entries.append((slug, fpath, entry))
        except:
            pass

    print(f"Gefunden: {len(entries)} Unterkünfte")

    # Filtere Einträge, die eine Beschreibung brauchen
    pending = [(s, f, e) for s, f, e in entries 
               if not e.get("beschreibung") or len(e.get("beschreibung", "").strip()) < 10]
    
    print(f"Benötigen Beschreibung: {len(pending)}")
    
    if not pending:
        print("✅ Alle Einträge haben bereits Beschreibungen!")
        return

    # Batch-Modus: verarbeite nur einen Teil
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--batch" else 999

    if batch_size < 999:
        pending = pending[:batch_size]
        print(f"Verarbeite Batch: 0-{len(pending)}")

    # API-Client
    key = load_api_key()
    client = OpenAI(base_url=API_URL, api_key=key)

    enriched = 0
    failed = 0
    
    for idx, (slug, fpath, entry) in enumerate(pending):
        name = entry.get("name", slug)
        ort = entry.get("ort", "")
        typ = entry.get("typ", "")
        
        print(f"  [{idx+1}/{len(pending)}] {name} ({ort})...", end=" ", flush=True)
        
        desc = generate_description(client, name, ort, typ)
        
        if desc:
            entry["beschreibung"] = desc
            json.dump(entry, open(fpath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            enriched += 1
            print(f"✅ ({len(desc)} Z)")
        else:
            failed += 1
            print(f"❌")
        
        time.sleep(0.5)
    
    print(f"\n✅ {enriched} erstellt, {failed} fehlgeschlagen")

if __name__ == "__main__":
    main()
