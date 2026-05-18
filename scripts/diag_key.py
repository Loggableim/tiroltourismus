#!/usr/bin/env python
"""Diagnose the auth key situation more carefully."""
import os, sys, json

# 1. Check env var directly
env_key = os.environ.get("OPENCODE_GO_API_KEY", "")
print(f"1. OPENCODE_GO_API_KEY from env: len={len(env_key)}, repr={repr(env_key[:8])}")

# 2. Read auth.json and show the raw access_token
auth_path = "E:/HermesPortable/home/auth.json"
with open(auth_path) as f:
    data = json.load(f)
pool = data.get("credential_pool", {}).get("opencode-go", [])
if pool:
    token = pool[0].get("access_token", "")
    print(f"2. auth.json access_token: len={len(token)}, repr={repr(token)}")
else:
    print("2. No opencode-go entries in auth.json")

# 3. Try credential_pool module for real
sys.path.insert(0, "E:/HermesPortable/cids-hermes-agent")
try:
    from agent.credential_pool import load_pool, CredentialPool
    result = load_pool("opencode-go")
    print(f"3. load_pool returned: {type(result).__name__}")
    if hasattr(result, '__iter__') and not isinstance(result, (str, bytes, dict)):
        items = list(result)
        if items:
            print(f"   First item type: {type(items[0]).__name__}")
            if hasattr(items[0], 'access_token'):
                print(f"   access_token: len={len(items[0].access_token)}, repr={repr(items[0].access_token[:8])}")
except Exception as e:
    print(f"3. Error: {type(e).__name__}: {e}")

# 4. Check env var again (after pool load)
env_key2 = os.environ.get("OPENCODE_GO_API_KEY", "")
print(f"4. After pool load - OPENCODE_GO_API_KEY: len={len(env_key2)}, repr={repr(env_key2[:8])}")
