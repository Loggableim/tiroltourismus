#!/usr/bin/env python3
"""Set OPENCODE_GO_API_KEY from Hermes auth.json and run enrich_batch."""
import json
import os
import sys
import subprocess

# Read the API key from Hermes auth.json
auth_path = os.path.expanduser("E:/HermesPortable/home/auth.json")
with open(auth_path) as f:
    data = json.load(f)

pool = data["credential_pool"].get("opencode-go", [])
if not pool:
    print("ERROR: No opencode-go credentials found in auth.json")
    sys.exit(1)

token = pool[0].get("access_token", "")
if not token:
    print("ERROR: Empty access_token for opencode-go")
    sys.exit(1)

os.environ["OPENCODE_GO_API_KEY"] = token
print(f"OPENCODE_GO_API_KEY set (len={len(token)})")

# Run the enrich_batch
batch_file = sys.argv[1]
cmd = ["python3", "scripts/enrich_batch.py", "--file", batch_file]
print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, cwd="F:/tiroltourismus", env={**os.environ})
sys.exit(result.returncode)
