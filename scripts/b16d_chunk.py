#!/usr/bin/env python3
"""B16d chunk worker — verarbeitet eine Teilmenge der Camping-Einträge.

Aufruf: python scripts/b16d_chunk.py <start_index> <count>
Beispiel: python scripts/b16d_chunk.py 0 20   (erste 20 noch unzureichende Einträge)
"""

import json, os, sys, time, re, ssl, urllib.request

PROJECT_DIR = r"F:/tiroltourismus"
CAMPING_DIR = os.path.join(PROJECT_DIR, "src/data/camping")
API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
MODEL = "deepseek-v4-flash"
RATE_LIMIT_SEC = 1.1

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
    print("FEHLER: Kein OPENCODE_GO_API_KEY")
    sys.exit(1)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def count_sentences(text):
    if not text:
        return 0
    clean = re.sub(r"<[^>]+>", "", text)
    return len([s.strip() for s in re.split(r"[.!?]+", clean) if s.strip()])


def clean_content(content):
    if not content:
        return ""
    content = content.strip()
    lower = content.lower()
    if "</think>" in lower:
        idx = lower.index("</think>") + 8
        content = content[idx:].strip()
        lower = content.lower()
    if "<" in content:
        content = content[content.index("<"):]
    if not content.startswith("<"):
        content = f"<p>{content}</p>"
    return content


def generate_description(name, ort):
    ort_str = f" in {ort}" if ort else ""
    prompt = (
        f"Schreibe eine sachliche, informative Beschreibung des Campingplatzes '{name}'{ort_str}, Tirol, Österreich. "
        f"Art: Campingplatz. MINDESTENS 5 Sätze, maximal 8 Sätze. "
        f"Beschreibe die Lage, die Atmosphäre, die Umgebung (Berge, Natur, Skigebiete, Wanderwege), "
        f"die Ausstattung und was Gäste erwartet. "
        f"Sachlich, faktenbasiert, kein Marketington, keine Superlative. "
        f"Format: <p>Text mit <strong>Hervorhebungen</strong> wichtiger Begriffe.</p> Keine Überschrift."
    )

    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Du schreibst sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch. Mindestens 5 Sätze, maximal 8 Sätze. Format: <p>HTML mit <strong>Hervorhebungen</strong>.</p> Antworte direkt mit dem HTML-Paragraph."},
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
                    raise ValueError(f"HTTP {resp.status_code}")
                c = resp.json()["choices"][0]["message"]["content"]
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
                    c = json.loads(resp.read())["choices"][0]["message"]["content"]
            result = clean_content(c)
            if result:
                return result
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
            else:
                print(f"    ❌ Fehler: {e}")
    return ""


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    # Find entries that need work
    todo = []
    for slug in sorted(os.listdir(CAMPING_DIR)):
        path = os.path.join(CAMPING_DIR, slug, "index.json")
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        desc = data.get("beschreibung", "")
        n = count_sentences(desc)
        if n < 5:
            todo.append((slug, path, data.get("name", "?"), data.get("ort", ""), n))

    chunk = todo[start:start + count]
    total_in_chunk = len(chunk)
    
    if total_in_chunk == 0:
        print("✅ Nichts zu tun in diesem Chunk.")
        return

    print(f"📋 Chunk: Einträge {start}–{start+total_in_chunk-1} ({total_in_chunk} Stück)")
    enriched = 0
    errors = 0

    for i, (slug, path, name, ort, old_n) in enumerate(chunk):
        print(f"  [{start+i+1}/{len(todo)}] {name} ({ort or 'o.A.'}) — {old_n} Sätze...", end=" ", flush=True)
        desc = generate_description(name, ort)
        if desc:
            new_n = count_sentences(desc)
            with open(path, encoding="utf-8") as f:
                entry = json.load(f)
            entry["beschreibung"] = desc
            with open(path, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
            status = "✅" if new_n >= 5 else "⚠️"
            print(f"{status} {new_n} Sätze")
            enriched += 1
        else:
            print("❌ Fehlgeschlagen")
            errors += 1
        if i < total_in_chunk - 1:
            time.sleep(RATE_LIMIT_SEC)

    print(f"\nChunk-Ergebnis: {enriched} ✅, {errors} ❌ (/{total_in_chunk})")

if __name__ == "__main__":
    main()
