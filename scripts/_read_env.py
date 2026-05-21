#!/usr/bin/env python3
"""Try to read the actual API key from .env file using raw file I/O."""
import os

env_path = r"C:\Users\logga\AppData\Local\hermes\.env"
print(f"File exists: {os.path.exists(env_path)}")

with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line.startswith("OPENCODE_GO_API_KEY="):
            key = line.split("=", 1)[1].strip()
            print(f"Found key, length: {len(key)}")
            print(f"First 10 chars: {key[:10]}")
            # Test if it's masked
            if key == "***":
                print("Key is literally '***' mask")
            else:
                print("Key appears to be real")
            break
