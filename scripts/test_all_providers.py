#!/usr/bin/env python3
"""Try local providers and check what's actually running"""
import json, os, urllib.request

endpoints = [
    ("Local GPU", "http://localhost:8080/v1/chat/completions", "", "Dolphin3.0-Llama3.1-8B-Q4_K_M"),
    ("Local CPU", "http://localhost:8081/v1/chat/completions", "", "Llama-3.2-3B-Instruct-uncensored-Q5_K_M"),
]

body = {
    "model": None,  # will set per endpoint
    "messages": [
        {"role": "system", "content": "Say just one word."},
        {"role": "user", "content": "Say hello."}
    ],
    "max_tokens": 10,
}

for name, url, key, model in endpoints:
    print(f"\n=== {name} ===")
    print(f"URL: {url}")
    body["model"] = model
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=5)
        result = json.loads(resp.read())
        print(f"✅ {result['choices'][0]['message']['content'][:80]}")
    except Exception as e:
        print(f"❌ {type(e).__name__}: {e}")
        if hasattr(e, "code"):
            print(f"   HTTP {e.code}")

# Also try deepseek's official API
print("\n=== Deepseek Official ===")
auth_path = "E:/HermesPortable/home/auth.json"
with open(auth_path, encoding="utf-8") as f:
    auth_data = json.load(f)
deepseek_key = auth_data["credential_pool"]["opencode-go"][0]["access_token"]

for base_url in [
    "https://api.deepseek.com/v1/chat/completions",
    "https://api.deepseek.com/chat/completions",
    "https://api.deepseek.ai/v1/chat/completions",
]:
    body2 = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "Say hello in 3 words."}],
        "max_tokens": 10,
    }
    req = urllib.request.Request(
        base_url,
        data=json.dumps(body2).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {deepseek_key}",
        },
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        print(f"  {base_url} ✅ {result['choices'][0]['message']['content'][:80]}")
    except Exception as e:
        print(f"  {base_url} ❌ {type(e).__name__}: {e}")
        if hasattr(e, "code"):
            print(f"     HTTP {e.code}")
