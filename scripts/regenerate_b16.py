#!/usr/bin/env python3
"""
regenerate_b16.py — Beschreibungen auf 5+ Sätze regenerieren (Batch 9-16)

Liest Batch-Dateien aus scripts/batches/b16/, generiert neue Beschreibungen mit
5-8 Sätzen via deepseek-v4-flash, schreibt in index.json zurück.
Rate-Limit: 1s zwischen Requests.
"""
import json, os, sys, time, ssl, urllib.request

# API config
API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
API_KEY = ""

# Lade API-Key aus .env
env_path = "E:/HermesPortable/home/.env"
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("OPENCODE_GO_API_KEY="):
                API_KEY = line.split("=", 1)[1].strip()
                break

if not API_KEY:
    print("FEHLER: OPENCODE_GO_API_KEY nicht gefunden")
    sys.exit(1)

BATCH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batches", "b16")
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TYP_LABELS = {
    "hotel": "Hotel",
    "gasthof": "Gasthof",
    "ferienwohnung": "Ferienwohnung",
    "ferienhaus": "Ferienhaus",
    "jugendherberge": "Jugendherberge",
    "camping": "Campingplatz",
    "bauernhof": "Bauernhof",
}


def count_sentences(text):
    """Count sentences in HTML description."""
    if not text:
        return 0
    plain = text.replace("</p>", "").replace("<p>", "")
    plain = plain.replace("<strong>", "").replace("</strong>", "")
    plain = plain.replace("<br>", ". ").replace("<br/>", ". ")
    sentences = [s.strip() for s in plain.replace("?", ".").replace("!", ".").split(".") if s.strip()]
    return len(sentences)


def generate_description(name, ort, typ):
    """Generiere eine Beschreibung mit 5-8 Sätzen via deepseek-v4-flash."""
    typ_label = TYP_LABELS.get(typ, typ)

    ort_teil = f" in {ort}" if ort else ""
    
    prompt = (
        f"Schreibe eine sachliche, informative Beschreibung von '{name}'"
        f"{ort_teil}, Tirol, Österreich. "
        f"Art der Unterkunft: {typ_label}. "
        f"MINDESTENS 5 SÄTZE, maximal 8 Sätze. "
        f"Die Beschreibung soll faktenbasiert und journalistisch-neutral sein. "
        f"Beschreibe die Lage, die Umgebung, die Ausstattung, die Atmosphäre "
        f"und welche Art von Gästen sich hier wohlfühlt. "
        f"Kein Marketington, keine Superlative, keine Übertreibungen. "
        f"Keine generischen Floskeln. "
        f"Wichtige Wörter mit <strong> hervorheben. "
        f"Antworte NUR mit einem einzigen <p>Paragraph mit 5-8 Sätzen.</p>"
    )

    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Du bist ein Tirol-Tourismusredakteur. Du schreibst sachliche, "
                    "detailreiche Beschreibungen für Unterkünfte. "
                    "Jede Beschreibung hat MINDESTENS 5 SÄTZE, maximal 8. "
                    "Du antwortest ausschließlich mit einem einzigen HTML-Paragraph "
                    "(<p>...</p>) ohne einleitende Worte. "
                    "Du verwendest <strong> für Hervorhebungen. "
                    "Du verzichtest auf Übertreibungen und Marketing-Jargon."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 8192,
        "temperature": 0.3,
    }

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

    def _call_api():
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        resp = urllib.request.urlopen(req, timeout=180, context=ctx)
        result = json.loads(resp.read())
        choice = result["choices"][0]
        msg = choice.get("message", {})
        text = (msg.get("content") or "").strip()
        finish_reason = choice.get("finish_reason", "unknown")
        return text, finish_reason

    for attempt in range(2):
        try:
            text, finish_reason = _call_api()
            
            if not text:
                print(f"[finish_reason={finish_reason}, leer]", end=" ")
                if attempt == 0:
                    time.sleep(3)
                    continue
                return "", 0

            # Clean up markdown code fences
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(l for l in lines if not l.startswith("```"))
            text = text.strip()

            # Wrap in <p> if not already HTML
            if not text.startswith("<"):
                text = f"<p>{text}</p>"

            # Ensure closing tag
            if not text.endswith("</p>"):
                text += "</p>"

            sent_count = count_sentences(text)
            print(f"[{finish_reason}, {sent_count}S]", end=" ")
            return text, sent_count

        except Exception as e:
            print(f"[Fehler: {e}]", end=" ")
            if attempt == 0:
                time.sleep(3)
                continue
            return "", 0

    return "", 0


