import os
print(f"OPENCODE_GO_API_KEY set: {'OPENCODE_GO_API_KEY' in os.environ}")
val = os.environ.get('OPENCODE_GO_API_KEY', '')
print(f"Value length: {len(val)}")
print(f"First 5 chars: {repr(val[:5])}")

# Check all env vars
for k in sorted(os.environ.keys()):
    if 'OPENCODE' in k.upper() or 'API' in k.upper() or 'KEY' in k.upper() or 'TOKEN' in k.upper():
        v = os.environ[k]
        print(f"  {k}={v[:20] if v else '(empty)'} (len={len(v)})")
