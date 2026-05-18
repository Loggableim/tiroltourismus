import os
key = os.environ.get("OPENCODE_GO_API_KEY", "")
print(f"Key length: {len(key)}")
print(f"Key first 10: {key[:10]}")
print(f"Key last 5: {key[-5:]}")
