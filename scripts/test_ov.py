import requests, json, sys

ov = "https://overpass-api.de/api/interpreter"
q = '[out:json][timeout:10];node(47.2,10.3,47.5,12.6)[amenity=cafe];out 3;'

print("=== Test POST form-encoded ===", flush=True)
r = requests.post(ov, data={"data": q}, headers={"User-Agent": "Test/1.0", "Accept": "application/json"}, timeout=30)
print(f"Status: {r.status_code}", flush=True)
print(f"Headers: {dict(r.headers)}", flush=True)
print(f"Body (first 300): {r.text[:300]}", flush=True)
