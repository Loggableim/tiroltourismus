#!/usr/bin/env python
"""Use Hermes credential pool properly to get the API key."""
import os, sys

sys.path.insert(0, "E:/HermesPortable/cids-hermes-agent")
os.environ["HERMES_HOME"] = "E:/HermesPortable/home"

from agent.credential_pool import load_pool

pool = load_pool("opencode-go")
print(f"Pool type: {type(pool).__name__}")
print(f"Has credentials: {pool.has_credentials()}")
print(f"Pool size: {pool.size()}")

entry = pool.select()
if entry:
    print(f"Entry type: {type(entry).__name__}")
    print(f"Access token: len={len(entry.access_token)}")
    print(f"Runtime API key: {getattr(entry, 'runtime_api_key', 'N/A')}")
    key = entry.access_token or str(entry.agent_key or "") if hasattr(entry, 'agent_key') else entry.access_token
    print(f"Effective key preview: {repr(str(key)[:12])}")
    
    # Try the API call
    import json, urllib.request, urllib.error
    url = "https://opencode.ai/zen/go/v1/chat/completions"
    body = {
        "model": "deepseek-v4-flash",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 10,
    }
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        print(f"API OK: {result['choices'][0]['message']['content']}")
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:200]}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No entry selected from pool")
