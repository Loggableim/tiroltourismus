#!/usr/bin/env python3
"""Debug script to test the API connection."""
import json, os, urllib.request

API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
print(f"Key length: {len(API_KEY)}")
print(f"Key starts with: {API_KEY[:10] if API_KEY else 'EMPTY'}")

body = {
    "model": "deepseek-v4-flash",
    "messages": [{"role": "user", "content": "Say hello in one word"}],
    "max_tokens": 10,
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
    print("SUCCESS:", result["choices"][0]["message"]["content"][:100])
except Exception as e:
    print(f"ERROR: {e}")
    if hasattr(e, "code"):
        print(f"HTTP code: {e.code}")
    if hasattr(e, "read"):
        print(f"Body: {e.read().decode()[:500]}")
