#!/usr/bin/env python3
"""Test different API endpoints"""
import json, os, urllib.request

auth_path = "E:/HermesPortable/home/auth.json"
with open(auth_path, encoding="utf-8") as f:
    auth = json.load(f)

# Get keys
opencode_key = auth["credential_pool"]["opencode-go"][0]["access_token"]
copilot_key = auth["credential_pool"]["copilot"][0]["access_token"]

endpoints = [
    ("opencode-go", "https://opencode.ai/zen/go/v1/chat/completions", opencode_key),
    ("copilot", "https://api.githubcopilot.com/chat/completions", copilot_key),
]

body = {
    "model": "deepseek-v4-flash",
    "messages": [
        {"role": "system", "content": "Say one word."},
        {"role": "user", "content": "Say hello."}
    ],
    "max_tokens": 10,
}

for name, url, key in endpoints:
    print(f"\n=== Trying {name} ===")
    print(f"URL: {url}")
    print(f"Key len: {len(key)}, prefix: {key[:10]}...")
    
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        print(f"OK: {result['choices'][0]['message']['content'][:100]}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        if hasattr(e, "read"):
            try:
                print(f"Body: {e.read().decode()[:300]}")
            except:
                pass
