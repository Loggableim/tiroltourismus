#!/usr/bin/env python3
"""
B16c: Final pass — process ALL entries in batches 1-8 that need ≥5 sentences.
"""
import json, os, sys, time, re, ssl, urllib.request, urllib.error

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
if not API_KEY:
    for env_file in ["E:/HermesPortable/home/.env"]:
        if os.path.exists(env_file):
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        os.environ[k] = v
            if os.environ.get("OPENCODE_GO_API_KEY"):
                break
    API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")

if not API_KEY:
    print("❌ No API key", flush=True)
    sys.exit(1)

API_URL = "https://opencode.ai/zen/go/v1/chat/completions"


def count_sentences(html_text):
    text = re.sub(r'<[^>]+>', '', html_text).strip()
    sentences = re.split(r'[.!?](?:\s+|$)', text)
    return len([s for s in sentences if s.strip()])


def generate(name, ort, typ_label, retries=5):
    prompt = (
        f"Schreibe eine Beschreibung über '{name}'"
        + (f" in {ort}, Tirol, Österreich" if ort else " in Tirol, Österreich")
        + f". Art: {typ_label}. "
        f"MINDESTENS 5 Sätze, maximal 8. Sachlich, informativ. "
        f"Beschreibe Lage, Umgebung, Ausstattung, Atmosphäre, Zielpublikum. "
        f"Format: <p>...</p>"
    )

    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "Du schreibst sachliche Beschreibungen für ein Tirol-Tourismusportal. MINDESTENS 5 Sätze, max 8. Deutsch. Ausgabe: <p>...</p>. Antwort direkt mit HTML."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4000,
        "temperature": 0.5,
    }

    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                API_URL, data=json.dumps(body).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}",
                    "User-Agent": "Mozilla/5.0",
                }, method="POST"
            )
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            resp = urllib.request.urlopen(req, timeout=120, context=ctx)
            result = json.loads(resp.read())
            content = (result["choices"][0]["message"].get("content") or "").strip()
            if not content:
                raise ValueError("Empty content")
            if content.startswith("```"):
                content = "\n".join(l for l in content.split("\n") if not l.startswith("```"))
            if not content.startswith("<"):
                content = f"<p>{content}</p>"
            s = count_sentences(content)
            if s >= 5:
                return content
            else:
                raise ValueError(f"Nur {s} Sätze")
        except Exception as e:
            if attempt < retries:
                print(f"    ⚠️ V{attempt}/{retries}: {e}", flush=True)
                time.sleep(attempt * 3)
            else:
                raise e


def main():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batches", "b16")
    total_needed = 0
    total_done = 0
    total_err = 0

    for bn in range(1, 9):
        bf = os.path.join(base, f"batch_{bn:03d}.json")
        batch = json.load(open(bf, encoding="utf-8"))
        for item in batch:
            fp = item["filepath"]
            name = item["name"]
            ort = item.get("ort", "")
            typ = item.get("typ", "")

            if not os.path.exists(fp):
                print(f"⚠️ {name}: file not found", flush=True)
                continue

            entry = json.load(open(fp, encoding="utf-8"))
            desc = entry.get("beschreibung", "")
            current = count_sentences(desc) if desc else 0

            if current >= 5:
                print(f"✅ {name}: already {current} Sätze", flush=True)
                total_done += 1
                continue

            typ_label = {"hotel":"Hotel","gasthof":"Gasthof","ferienwohnung":"Ferienwohnung",
                         "ferienhaus":"Ferienhaus","jugendherberge":"Jugendherberge",
                         "camping":"Campingplatz","bauernhof":"Bauernhof"}.get(typ, typ)

            print(f"🔄 {name} ({ort}) [{current}S→...]", end=" ", flush=True)
            try:
                new_html = generate(name, ort, typ_label)
                entry["beschreibung"] = new_html
                json.dump(entry, open(fp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
                ns = count_sentences(new_html)
                print(f"✅ {ns} Sätze", flush=True)
                total_done += 1
            except Exception as e:
                print(f"❌ {e}", flush=True)
                total_err += 1

            time.sleep(1.0)
            total_needed += 1

    print(f"\n{'='*50}", flush=True)
    print(f"Done: {total_done}, Errors: {total_err}", flush=True)
    print(f"{'='*50}", flush=True)

if __name__ == "__main__":
    main()
