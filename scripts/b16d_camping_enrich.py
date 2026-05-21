#!/usr/bin/env python3
"""B16d: Camping 5+ Saetze — Regeneriere ALLE Camping-Beschreibungen auf mindestens 5 Sätze.

Verbesserte Version mit:
- stdout-Pufferung deaktiviert
- Progress-Journal für Resume-Fähigkeit
- Robusterer Fehlerbehandlung
"""

import json, os, sys, time, re, ssl, urllib.request

# Unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# ── Config ──
PROJECT_DIR = r"F:/tiroltourismus"
CAMPING_DIR = os.path.join(PROJECT_DIR, "src/data/camping")
API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
MODEL = "mimo-v2-pro"
RATE_LIMIT_SEC = 1.1
JOURNAL_FILE = os.path.join(os.path.dirname(__file__), "b16d_journal.json")

# ── API Key laden ──
API_KEY = ""
for env_path in [
    "E:/HermesPortable/home/.env",
    os.path.expanduser("~/.hermes/.env"),
    os.path.join(os.environ.get("HERMES_HOME", ""), ".env"),
]:
    if env_path and os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("OPENCODE_GO_API_KEY="):
                    API_KEY = line.split("=", 1)[1].strip()
                    break
        if API_KEY:
            break

if not API_KEY:
    print("FEHLER: Kein OPENCODE_GO_API_KEY gefunden.", flush=True)
    sys.exit(1)

print(f"🔑 API-Key geladen: ***{API_KEY[-4:]}", flush=True)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def count_sentences(text):
    if not text:
        return 0
    clean = re.sub(r"<[^>]+>", "", text)
    sentences = [s.strip() for s in re.split(r"[.!?]+", clean) if s.strip()]
    return len(sentences)


def clean_content(content):
    if not content:
        return ""
    content = content.strip()
    lower = content.lower()
    # Remove thinking block
    for tag in ["response</think>", "</think>"]:
        if tag in lower:
            idx = lower.index(tag) + len(tag)
            content = content[idx:].strip()
            lower = content.lower()
    # Remove non-HTML prefix
    if "<" in content:
        content = content[content.index("<"):]
    if not content.startswith("<"):
        content = f"<p>{content}</p>"
    return content


def generate_description(name, ort):
    ort_str = f" in {ort}" if ort else ""
    prompt = (
        f"Schreibe eine sachliche, informative Beschreibung des Campingplatzes '{name}'{ort_str}, Tirol, Österreich. "
        f"Art: Campingplatz. "
        f"MINDESTENS 5 Sätze, maximal 8 Sätze. "
        f"Beschreibe die Lage, die Atmosphäre, die Umgebung (Berge, Natur, Skigebiete, Wanderwege), "
        f"die Ausstattung und was Gäste erwartet. "
        f"Sachlich, faktenbasiert, kein Marketington, keine Superlative. "
        f"Format: <p>Text mit <strong>Hervorhebungen</strong> wichtiger Begriffe.</p> "
        f"Keine Überschrift, nur der Paragraph."
    )

    body = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Du schreibst sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch. "
                           "Mindestens 5 Sätze, maximal 8 Sätze. "
                           "Format: <p>HTML mit <strong>Hervorhebungen</strong>.</p> "
                           "Antworte direkt mit dem HTML-Paragraph, ohne zusätzliche Kommentare.",
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4096,
        "temperature": 0.4,
    }

    for attempt in range(3):
        try:
            if HAS_REQUESTS:
                resp = requests.post(
                    API_URL, json=body,
                    headers={"Authorization": f"Bearer {API_KEY}", "User-Agent": "curl/8.0.0"},
                    timeout=120,
                )
                if resp.status_code != 200:
                    raise ValueError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                content = resp.json()["choices"][0]["message"]["content"]
            else:
                data = json.dumps(body).encode()
                req = urllib.request.Request(
                    API_URL, data=data,
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}",
                             "User-Agent": "curl/8.0.0"},
                    method="POST",
                )
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
                    content = json.loads(resp.read())["choices"][0]["message"]["content"]

            result = clean_content(content)
            if result:
                return result
        except Exception as e:
            if attempt < 2:
                print(f"    ⚠️ Versuch {attempt+1} fehlgeschlagen: {e}", flush=True)
                time.sleep(3)
            else:
                print(f"    ❌ Alle 3 Versuche fehlgeschlagen: {e}", flush=True)
    return ""


