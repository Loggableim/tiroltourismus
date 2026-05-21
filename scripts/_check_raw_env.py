#!/usr/bin/env python3
"""Read the exact .env content for the OPENCODE_GO_API_KEY line."""
env_path = r"C:\Users\logga\AppData\Local\hermes\.env"
with open(env_path, "rb") as f:
    data = f.read()

# Find the line
lines = data.split(b"\n")
for i, line in enumerate(lines):
    if line.startswith(b"OPENCODE_GO_API_KEY="):
        print(f"Line {i}: {line}")
        print(f"Hex: {line.hex()}")
        print(f"After =: {line.split(b'=', 1)[1]}")
        print(f"Len after =: {len(line.split(b'=', 1)[1])}")
        
# Also check the # comment line
for i, line in enumerate(lines):
    if b"OPENCODE_GO_API_KEY=" in line and b"#" in line:
        print(f"\nComment line {i}: {line}")
        print(f"Hex: {line.hex()}")
