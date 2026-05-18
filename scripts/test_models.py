#!/usr/bin/env python
"""Test various model names and endpoints for opencode-go."""
import json, os, sys, urllib.request, urllib.error

sys.path.insert(0, "E:/HermesPortable/cids-hermes-agent")
os.environ["HERMES_HOME"] = "E:/HermesPortable/home"

# Get API key
auth_path = "E:/HermesPortable/home/auth.json"
with open(auth_path) as f:
    data = json.load(f)
api_key = data["credential_pool"]["opencode-go"][0]["access_token"]

base_urls = [
    "https://opencode.ai/zen/go/v1",
    "https://opencode.ai/zen/v1",
]

models = [
    "deepseek-v4-flash",
    "deepseek-chat",
    "deepseek-v4",
    "gpt-4o-mini",
]

for base_url in base_urls:
    for model in models:
        url = f"{base_url}/chat/completions"
        body = {
            "model": model,
            "messages": [{"role": "user", "content": "Say hi."}],
            "max_tokens": 5,
        }
        req = urllib.request.Request(
            url, data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST"
        )
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read())
            print(f"✅ {base_url}/{model}: {result['choices'][0]['message']['content']}")
        except urllib.error.HTTPError as e:
            code = e.code
            msg = e.read().decode()[:150]
            print(f"❌ {base_url}/{model}: HTTP {code} {msg}")
        except Exception as e:
            print(f"⚠️ {base_url}/{model}: {e}")
