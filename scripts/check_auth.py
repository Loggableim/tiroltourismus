#!/usr/bin/env python3
"""Check auth.json contents"""
import json

auth_path = "E:/HermesPortable/home/auth.json"
with open(auth_path, encoding="utf-8") as f:
    auth = json.load(f)

pool = auth.get("credential_pool", {})
print(f"Credential pool keys: {list(pool.keys())}")

for provider in pool:
    items = pool[provider]
    print(f"\n{provider}: {len(items)} credential(s)")
    for i, item in enumerate(items):
        for k, v in item.items():
            if k == "access_token":
                print(f"  [{i}] {k}: '{v[:15]}...' (len={len(v)})" if v else f"  [{i}] {k}: EMPTY!")
            else:
                v_str = str(v)[:30]
                print(f"  [{i}] {k}: {v_str}")
