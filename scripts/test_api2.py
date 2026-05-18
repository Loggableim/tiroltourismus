#!/usr/bin/env python3
"""Test API call with requests."""
import json, os

env_file = "E:/HermesPortable/home/.env"
with open(env_file) as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k] = v

API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")

# Try with requests
try:
    import requests
    resp = requests.post(
        "https://opencode.ai/zen/go/v1/chat/completions",
        json={
            "model": "deepseek-v4-flash",
            "messages": [
                {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen. Deutsch."},
                {"role": "user", "content": "Schreibe 2 Sätze HTML über 'Hotel Landhof' in Ellmau, Tirol. Format: <p>Text</p>"}
            ],
            "max_tokens": 200,
            "temperature": 0.4,
        },
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=30,
        verify=False
    )
    print(f"Status: {resp.status_code}")
    result = resp.json()
    text = result["choices"][0]["message"]["content"].strip()
    print(f"Content: {text[:300]}")
except Exception as e:
    print(f"Requests error: {e}")
    import traceback
    traceback.print_exc()

# Now try with ssl context
print("\n--- Trying with SSL context ---")
import urllib.request, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

body = {
    "model": "deepseek-v4-flash",
    "messages": [
        {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen. Deutsch."},
        {"role": "user", "content": "Schreibe 2 Sätze HTML über 'Hotel Landhof' in Ellmau, Tirol. Format: <p>Text</p>"}
    ],
    "max_tokens": 200,
    "temperature": 0.4,
}

req = urllib.request.Request(
    "https://opencode.ai/zen/go/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    },
    method="POST"
)

try:
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    result = json.loads(resp.read())
    text = result["choices"][0]["message"]["content"].strip()
    print(f"Status: {resp.status}")
    print(f"Content: {text[:300]}")
except Exception as e:
    print(f"urllib error: {e}")