def build_tags(name, typ):
    """Build sensible tags for an accommodation."""
    tags = set()

    typ_tags = {
        "hotel": ["hotel", "übernachten", "komfort"],
        "gasthof": ["gasthof", "kulinarik", "tradition"],
        "ferienwohnung": ["ferienwohnung", "familie", "urlaub"],
        "ferienhaus": ["ferienhaus", "familie", "urlaub"],
        "jugendherberge": ["jugendherberge", "günstig"],
        "camping": ["camping", "outdoor", "familie"],
        "bauernhof": ["bauernhof", "urlaub-am-bauernhof", "familie"],
    }
    tags.update(typ_tags.get(typ, ["übernachten"]))

    kw_map = {
        "wellness": ["wellness", "entspannung"],
        "spa": ["wellness", "entspannung"],
        "sauna": ["wellness", "sauna"],
        "berg": ["berg", "wandern"],
        "alm": ["alm", "natur"],
        "ski": ["ski", "winter"],
        "sport": ["sport", "aktiv"],
        "see": ["see", "wasser"],
        "familie": ["familie", "kinder"],
        "design": ["design", "modern"],
        "schloss": ["schloss", "historisch"],
        "luxus": ["luxus", "premium"],
        "bio": ["bio", "nachhaltig"],
    }
    name_lower = name.lower()
    for kw, taglist in kw_map.items():
        if kw in name_lower:
            tags.update(taglist)

    return sorted(tags)[:6]


def process_batch(batch_file):
    """Process a single batch file, generating descriptions."""
    print(f"\n{'='*60}")
    print(f"📋 Verarbeite: {os.path.basename(batch_file)}")
    print(f"{'='*60}")

    with open(batch_file, encoding="utf-8") as f:
        items = json.load(f)

    enriched = 0
    skipped = 0
    failed = 0

    for idx, item in enumerate(items):
        filepath = item["filepath"]
        name = item["name"]
        ort = item["ort"] or ""
        typ = item["typ"]
        slug = item["slug"]

        # Nur verarbeiten wenn aktuell < 5 Sätze
        entry = json.load(open(filepath, encoding="utf-8"))
        current_sents = count_sentences(entry.get("beschreibung", ""))
        
        if current_sents >= 5:
            print(f"  [{idx+1}/{len(items)}] ✅ {name} — {current_sents} Sätze (übersprungen)")
            skipped += 1
            continue

        print(f"  [{idx+1}/{len(items)}] {name}{' (' + ort + ')' if ort else ''} — {current_sents} Sätze → ", end="")
        sys.stdout.flush()

        desc, sent_count = generate_description(name, ort, typ)

        if desc and sent_count >= 5:
            entry["beschreibung"] = desc
            entry["tags"] = build_tags(name, typ)
            json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            print(f"✅ {sent_count} Sätze")
            enriched += 1
        elif desc and sent_count >= 3:
            entry["beschreibung"] = desc
            entry["tags"] = build_tags(name, typ)
            json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            print(f"⚠️ nur {sent_count} Sätze (trotzdem geschrieben)")
            enriched += 1
        else:
            print(f"❌ Fehlgeschlagen ({sent_count} Sätze)")
            failed += 1

        time.sleep(1.0)

    return enriched, skipped, failed


def main():
    print("=" * 60)
    print("  B16c: Beschreibungen auf 5+ Sätze regenerieren (Batch 9-16)")
    print("=" * 60)

    total_enriched = 0
    total_skipped = 0
    total_failed = 0

    for batch_num in range(9, 17):
        batch_file = os.path.join(BATCH_DIR, f"batch_{batch_num:03d}.json")

        if not os.path.exists(batch_file):
            print(f"\n⚠️ Batch-Datei nicht gefunden: {batch_file}")
            continue

        e, s, f = process_batch(batch_file)
        total_enriched += e
        total_skipped += s
        total_failed += f

    print(f"\n{'='*60}")
    print(f"  ✅ Fertig!")
    print(f"     Erfolgreich: {total_enriched}")
    print(f"     Übersprungen: {total_skipped}")
    print(f"     Fehlgeschlagen: {total_failed}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
