"""Test API call speed with different models."""
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

print(f"API_KEY: {API_KEY[:8]}...{API_KEY[-4:]}")

models = ["deepseek-v4-flash", "minimax-m2.7", "deepseek-chat"]

for model in models:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, 5-8 Sätze, als HTML-Paragraph."},
            {"role": "user", "content": f"Schreibe eine Beschreibung von 5-8 Sätzen über die Sehenswürdigkeit 'Alpinarium' in Imst, Tirol."}
        ],
        "max_tokens": 2048,
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
        result = json.loads(resp.read())
        text = result["choices"][0]["message"]["content"].strip()
        elapsed = time.time() - t0
        
        # Count sentences
        clean = re.sub(r"<[^>]+>", "", text)
        clean = clean.replace("\n", " ").strip()
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if s.strip()]
        
        print(f"\n{model}: {elapsed:.1f}s, {len(sents)} Sätze")
        print(f"  {text[:120]}...")
    except Exception as e:
        print(f"\n{model}: ERROR - {e}")
