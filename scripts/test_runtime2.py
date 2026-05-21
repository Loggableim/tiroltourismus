#!/usr/bin/env python
"""Use Hermes internal modules to make an API call."""
import os, sys, json

sys.path.insert(0, "E:/HermesPortable/cids-hermes-agent")
os.environ["HERMES_HOME"] = "E:/HermesPortable/home"

from hermes_cli.runtime_provider import resolve_runtime_provider

runtime = resolve_runtime_provider(requested="opencode-go", target_model="deepseek-v4-flash")

api_key = runtime["api_key"]
base_url = runtime["base_url"]
api_mode = runtime["api_mode"]

print(f"Base URL: {base_url}")
print(f"Mode: {api_mode}")
print(f"Key preview: {api_key[:12]}...")
print(f"Provider: {runtime.get('provider')}")

url = f"{base_url}/chat/completions"
body = {
    "model": "deepseek-v4-flash",
    "messages": [
        {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen."},
        {"role": "user", "content": "Schreibe 2 Sätze über ein Hotel in Tirol."}
    ],
    "max_tokens": 100,
    "temperature": 0.4,
}

import urllib.request, urllib.error
req = urllib.request.Request(
    url, data=json.dumps(body).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    },
    method="POST"
)
try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    text = result["choices"][0]["message"]["content"]
    print(f"\n✅ Success! ({len(text)} chars)")
    print(text[:300])
except urllib.error.HTTPError as e:
    print(f"\n❌ HTTP {e.code}: {e.read().decode()[:300]}")
except Exception as e:
    print(f"\n❌ {e}")
