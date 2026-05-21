#!/usr/bin/env python3
"""Wrapper: set API key from auth.json, then run enrich_batch.py --file <batch>"""
import json, sys, os, subprocess

# Read the API key from Hermes auth.json
auth_path = "E:/HermesPortable/home/auth.json"
with open(auth_path, encoding="utf-8") as f:
    auth = json.load(f)
key = auth["credential_pool"]["opencode-go"][0]["access_token"]

# Set env
env = {**os.environ, "OPENCODE_GO_API_KEY": key}

# Build command
batch_file = sys.argv[1]
cmd = ["python", "scripts/enrich_batch.py", "--file", batch_file]
print(f"Processing: {batch_file}")
print(f"API key set (len={len(key)})")
sys.stdout.flush()

result = subprocess.run(cmd, cwd="F:/tiroltourismus", env=env)
sys.exit(result.returncode)
