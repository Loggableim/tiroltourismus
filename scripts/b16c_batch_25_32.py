#!/usr/bin/env python3
"""
B16c: Regeneriere Beschreibungen auf MINDESTENS 5 Sätze (Batch 25-32).
Verwendet deepseek-v4-flash via opencode.ai API.
"""
import json, os, sys, time, re

# Redirect stdout to a log file for visibility
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "b16c_batch_25_32.log")
log_fh = open(LOG_FILE, "w", encoding="utf-8")
def log(msg, end="\n"):
    print(msg, end=end)
    log_fh.write(msg + end)
    log_fh.flush()

# Load .env
for env_file_candidate in [
    "E:/HermesPortable/home/.env",
    os.path.expanduser(r"~\\.hermes\\.env"),
    os.path.join(os.environ.get("HERMES_HOME", ""), ".env"),
]:
    if env_file_candidate and os.path.exists(env_file_candidate):
        with open(env_file_candidate) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ[k] = v

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")

if not API_KEY:
    for _ep in [
        os.path.expanduser(r"~\\.hermes\\.env"),
        r"C:\Users\logga\.hermes\.env",
    ]:
        if os.path.exists(_ep):
            with open(_ep, "r", encoding="utf-8") as _f:
                for _line in _f:
                    _line = _line.strip()
                    if _line.startswith("OPENCODE_GO_API_KEY="):
                        API_KEY = _line.split("=", 1)[1].strip()
                        break
            if API_KEY:
                break

BATCH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batches", "b16")


def count_sentences(html_text):
    """Count sentences in HTML description."""
    plain = re.sub(r'<[^>]+>', '', html_text).strip()
    sentences = [s.strip() for s in re.split(r'[.!?]+', plain) if s.strip()]
    return len(sentences)


def generate_description(name, ort, typ, region):
    """Generiere eine Beschreibung mit MINDESTENS 5 Sätzen via deepseek-v4-flash."""
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

    if HAS_REQUESTS:
        return _generate_via_requests(body)
    else:
        return _generate_via_urllib(body)


def _generate_via_requests(body):
    import requests as req_lib
    try:
        resp = req_lib.post(
            API_URL,
            json=body,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "User-Agent": "curl/8.0.0",
            },
            timeout=180,
        )
        if resp.status_code != 200:
            raise ValueError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        result = resp.json()
        text = result["choices"][0]["message"]["content"].strip()
        if not text:
            raise ValueError("Empty content from API")
        return text
    except Exception as e:
        log(f"    ⚠️ API-Fehler (1.Versuch): {e}")
        try:
            time.sleep(3)
            resp = req_lib.post(
                API_URL,
                json=body,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "User-Agent": "curl/8.0.0",
                },
                timeout=180,
            )
            if resp.status_code != 200:
                raise ValueError(f"HTTP {resp.status_code}")
            result = resp.json()
            text = result["choices"][0]["message"]["content"].strip()
            if not text:
                raise ValueError("Empty content on retry")
            return text
        except Exception as e2:
            log(f"    ⚠️ Retry auch fehlgeschlagen: {e2}")
            return ""


def _generate_via_urllib(body):
    import urllib.request, ssl
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "User-Agent": "curl/8.0.0",
        },
        method="POST"
    )
    try:
        ctx = ssl.create_default_context()
        resp = urllib.request.urlopen(req, timeout=180, context=ctx)
        result = json.loads(resp.read())
        text = result["choices"][0]["message"]["content"].strip()
        if not text:
            raise ValueError("Empty content from API")
        return text
    except Exception as e:
        log(f"    ⚠️ API-Fehler (1.Versuch): {e}")
        try:
            time.sleep(3)
            resp = urllib.request.urlopen(req, timeout=180, context=ctx)
            result = json.loads(resp.read())
            text = result["choices"][0]["message"]["content"].strip()
            if not text:
                raise ValueError("Empty content on retry")
            return text
        except Exception as e2:
            log(f"    ⚠️ Retry auch fehlgeschlagen: {e2}")
            return ""


def process_batch(batch_file):
    """Process a single batch file."""
    log(f"\n{'='*60}")
    log(f"📋 Verarbeite: {os.path.basename(batch_file)}")
    log(f"{'='*60}")

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
            log(f"  [{idx+1}/{len(batch_data)}] {name}: Datei nicht gefunden ❌")
            failed += 1
            continue

        entry = json.load(open(filepath, encoding="utf-8"))
        region = entry.get("region", "")

        loc_for_display = ort if ort else (region if region else "?")
        log(f"  [{idx+1}/{len(batch_data)}] {name} (aktuell: {aktuelle} Sätze, Ort: {loc_for_display})...", end=" ")

        # Generate new description
        desc = generate_description(name, ort or "", typ, region)
        if not desc:
            log("❌ Keine Beschreibung erhalten")
            failed += 1
            continue

        # Ensure HTML wrapping
        if not desc.startswith("<"):
            desc = f"<p>{desc}</p>"

        # Count sentences
        new_count = count_sentences(desc)
        if new_count < 5:
            log(f"⚠️ Nur {new_count} Sätze (Ziel: 5+)")
        else:
            log(f"✅ ({new_count} Sätze)")

        # Write back - only update beschreibung, leave everything else
        entry["beschreibung"] = desc
        json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        enriched += 1

        # Rate limit: 1s between requests
        if idx < len(batch_data) - 1:
            time.sleep(1.1)

    log(f"\n  Ergebnis: {enriched} angereichert, {skipped} übersprungen, {failed} fehlgeschlagen")
    return enriched, skipped, failed


def main():
    batches = list(range(25, 33))
    total_enriched = 0
    total_skipped = 0
    total_failed = 0

    log("=" * 60)
    log("B16c: Beschreibungen auf 5+ Sätze regenerieren (Batch 25-32)")
    log(f"Modell: deepseek-v4-flash")
    log(f"API: {'requests' if HAS_REQUESTS else 'urllib'}")
    log(f"API Key: {'✅ gefunden' if API_KEY else '❌ NICHT gefunden'}")
    log(f"Batches: {batches}")
    log(f"Log: {LOG_FILE}")
    log("=" * 60)

    if not API_KEY:
        log("\n❌ OPENCODE_GO_API_KEY nicht gefunden! Abbruch.")
        sys.exit(1)

    for b in batches:
        batch_file = os.path.join(BATCH_DIR, f"batch_{b:03d}.json")
        if not os.path.exists(batch_file):
            log(f"\n⚠️  Batch {b:03d} nicht gefunden: {batch_file}")
            continue
        e, s, f = process_batch(batch_file)
        total_enriched += e
        total_skipped += s
        total_failed += f

    log(f"\n{'='*60}")
    log(f"✅ FERTIG: {total_enriched} Einträge angereichert")
    if total_skipped:
        log(f"   Übersprungen: {total_skipped}")
    if total_failed:
        log(f"   Fehlgeschlagen: {total_failed}")
    log(f"{'='*60}")
    log_fh.close()


if __name__ == "__main__":
    main()
