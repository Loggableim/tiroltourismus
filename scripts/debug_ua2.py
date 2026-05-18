"""Find a User-Agent that works."""
import requests

ov = "https://overpass-api.de/api/interpreter"
q = '[out:json][timeout:120];(node(46.4,10.1,47.6,12.9)[amenity=restaurant];node(46.4,10.1,47.6,12.9)[amenity=cafe];node(46.4,10.1,47.6,12.9)[amenity=pub];node(46.4,10.1,47.6,12.9)[amenity=bar];node(46.4,10.1,47.6,12.9)[amenity=bistro];node(46.4,10.1,47.6,12.9)[amenity=fast_food];);out center body;'

uas = [
    "Test/1.0",
    "Mozilla/5.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "curl/8.17.0",
    "OverpassTurbo/1.0",  # maybe this one works?
    "okhttp/4.12.0",
    "Go-http-client/2.0",
    "Java/1.8",
    "Python/3.12",
    "test",
    "foo",
    "a",
]

for ua in uas:
    r = requests.post(ov, data={"data": q}, headers={"User-Agent": ua, "Accept": "application/json"}, timeout=15)
    status = r.status_code
    if status == 200:
        count = len(r.json().get("elements", []))
        print(f"  ✓ UA='{ua}' → {status}, {count} elements")
    else:
        print(f"  ✗ UA='{ua}' → {status}")