def main():
    print("=" * 60, flush=True)
    print("🔨 B16d: Camping-Beschreibungen auf ≥5 Sätze regenerieren", flush=True)
    print(f"   Modell: {MODEL}", flush=True)
    print("=" * 60, flush=True)

    # Journal laden (bereits verarbeitete Slugs)
    done_slugs = set()
    if os.path.exists(JOURNAL_FILE):
        try:
            with open(JOURNAL_FILE) as f:
                done_slugs = set(json.load(f))
            print(f"📝 Journal geladen: {len(done_slugs)} bereits verarbeitet", flush=True)
        except Exception:
            pass

    # Alle Camping-Einträge scannen
    all_slugs = sorted(os.listdir(CAMPING_DIR))
    print(f"📂 Camping-Einträge insgesamt: {len(all_slugs)}", flush=True)

    entries_to_process = []
    skipped_already_done = 0
    skipped_already_long = 0

    for slug in all_slugs:
        idx_path = os.path.join(CAMPING_DIR, slug, "index.json")
        if not os.path.isfile(idx_path):
            continue
        try:
            with open(idx_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        name = data.get("name", slug)
        ort = data.get("ort", "")
        desc = data.get("beschreibung", "")
        n = count_sentences(desc)

        if slug in done_slugs:
            skipped_already_done += 1
            continue
        if n >= 5:
            skipped_already_long += 1
            continue

        entries_to_process.append((slug, idx_path, name, ort, n))

    print(f"   Bereits ≥5 Sätze:      {skipped_already_long}", flush=True)
    print(f"   Bereits im Journal:    {skipped_already_done}", flush=True)
    print(f"   Noch zu verarbeiten:   {len(entries_to_process)}", flush=True)
    print(flush=True)

    if not entries_to_process:
        print("✅ Alle Camping-Einträge haben bereits ≥5 Sätze.", flush=True)
        return

    print(f"{'='*60}", flush=True)
    print(f"🔄 Verarbeite {len(entries_to_process)} Einträge...", flush=True)
    print(f"{'='*60}", flush=True)

    enriched = 0
    errors = 0

    for i, (slug, idx_path, name, ort, old_n) in enumerate(entries_to_process, 1):
        print(f"  [{i}/{len(entries_to_process)}] {name} ({ort or 'o.A.'}) — aktuell {old_n} Sätze...", end=" ", flush=True)

        desc = generate_description(name, ort)

        if desc:
            new_n = count_sentences(desc)
            try:
                with open(idx_path, encoding="utf-8") as f:
                    entry = json.load(f)
                entry["beschreibung"] = desc
                with open(idx_path, "w", encoding="utf-8") as f:
                    json.dump(entry, f, indent=2, ensure_ascii=False)

                status = "✅" if new_n >= 5 else "⚠️"
                print(f"{status} {new_n} Sätze (vorher: {old_n})", flush=True)
                enriched += 1
            except Exception as e:
                print(f"❌ Schreibfehler: {e}", flush=True)
                errors += 1
        else:
            print("❌ Keine Beschreibung generiert", flush=True)
            errors += 1

        # Journal aktualisieren (auch bei Fehlern, damit wir nicht immer wieder dieselben probieren)
        done_slugs.add(slug)
        try:
            with open(JOURNAL_FILE, "w") as f:
                json.dump(sorted(done_slugs), f)
        except Exception:
            pass

        # Rate-Limit
        if i < len(entries_to_process):
            time.sleep(RATE_LIMIT_SEC)

    print(f"\n{'='*60}", flush=True)
    print(f"📊 Zusammenfassung:", flush=True)
    print(f"   ✅ Neu generiert:         {enriched}", flush=True)
    print(f"   ⏭️  Bereits ≥5 Sätze:     {skipped_already_long + skipped_already_done}", flush=True)
    print(f"   ❌ Fehler:                {errors}", flush=True)
    print(f"{'='*60}", flush=True)


if __name__ == "__main__":
    main()
