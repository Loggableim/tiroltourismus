#!/usr/bin/env python
"""Check what API keys are available in our environment."""
import os

# Check all env vars for API keys
for k, v in sorted(os.environ.items()):
    if 'api' in k.lower() or 'key' in k.lower() or 'token' in k.lower() or 'secret' in k.lower():
        preview = v[:12] + '...' if v else '(empty)'
        print(f"{k}={preview}")

print("\n--- OLLAMA ---")
# Try ollama cloud as alternative
ollama_key = os.environ.get("OLLAMA_API_KEY", "")
if ollama_key:
    print(f"OLLAMA_API_KEY available: len={len(ollama_key)}")
else:
    print("OLLAMA_API_KEY not available")
