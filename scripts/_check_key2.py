#!/usr/bin/env python3
"""Check if Hermes venv has the key."""
import os, sys

venv = r"C:\Users\logga\AppData\Local\hermes\hermes-agent\venv"
if os.path.exists(venv):
    # Try to activate - just check the key in current env
    key = os.environ.get("OPENCODE_GO_API_KEY", "")
    print(f"Current env Key len: {len(key)}")
    print(f"Current env Key exists: {bool(key)}")

# Check windows env through a different mechanism
print(f"\nPython executable: {sys.executable}")
print(f"Platform: {sys.platform}")

# Try to look for any config files that might have the key
config_dirs = [
    r"C:\Users\logga\AppData\Local\hermes",
    r"C:\Users\logga\.config\hermes",
]
for d in config_dirs:
    if os.path.exists(d):
        print(f"\nContents of {d}:")
        for root, dirs, files in os.walk(d):
            for f in files:
                fp = os.path.join(root, f)
                if fp.endswith((".json", ".yaml", ".yml", ".env")):
                    print(f"  {fp}")
