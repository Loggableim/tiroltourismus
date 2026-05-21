#!/usr/bin/env python3
import os, json, urllib.request

# Check env
key = os.environ.get("OPENCODE_GO_API_KEY", "")
print(f"KEY_LEN: {len(key)}")
print(f"KEY_EXISTS: {bool(key)}")

# Also check DEEPSEEK
ds_key = os.environ.get("DEEPSEEK_API_KEY", "")
print(f"DS_KEY_LEN: {len(ds_key)}")

# Try the API
API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
body = {
    "model": "deepseek-v4-flash",
    "messages": [{"role": "user", "content": "Say hello in 3 words."}],
    "max_tokens": 20,
}
req = urllib.request.Request(
    API_URL,
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    method="POST",
)
try:
    resp = urllib.request.urlopen(req, timeout=15)
    result = json.loads(resp.read())
    print(f"OK: {result['choices'][0]['message']['content']}")
except Exception as e:
    print(f"ERR: {type(e).__name__}: {e}")
