"""Test API call for extending descriptions."""
import json, os, urllib.request, re

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

print(f"API_KEY loaded: {API_KEY[:8]}...{API_KEY[-4:]}")

# Test with alpinarium
entry = json.load(open("src/data/sehenswuerdigkeiten/alpinarium/index.json"))
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

body = {
    "model": "deepseek-v4-flash",
    "messages": [
        {"role": "system", "content": "Du schreibst sachliche, informative Beschreibungen für ein Tirol-Tourismusportal. Deutsch, 5-8 Sätze, als HTML-Paragraph. Kein Marketington, keine Übertreibungen. Nur das HTML ausgeben, keine Denkprozesse."},
        {"role": "user", "content": prompt}
    ],
    "max_tokens": 4096,
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
    resp = urllib.request.urlopen(req, timeout=120)
    result = json.loads(resp.read())
    text = result["choices"][0]["message"]["content"].strip()
    print(f"\n=== Generated description for {name} ===")
    print(text)
    
    clean = re.sub(r"<[^>]+>", "", text)
    clean = clean.replace("\n", " ").strip()
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if s.strip()]
    print(f"\n--- Sentence count: {len(sents)} ---")
except Exception as e:
    print(f"ERROR: {e}")
    if hasattr(e, "read"):
        print(e.read().decode())
