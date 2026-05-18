#!/usr/bin/env python3
import os, json, subprocess, sys

# Check env
key = os.environ.get("OPENCODE_GO_API_KEY", "")
print(f"OPENCODE_GO_API_KEY: length={len(key)}")

# Try to get it from hermes config
try:
    result = subprocess.run(["hermes", "config", "show"], capture_output=True, text=True, timeout=10)
    print("=== hermes config show output (first 2000 chars) ===")
    print(result.stdout[:2000])
except Exception as e:
    print(f"hermes config show error: {e}")
