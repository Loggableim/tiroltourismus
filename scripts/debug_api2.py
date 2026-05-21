#!/usr/bin/env python3
"""Debug API: test what the API actually returns"""
import json, sys, os, urllib.request

# Get key from auth.json
auth_path = "E:/HermesPortable/home/auth.json"
with open(auth_path, encoding="utf-8") as f:
    auth = json.load(f)
key = auth["credential_pool"]["opencode-go"][0]["access_token"]

# Full request & response debug
API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
body = {
    "model": "deepseek-v4-flash",
    "messages": [
        {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph."},
        {"role": "user", "content": "Schreibe 2-3 Sätze HTML über '5-Sterne-Camping Zugspitz Resort' in Ehrwald, Tirol, Österreich. Art: Campingplatz. Beschreibe die Lage, Atmosphäre und was Gäste erwartet. Sachlich, kein Marketington, kein Superlativ. Maximal 120 Wörter. Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"}
    ],
    "max_tokens": 200,
    "temperature": 0.4,
}

req = urllib.request.Request(
    API_URL,
    data=json.dumps(body).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    },
    method="POST"
)
try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    print(f"Model: {result.get('model', 'N/A')}")
    print(f"Usage: {result.get('usage', {})}")
    content = result["choices"][0]["message"]["content"]
    print(f"\nContent ({len(content)} chars):")
    print(repr(content[:500]))
    print("\n--- finish_reason:", result["choices"][0].get("finish_reason"))
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    if hasattr(e, "read"):
        print(f"Body: {e.read().decode()[:500]}")
