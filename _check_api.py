#!/usr/bin/env python3
import os, json, urllib.request

# Load .env
for env_file_candidate in [
    "E:/HermesPortable/home/.env",
]:
    if os.path.exists(env_file_candidate):
        with open(env_file_candidate) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ[k] = v

API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
print(f"API_KEY set: {bool(API_KEY)}, len: {len(API_KEY)}")
print(f"First 8 chars: {API_KEY[:8]}...")
