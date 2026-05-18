#!/usr/bin/env python3
"""Check what the ACTUAL key value is from .env by reading raw bytes.
This is the most accurate check possible."""
env_path = r"C:\Users\logga\AppData\Local\hermes\.env"
with open(env_path, "rb") as f:
    data = f.read()

lines = data.split(b"\n")
for i, line in enumerate(lines):
    if line.startswith(b"OPENCODE_GO_API_KEY=") and not line.startswith(b"#"):
        # Extract value after =
        val = line.split(b"=", 1)[1]
        # Strip \r if present
        val = val.replace(b"\r", b"")
        print(f"Line {i}: length={len(val)}")
        print(f"Bytes: {val}")
        print(f"Valid sk- prefix: {val.startswith(b'sk-')}")
        break
