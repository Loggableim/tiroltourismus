#!/usr/bin/env python3
"""Check if OPENCODE_GO_API_KEY is accessible and working."""
import json, os

# Check env first
env_key = os.environ.get("OPENCODE_GO_API_KEY", "")
print(f"Env var length: {len(env_key)}")
print(f"Env var prefix: {env_key[:20] if env_key else 'EMPTY'}")

# Try reading auth.json
auth_paths = [
    "/e/HermesPortable/home/auth.json",
    os.path.expanduser("~/.config/hermes/auth.json"),
    "/c/Users/logga/.config/hermes/auth.json",
]
for ap in auth_paths:
    if os.path.exists(ap):
        print(f"\nFound auth.json at: {ap}")
        try:
            with open(ap, encoding='utf-8') as f:
                data = json.load(f)
            for prov, creds in data.get('credential_pool', {}).items():
                print(f"  Provider: {prov}")
                for c in creds:
                    token = c.get('access_token', '')
                    print(f"    Label: {c.get('label','?')}, Token len: {len(token)}, prefix: {token[:20]}...")
                    print(f"    Source: {c.get('source','?')}, Status: {c.get('last_status','?')}")
                    print(f"    Base URL: {c.get('base_url','?')}")
        except Exception as e:
            print(f"  Error reading: {e}")
