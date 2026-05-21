import requests, os
print("requests OK" if requests else "no requests")
key = os.environ.get("OPENCODE_GO_API_KEY", "")
if not key:
    for ef in ["E:/HermesPortable/home/.env", os.path.expanduser("~/.hermes/.env")]:
        if os.path.exists(ef):
            with open(ef) as f:
                for line in f:
                    if line.startswith("OPENCODE_GO_API_KEY="):
                        key = line.strip().split("=", 1)[1]
                        break
print(f"API key: {key[:10]}..." if key else "NO API KEY")
