import json, os

# Check auth.json
auth_file = "/e/HermesPortable/home/auth.json"
if os.path.exists(auth_file):
    d = json.load(open(auth_file, encoding='utf-8'))
    print("auth.json keys:", list(d.keys()))
    for k, v in d.items():
        if isinstance(v, str) and len(v) > 5:
            print(f"  {k}: {v[:20]}... (len={len(v)})")
        else:
            print(f"  {k}: {v}")
else:
    print("auth.json NOT found")

# Check if we can find the actual connection details
print()
print("--- Checking credential pool / state ---")

state_db = "/e/HermesPortable/home/state.db"
if os.path.exists(state_db):
    print(f"state.db exists ({os.path.getsize(state_db)} bytes)")

# Check env for anything relevant
for key in sorted(os.environ.keys()):
    if any(x in key.lower() for x in ['key', 'token', 'secret', 'api', 'auth', 'bearer', 'opencode', 'deepseek']):
        val = os.environ[key]
        if val:
            print(f"  {key}: {val[:20]}... (len={len(val)})")
        else:
            print(f"  {key}: (empty)")
