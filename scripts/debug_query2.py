"""Test exact queries from the known-working compare_queries.py."""
import requests

ov = "https://overpass-api.de/api/interpreter"
hdrs = {"User-Agent": "Test/1.0", "Accept": "application/json"}

# Exact working query from compare_queries.py (q_working_ways)
q_working = '[out:json][timeout:120];(node(46.4,10.1,47.6,12.9)[amenity=restaurant];node(46.4,10.1,47.6,12.9)[amenity=cafe];node(46.4,10.1,47.6,12.9)[amenity=pub];node(46.4,10.1,47.6,12.9)[amenity=bar];node(46.4,10.1,47.6,12.9)[amenity=bistro];node(46.4,10.1,47.6,12.9)[amenity=fast_food];way(46.4,10.1,47.6,12.9)[amenity=restaurant];way(46.4,10.1,47.6,12.9)[amenity=cafe];);out center body;'

# Scraper query (no newlines, all 6 types for ways too)
q_scraper = '[out:json][timeout:180];(node(46.4,10.1,47.6,12.9)[amenity=restaurant];node(46.4,10.1,47.6,12.9)[amenity=cafe];node(46.4,10.1,47.6,12.9)[amenity=pub];node(46.4,10.1,47.6,12.9)[amenity=bar];node(46.4,10.1,47.6,12.9)[amenity=bistro];node(46.4,10.1,47.6,12.9)[amenity=fast_food];way(46.4,10.1,47.6,12.9)[amenity=restaurant];way(46.4,10.1,47.6,12.9)[amenity=cafe];way(46.4,10.1,47.6,12.9)[amenity=pub];way(46.4,10.1,47.6,12.9)[amenity=bar];way(46.4,10.1,47.6,12.9)[amenity=bistro];way(46.4,10.1,47.6,12.9)[amenity=fast_food];);out center body;'

# Nodes-only scraper query
q_scraper_nodes = '[out:json][timeout:180];(node(46.4,10.1,47.6,12.9)[amenity=restaurant];node(46.4,10.1,47.6,12.9)[amenity=cafe];node(46.4,10.1,47.6,12.9)[amenity=pub];node(46.4,10.1,47.6,12.9)[amenity=bar];node(46.4,10.1,47.6,12.9)[amenity=bistro];node(46.4,10.1,47.6,12.9)[amenity=fast_food];);out center body;'

queries = [
    ("original_working_378", q_working),
    ("scraper_all_ways_539", q_scraper),
    ("scraper_nodes_only_294", q_scraper_nodes),
]

for name, q in queries:
    print(f"--- {name} ({len(q)} chars) ---", flush=True)
    try:
        r = requests.post(ov, data={"data": q}, headers=hdrs, timeout=30)
        print(f"  Status: {r.status_code}", flush=True)
        if r.status_code == 200:
            data = r.json()
            print(f"  Elements: {len(data.get('elements',[]))}", flush=True)
        else:
            print(f"  Body: {r.text[:150]}", flush=True)
    except Exception as e:
        print(f"  Error: {e}", flush=True)
    print()
