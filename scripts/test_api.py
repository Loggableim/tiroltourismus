#!/usr/bin/env python3
"""Quick test of the API endpoint."""
import json, os, urllib.request

API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")

body = {
    "model": "deepseek-v4-flash",
    "messages": [
        {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph."},
        {"role": "user", "content": 'Schreibe 2-3 Sätze HTML über "Essbaum" in Tirol, Österreich. Art: Ferienwohnung. Beschreibe die Lage, Atmosphäre und was Gäste erwartet. Sachlich, kein Marketington, kein Superlativ. Maximal 120 Wörter. Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>'}
    ],
    "max_tokens": 200,
    "temperature": 0.4,
}

req = urllib.request.Request(
    API_URL,
    data=json.dumps(body).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    },
    method="POST"
)
try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    print("Choices:", len(result.get("choices", [])))
    if result.get("choices"):
        print("Content:", repr(result["choices"][0]["message"]["content"]))
    else:
        print("Full response:", json.dumps(result, indent=2)[:1000])
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'read'):
        print(e.read().decode())
