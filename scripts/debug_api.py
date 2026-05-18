#!/usr/bin/env python3
"""Debug: check raw API response for empty HTML entries."""
import json, os, ssl, urllib.request

API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
if not API_KEY:
    HERMES_HOME = os.environ.get("HERMES_HOME", "")
    env_paths = [
        os.path.expanduser("~/.hermes/.env"),
        r"C:\Users\logga\.hermes\.env",
        os.path.join(HERMES_HOME, ".env"),
        r"E:\HermesPortable\home\.env",
    ]
    for ep in env_paths:
        if os.path.exists(ep):
            with open(ep) as f:
                for line in f:
                    if line.startswith("OPENCODE_GO_API_KEY="):
                        API_KEY = line.split("=", 1)[1].strip()
                        break
            if API_KEY:
                break

API_URL = "https://opencode.ai/zen/go/v1/chat/completions"

body = {
    "model": "deepseek-v4-flash",
    "messages": [
        {"role": "system", "content": "You write short factual descriptions for a Tyrol tourism portal."},
        {"role": "user", "content": "Write 2 sentences about Bauernhof-Ferienwohnung Hecherhof in Thiersee, Tyrol. It is a Ferienwohnung. Describe the location and atmosphere. Factual tone."}
    ],
    "max_tokens": 500,
    "temperature": 0.7,
}

print(f"Key length: {len(API_KEY)}")
print(f"Key starts: {API_KEY[:10] if API_KEY else '(empty)'}")

req = urllib.request.Request(
    API_URL,
    data=json.dumps(body).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "User-Agent": "Mozilla/5.0",
    },
    method="POST"
)

ctx = ssl.create_default_context()
try:
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    raw = resp.read().decode()
    result = json.loads(raw)
    print(f"\nFull response keys: {list(result.keys())}")
    if "choices" in result and len(result["choices"]) > 0:
        content = result["choices"][0]["message"]["content"]
        print(f"\nContent: {repr(content)}")
        print(f"Content length: {len(content)}")
except Exception as e:
    print(f"\nError: {e}")
