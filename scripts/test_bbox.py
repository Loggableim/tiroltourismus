import requests
ov = "https://overpass-api.de/api/interpreter"

# Test 1: Simple bbox query for Tirol
q1 = '[out:json][timeout:30];node(46.4,10.1,47.6,12.9)[amenity=restaurant];out body 3;'
print("Test 1: bbox for Tirol", flush=True)
r = requests.post(ov, data={"data": q1}, headers={"User-Agent": "Test/1.0", "Accept": "application/json"}, timeout=30)
print(f"  Status: {r.status_code}", flush=True)
if r.status_code == 200:
    data = r.json()
    print(f"  Elements: {len(data.get('elements',[]))}", flush=True)
    for e in data.get('elements', [])[:2]:
        print(f"    {e.get('tags',{}).get('name','?')} ({e.get('lat','?')},{e.get('lon','?')})", flush=True)
else:
    print(f"  {r.text[:200]}", flush=True)

# Test 2: All amenity types with bbox
q2 = '[out:json][timeout:60];(node(46.4,10.1,47.6,12.9)[amenity=restaurant];node(46.4,10.1,47.6,12.9)[amenity=cafe];node(46.4,10.1,47.6,12.9)[amenity=pub];node(46.4,10.1,47.6,12.9)[amenity=bar];node(46.4,10.1,47.6,12.9)[amenity=bistro];node(46.4,10.1,47.6,12.9)[amenity=fast_food];node(46.4,10.1,47.6,12.9)[amenity=food_court];);out center body;'
print("\nTest 2: All amenity types with bbox", flush=True)
r = requests.post(ov, data={"data": q2}, headers={"User-Agent": "Test/1.0", "Accept": "application/json"}, timeout=120)
print(f"  Status: {r.status_code}", flush=True)
if r.status_code == 200:
    data = r.json()
    print(f"  Elements: {len(data.get('elements',[]))}", flush=True)
    for e in data.get('elements', [])[:3]:
        print(f"    {e.get('tags',{}).get('name','?')} (type={e.get('type','?')})", flush=True)
else:
    print(f"  {r.text[:200]}", flush=True)

# Test 3: Also include ways and relations
q3 = '[out:json][timeout:120];(node(46.4,10.1,47.6,12.9)[amenity=restaurant];node(46.4,10.1,47.6,12.9)[amenity=cafe];node(46.4,10.1,47.6,12.9)[amenity=pub];node(46.4,10.1,47.6,12.9)[amenity=bar];node(46.4,10.1,47.6,12.9)[amenity=bistro];node(46.4,10.1,47.6,12.9)[amenity=fast_food];way(46.4,10.1,47.6,12.9)[amenity=restaurant];way(46.4,10.1,47.6,12.9)[amenity=cafe];);out center body;'
print("\nTest 3: Including ways", flush=True)
r = requests.post(ov, data={"data": q3}, headers={"User-Agent": "Test/1.0", "Accept": "application/json"}, timeout=180)
print(f"  Status: {r.status_code}", flush=True)
if r.status_code == 200:
    data = r.json()
    print(f"  Elements: {len(data.get('elements',[]))}", flush=True)
else:
    print(f"  {r.text[:200]}", flush=True)
