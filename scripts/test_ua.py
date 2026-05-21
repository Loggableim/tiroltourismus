#!/usr/bin/env python3
"""Test API with User-Agent header."""
import json, os, urllib.request

API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
body = {
    "model": "deepseek-v4-flash",
    "messages": [
        {"role": "system", "content": "Du schreibst kurze Beschreibungen."},
        {"role": "user", "content": "Schreibe 2 Sätze über Tirol."}
    ],
    "max_tokens": 300,
    "temperature": 0.4,
}

# Test WITH User-Agent
req = urllib.request.Request(
    "https://opencode.ai/zen/go/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "User-Agent": "curl/8.0.0",
    },
    method="POST"
)
try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    print("WITH User-Agent:")
    print(" Content:", repr(result["choices"][0]["message"]["content"][:200]))
except Exception as e:
    print(f"WITH User-Agent FAILED: {e}")
    if hasattr(e, 'read'):
        print(" Body:", e.read().decode())

# Test WITHOUT User-Agent
req2 = urllib.request.Request(
    "https://opencode.ai/zen/go/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    },
    method="POST"
)
try:
    resp = urllib.request.urlopen(req2, timeout=30)
    result = json.loads(resp.read())
    print("WITHOUT User-Agent:")
    print(" Content:", repr(result["choices"][0]["message"]["content"][:200]))
except Exception as e:
    print(f"WITHOUT User-Agent FAILED: {e}")
    if hasattr(e, 'read'):
        print(" Body:", e.read().decode())
