"""Debug empty content issue with deepseek-v4-flash."""
import json, os, urllib.request, time, re

API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
if not API_KEY:
    for f in ["E:/HermesPortable/home/.env", os.path.expanduser("~/.hermes/.env")]:
        if os.path.exists(f):
            with open(f) as fh:
                for line in fh:
                    if line.startswith("OPENCODE_GO_API_KEY="):
                        API_KEY = line.split("=", 1)[1].strip()
                        break
            if API_KEY:
                break

# Test with Mondscheinspitze (failed entry)
entry = json.load(open("src/data/sehenswuerdigkeiten/mondscheinspitze/index.json"))
name = entry["name"]
ort = entry["ort"]
typ = entry["kategorie"]

prompt = (
    'Schreibe eine sachlich-informative Beschreibung von 5 bis 8 Sätzen '
    f'über die Sehenswürdigkeit "{name}" in {ort}, Tirol, Österreich. '
    f'Kategorie/Typ: {typ}. '
    'Beschreibe die Lage, Angebote, Besonderheiten und was Besucher erwartet. '
    'Sachlich, informativ, kein Marketing-Jargon, keine Superlative. '
    'Keine Wiederholungen. '
    'Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>'
)

# Try different max_tokens settings
for mt in [3072, 4096, 2048]:
    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "Du schreibst sachliche, informative Beschreibungen für ein Tirol-Tourismusportal. Deutsch, 5-8 Sätze, als HTML-Paragraph. Kein Marketington, keine Übertreibungen. Nur das HTML ausgeben, keine Denkprozesse."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": mt,
        "temperature": 0.3,
    }

    req = urllib.request.Request(
        "https://opencode.ai/zen/go/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
        method="POST",
    )

    try:
        t0 = time.time()
        resp = urllib.request.urlopen(req, timeout=120)
        resp_data = json.loads(resp.read())
        elapsed = time.time() - t0
        
        choice = resp_data["choices"][0]
        finish_reason = choice.get("finish_reason", "?")
        message = choice.get("message", {})
        content = message.get("content", "")
        reasoning = message.get("reasoning_content", "")
        
        clean = re.sub(r"<[^>]+>", "", content)
        clean = clean.replace("\n", " ").strip()
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if s.strip()] if clean else []
        
        print(f"\nmax_tokens={mt}: {elapsed:.1f}s, finish={finish_reason}")
        print(f"  reasoning_tokens: {len(reasoning)} chars")
        print(f"  sentences: {len(sents)}, content_length: {len(content)}")
        print(f"  has_content: {bool(content)}")
        if content:
            print(f"  preview: {content[:150]}...")
        if reasoning:
            print(f"  reasoning (first 100): {reasoning[:100]}")
    except Exception as e:
        print(f"\nmax_tokens={mt}: ERROR - {e}")
        if hasattr(e, "read"):
            print(e.read().decode())
    
    time.sleep(1.1)
