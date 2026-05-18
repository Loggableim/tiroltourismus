#!/usr/bin/env python3
"""Check how Hermes authenticates to opencode-go by looking at state/sessions."""
import json, os, glob

# Check session DB for any connection info
state_files = [
    "/e/HermesPortable/home/state.db",
    "/e/HermesPortable/home/sessions",
]

for f in state_files:
    if os.path.exists(f):
        print(f"  📁 {f} ({os.path.getsize(f)} bytes)")

# Check auth.json
auth_file = "/e/HermesPortable/home/auth.json"
if os.path.exists(auth_file):
    data = json.load(open(auth_file, encoding='utf-8'))
    # Print keys but not full values
    print(f"  📁 auth.json keys: {list(data.keys())}")
    for k, v in data.items():
        if isinstance(v, str) and len(v) > 10:
            print(f"    {k}: {v[:15]}... (len={len(v)})")
        else:
            print(f"    {k}: {v}")
