#!/usr/bin/env python
"""Use Hermes credential pool properly to get the API key."""
import os, sys

sys.path.insert(0, "E:/HermesPortable/cids-hermes-agent")
os.environ["HERMES_HOME"] = "E:/HermesPortable/home"

from agent.credential_pool import load_pool

pool = load_pool("opencode-go")
print(f"Pool: {type(pool).__name__}")
print(f"Has credentials: {pool.has_credentials()}")

entry = pool.select()
if entry is None:
    print("select() returned None, trying entries...")
    print(f"Entries attr: {type(pool.entries)}")
    if pool.entries:
        entry = pool.entries[0]
    else:
        print("No entries!")
        sys.exit(1)

print(f"Entry type: {type(entry).__name__}")
print(f"Access token len: {len(entry.access_token)}")
print(f"Access token preview: {repr(entry.access_token[:12])}")

key = entry.access_token
if not key:
    key = str(getattr(entry, 'agent_key', '') or '')

if key:
    import json, urllib.request, urllib.error
    url = "https://opencode.ai/zen/go/v1/chat/completions"
    body = {
        "model": "deepseek-v4-flash",
        "messages": [{"role": "user", "content": "Say hello."}],
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
        print(f"HTTP {e.code}: {e.read().decode()[:300]}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No key found!")
