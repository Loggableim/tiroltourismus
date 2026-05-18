#!/usr/bin/env python3
"""
Fix: Re-process batches 25-27 which still have old short descriptions.
"""
import json, os, sys, time, re
import urllib.request, ssl

# Load .env
for env_file in [
    "E:/HermesPortable/home/.env",
    os.path.expanduser(r"~\\.hermes\\.env"),
    os.path.join(os.environ.get("HERMES_HOME", ""), ".env"),
]:
    if env_file and os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ[k] = v

API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
if not API_KEY:
    for _ep in [os.path.expanduser(r"~\\.hermes\\.env"), r"C:\Users\logga\.hermes\.env"]:
        if os.path.exists(_ep):
            with open(_ep) as f:
                for _l in f:
                    _l = _l.strip()
                    if _l.startswith("OPENCODE_GO_API_KEY="):
                        API_KEY = _l.split("=", 1)[1].strip()
                        break
            if API_KEY:
                break

BATCH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batches", "b16")

def count_sentences(html_text):
    plain = re.sub(r'<[^>]+>', '', html_text).strip()
    sentences = [s.strip() for s in re.split(r'[.!?]+', plain) if s.strip()]
    return len(sentences)

def generate_description(name, ort, typ, region):
    loc = ort if ort else (region if region else "Tirol")
    prompt = (
        f"Beschreibe '{name}' in {loc}, Tirol, Österreich. "
        f"Art der Unterkunft: {typ}. "
        f"MINDESTENS 5 Sätze, maximal 8 Sätze. "
        f"Sachlich, informativ, kein Marketington, keine Superlative. "
        f"Beschreibe die Lage, Atmosphäre, was Gäste erwartet, "
        f"die Umgebung und die Ausstattung. "
        f"Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"
    )

    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Du schreibst sachliche Beschreibungen für ein Tirol-Tourismusportal. "
                    "Deutsch, MINDESTENS 5 Sätze, maximal 8. "
                    "Antworte direkt mit dem HTML-Paragraph, ohne nachzudenken oder zu erklären. "
                    "Jeder Satz muss mit Punkt enden. Keine Aufzählungen."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4096,
        "temperature": 0.4,
    }

    try:
        # Use urllib directly (simpler)
        import requests
        resp = requests.post(
            "https://opencode.ai/zen/go/v1/chat/completions",
            json=body,
            headers={"Authorization": f"Bearer {API_KEY}", "User-Agent": "curl/8.0.0"},
            timeout=180,
        )
        if resp.status_code != 200:
            raise ValueError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        result = resp.json()
        text = result["choices"][0]["message"]["content"].strip()
        if not text:
            raise ValueError("Empty content")
        return text
    except Exception as e:
        print(f"    ⚠️ API-Fehler: {e}")
        time.sleep(3)
        try:
            resp = requests.post(
                "https://opencode.ai/zen/go/v1/chat/completions",
                json=body,
                headers={"Authorization": f"Bearer {API_KEY}", "User-Agent": "curl/8.0.0"},
                timeout=180,
            )
            if resp.status_code == 200:
                result = resp.json()
                text = result["choices"][0]["message"]["content"].strip()
                if text:
                    return text
        except:
            pass
        return ""

def process_batch(batch_file):
    print(f"\n{'='*60}")
    print(f"📋 Verarbeite: {os.path.basename(batch_file)}")
    print(f"{'='*60}")
    
    batch_data = json.load(open(batch_file, encoding="utf-8"))
    enriched = 0
    skipped = 0
    failed = 0
    
    for idx, item in enumerate(batch_data):
        filepath = item["filepath"]
        name = item.get("name", "?")
        ort = item.get("ort", "")
        typ = item.get("typ", "")
        slug = item.get("slug", "")
        aktuelle = item.get("aktuelle_saetze", 0)
        
        if not os.path.exists(filepath):
            print(f"  [{idx+1}/{len(batch_data)}] {name}: Datei nicht gefunden ❌")
            failed += 1
            continue
        
        entry = json.load(open(filepath, encoding="utf-8"))
        region = entry.get("region", "")
        loc_for_display = ort if ort else (region if region else "?")
        
        # Check current sentence count
        current_desc = entry.get("beschreibung", "")
        current_count = count_sentences(current_desc)
        if current_count >= 5:
            print(f"  [{idx+1}/{len(batch_data)}] {name}: bereits {current_count} Sätze ✅")
            skipped += 1
            continue
        
        print(f"  [{idx+1}/{len(batch_data)}] {name} (aktuell: {current_count} Sätze, Ort: {loc_for_display})...", end=" ", flush=True)
        
        desc = generate_description(name, ort or "", typ, region)
        if not desc:
            print("❌ Keine Beschreibung erhalten")
            failed += 1
            continue
        
        if not desc.startswith("<"):
            desc = f"<p>{desc}</p>"
        
        new_count = count_sentences(desc)
        entry["beschreibung"] = desc
        json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        enriched += 1
        
        if new_count < 5:
            print(f"⚠️ Nur {new_count} Sätze")
        else:
            print(f"✅ ({new_count} Sätze)")
        
        if idx < len(batch_data) - 1:
            time.sleep(1.1)
    
    print(f"\n  Ergebnis: {enriched} angereichert, {skipped} übersprungen, {failed} fehlgeschlagen")
    return enriched, skipped, failed

def main():
    batches = [25, 26, 27]
    total_e = total_s = total_f = 0
    
    print("=" * 60)
    print("B16c FIX: Nachbearbeitung Batch 25-27 (fehlgeschlagene Beschreibungen)")
    print("=" * 60)
    
    for b in batches:
        batch_file = os.path.join(BATCH_DIR, f"batch_{b:03d}.json")
        if not os.path.exists(batch_file):
            print(f"\n⚠️  Batch {b:03d} nicht gefunden: {batch_file}")
            continue
        e, s, f = process_batch(batch_file)
        total_e += e
        total_s += s
        total_f += f
    
    print(f"\n{'='*60}")
    print(f"FIX FERTIG: {total_e} neu geschrieben, {total_s} übersprungen (bereits OK), {total_f} fehlgeschlagen")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
