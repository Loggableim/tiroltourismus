#!/usr/bin/env python3
"""Extract OPENCODE_GO_API_KEY from Hermes auth.json and print as shell export."""
import json
import sys

auth_path = "E:/HermesPortable/home/auth.json"
with open(auth_path) as f:
    data = json.load(f)

pool = data["credential_pool"].get("opencode-go", [])
if not pool:
    print("echo 'ERROR: No opencode-go credentials found'")
    sys.exit(1)

token = pool[0].get("access_token", "")
if not token:
    print("echo 'ERROR: Empty access_token for opencode-go'")
    sys.exit(1)

# Print safe shell-safe export
print(f"export OPENCODE_GO_API_KEY='{token}'")
