#!/usr/bin/env python3
"""Test with max_tokens=800."""
import json, os, urllib.request, ssl

API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")

body = {
    "model": "deepseek-v4-flash",
    "messages": [
        {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph."},
        {"role": "user", "content": "Schreibe 2-3 Sätze HTML über 'Camping Rossbach' in Nassereith, Tirol, Österreich. Art: Campingplatz. Beschreibe die Lage, Atmosphäre und was Gäste erwartet. Sachlich, kein Marketington, kein Superlativ. Maximal 120 Wörter. Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"}
    ],
    "max_tokens": 800,
    "temperature": 0.4,
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(
    API_URL,
    data=json.dumps(body).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    },
    method="POST"
)

resp = urllib.request.urlopen(req, timeout=30, context=ctx)
result = json.loads(resp.read())
content = result["choices"][0]["message"]["content"].strip()
print("Content:", content)
print("Finish reason:", result["choices"][0]["finish_reason"])
usage = result["usage"]
print(f"Usage: prompt={usage['prompt_tokens']}, completion={usage['completion_tokens']}, total={usage['total_tokens']}")
if "completion_tokens_details" in usage:
    print(f"Reasoning tokens: {usage['completion_tokens_details'].get('reasoning_tokens', 'N/A')}")
print(f"Length check: >= 10 chars? {len(content) >= 10}")
