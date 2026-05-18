#!/usr/bin/env python3
"""Test the exact generate_description logic."""
import json, os, ssl, urllib.request

# Load env
env_file = "E:/HermesPortable/home/.env"
with open(env_file) as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k] = v

API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
API_URL = "https://opencode.ai/zen/go/v1/chat/completions"

prompt = (
    "Schreibe 2-3 Sätze HTML über 'Hotel Landhof' in Ellmau, Tirol, Österreich. "
    "Art: Hotel. "
    "Beschreibe die Lage, Atmosphäre und was Gäste erwartet. "
    "Sachlich, kein Marketington, kein Superlativ. "
    "Maximal 120 Wörter. "
    "Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"
)

body = {
    "model": "deepseek-v4-flash",
    "messages": [
        {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph."},
        {"role": "user", "content": prompt}
    ],
    "max_tokens": 1024,
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
        "User-Agent": "Mozilla/5.0",
    },
    method="POST"
)

try:
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    result = json.loads(resp.read())
    text = result["choices"][0]["message"]["content"].strip()
    fin_reason = result["choices"][0].get("finish_reason", "?")
    usage = result.get("usage", {})
    print(f"Status: {resp.status}")
    print(f"Finish reason: {fin_reason}")
    print(f"Usage: {json.dumps(usage, indent=2)}")
    print(f"Content: '{text[:500]}'")
    if not text:
        msg = result["choices"][0]["message"]
        if "reasoning_content" in msg:
            print(f"Reasoning (last 200): ...{msg['reasoning_content'][-200:]}")
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'read'):
        print(e.read().decode()[:1000])
