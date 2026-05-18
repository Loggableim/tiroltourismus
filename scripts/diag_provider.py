#!/usr/bin/env python
"""Check what the Hermes runtime is actually using."""
import os, sys, json

# Check all HERMES-related env vars
for k, v in sorted(os.environ.items()):
    if 'HERMES' in k.upper() or 'MODEL' in k.upper() or 'PROVIDER' in k.upper():
        print(f"{k}={v}")

print("\n--- Auth config ---")
sys.path.insert(0, "E:/HermesPortable/cids-hermes-agent")
os.environ["HERMES_HOME"] = "E:/HermesPortable/home"

from hermes_cli.config import load_config
cfg = load_config()
model = cfg.get("model", {})
print(f"Config model.default: {model.get('default')}")
print(f"Config model.provider: {model.get('provider')}")
print(f"Config model.base_url: {model.get('base_url')}")

# Check profile config
profile_path = "E:/HermesPortable/home/profiles/content-filler/config.yaml"
if os.path.exists(profile_path):
    import yaml
    with open(profile_path) as f:
        pcfg = yaml.safe_load(f) or {}
    pmodel = pcfg.get("model", {})
    print(f"\nProfile model.default: {pmodel.get('default')}")
    print(f"Profile model.provider: {pmodel.get('provider')}")

# Also check what happens with the fallback providers
print("\n--- Testing fallback: local-gpu ---")
import subprocess
result = subprocess.run(
    ["curl", "-s", "--max-time", "5", "http://localhost:8080/v1/models"],
    capture_output=True, text=True
)
if result.returncode == 0:
    print(f"local-gpu: {result.stdout[:200]}")
else:
    print(f"local-gpu not available")

print("\n--- Testing fallback: local-cpu ---")
result = subprocess.run(
    ["curl", "-s", "--max-time", "5", "http://localhost:8081/v1/models"],
    capture_output=True, text=True
)
if result.returncode == 0:
    print(f"local-cpu: {result.stdout[:200]}")
else:
    print(f"local-cpu not available")
