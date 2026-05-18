#!/usr/bin/env python3
"""Wrapper: loads .env from Hermes home, then runs enrich_batch.py."""
import os, sys, subprocess

# Find and load the .env file
env_paths = [
    "E:/HermesPortable/home/.env",
    os.path.expanduser("~/.hermes/.env"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"),
]

for env_path in env_paths:
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, _, val = line.partition("=")
                    os.environ[key.strip()] = val.strip()

# Verify key is now set
key = os.environ.get("OPENCODE_GO_API_KEY", "")
print(f"OPENCODE_GO_API_KEY: {'set' if key else 'MISSING'} (len={len(key)})", file=sys.stderr)

# Run enrich_batch.py with same args
script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enrich_batch.py")
result = subprocess.run([sys.executable, script] + sys.argv[1:])
sys.exit(result.returncode)
