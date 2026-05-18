#!/usr/bin/env python3
"""Generate descriptions for a batch using hermes CLI."""
import json, os, sys, time, subprocess

def generate_description(name, ort, typ, region):
    """Generate a description using hermes CLI."""
    typ_label = {"hotel": "Hotel", "gasthof": "Gasthof", "ferienwohnung": "Ferienwohnung",
                 "ferienhaus": "Ferienhaus", "jugendherberge": "Jugendherberge",
                 "camping": "Campingplatz", "bauernhof": "Bauernhof"}.get(typ, typ)
    
    ort_str = f" in {ort}" if ort else ""
    
    prompt = (
        f"Schreibe 2-3 Sätze HTML über '{name}'{ort_str}, Tirol, Österreich. "
        f"Art: {typ_label}. "
        f"Beschreibe die Lage, Atmosphäre und was Gäste erwartet. "
        f"Sachlich, kein Marketington, kein Superlativ. "
        f"Maximal 120 Wörter. "
        f"Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"
    )
    
    # Try calling the model via hermes exec
    cmd = [
        "hermes", "exec", "-m", "deepseek-v4-flash",
        "--provider", "opencode-go",
        "--system", "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph.",
        prompt
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        print(f"    hermes exec return code: {result.returncode}")
        if result.returncode == 0:
            text = result.stdout.strip()
            if not text.startswith("<"):
                text = f"<p>{text}</p>"
            return text
        else:
            print(f"    stderr: {result.stderr[:200]}")
            return ""
    except Exception as e:
        print(f"    Error: {e}")
        return ""

if __name__ == "__main__":
    batch_file = sys.argv[1]
    batch_data = json.load(open(batch_file, encoding="utf-8"))
    print(f"Verarbeite {batch_file}: {len(batch_data)} Einträge")
    enriched = 0
    
    for item in batch_data:
        if item.get("hat_beschreibung"):
            print(f"  {item['name']}: bereits vorhanden ✅")
            continue
        
        filepath = item["filepath"]
        if not os.path.exists(filepath):
            print(f"  {item['name']}: Datei nicht gefunden ❌")
            continue
        
        entry = json.load(open(filepath, encoding="utf-8"))
        name, ort, typ, region = item["name"], item["ort"], item["typ"], item["region"]
        print(f"  {name} in {ort or '?'}...", end=" ", flush=True)
        
        desc = generate_description(name, ort, typ, region)
        if desc:
            entry["beschreibung"] = desc
            print(f"✅ Beschreibung")
        else:
            print(f"❌ Keine Beschreibung")
        
        # Tags
        if not entry.get("tags") or len(entry.get("tags", [])) < 2:
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
            entry["tags"] = sorted(tags)[:6]
        
        # Ausstattung
        if not entry.get("ausstattung"):
            entry["ausstattung"] = []
        
        if not entry.get("tier"):
            entry["tier"] = "basic"
        
        json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        enriched += 1
        time.sleep(0.5)
    
    print(f"\n✅ Batch done: {enriched} Einträge angereichert")
