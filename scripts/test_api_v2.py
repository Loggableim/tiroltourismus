#!/usr/bin/env python
"""Test the exact same API call as enrich_batch.py with the real key."""
import json, os, sys, urllib.request, urllib.error

# Read API key from auth.json
auth_path = "E:/HermesPortable/home/auth.json"
with open(auth_path) as f:
    data = json.load(f)
pool = data.get("credential_pool", {}).get("opencode-go", [])
api_key = pool[0]["access_token"]
print(f"Key length: {len(api_key)}")
print(f"Key preview: {repr(api_key[:12])}...")

# Exact same call as enrich_batch.py
url = "https://opencode.ai/zen/go/v1/chat/completions"
body = {
    "model": "deepseek-v4-flash",
    "messages": [
        {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph."},
        {"role": "user", "content": "Schreibe 2-3 Sätze HTML über 'Jausenstation Hochschwendt' in Ellmau, Tirol, Österreich. Art: Gasthof. Beschreibe die Lage, Atmosphäre und was Gäste erwartet. Sachlich, kein Marketington, kein Superlativ. Maximal 120 Wörter. Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"}
    ],
    "max_tokens": 200,
    "temperature": 0.4,
}
print(f"\nSending request to {url}...")
req = urllib.request.Request(
    url, data=json.dumps(body).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    },
    method="POST"
)
try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    text = result["choices"][0]["message"]["content"].strip()
    print(f"Response ({len(text)} chars):")
    print(text[:300])
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.reason}")
    print(f"Body: {e.read().decode()[:500]}")
except Exception as e:
    print(f"Error: {e}")
