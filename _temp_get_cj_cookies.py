#!/usr/bin/env python3
"""Extract CJ cookies from Zen Browser and import into Camofox"""
import browser_cookie3, json, requests, time

CAMOFOX = "http://localhost:9377"
USER_ID = "cj_onboarding"

cookie_file = r"C:\Users\logga\AppData\Roaming\Zen\Profiles\3t1ky4e4.Default (release)\cookies.sqlite"

# Get all cookies for CJ domains
cj = browser_cookie3.firefox(cookie_file=cookie_file, domain_name="members.cj.com")
cookies = [{"name": c.name, "value": c.value, "domain": c.domain.lstrip("."), 
            "path": c.path or "/", "secure": bool(c.secure), "httpOnly": False} for c in cj]

# Also try to get cj.com cookies
try:
    cj2 = browser_cookie3.firefox(cookie_file=cookie_file, domain_name="cj.com")
    existing_domains = {c['domain'] for c in cookies}
    for c in cj2:
        d = c.domain.lstrip(".")
        if d not in existing_domains:
            cookies.append({"name": c.name, "value": c.value, "domain": d, 
                "path": c.path or "/", "secure": bool(c.secure), "httpOnly": False})
except:
    pass

print(f"Extracted {len(cookies)} cookies")

# Print cookie names for debugging
for c in cookies:
    print(f"  {c['name']}: {c['domain']} -> {c['value'][:30]}...")

# Import into Camofox session
print(f"\nImporting into Camofox session '{USER_ID}'...")
resp = requests.post(f"{CAMOFOX}/sessions/{USER_ID}/cookies", json={
    "cookies": cookies
}, timeout=15)
print(f"Import result: {resp.json()}")

# Create a tab and navigate to CJ onboarding
print("\nCreating tab...")
resp = requests.post(f"{CAMOFOX}/tabs", json={
    "userId": USER_ID,
    "sessionKey": "cj_onboarding",
    "url": "https://members.cj.com/member/publisher/onboarding.cj"
}, timeout=30)

if resp.status_code == 200:
    tab_id = resp.json()["tabId"]
    print(f"Tab created: {tab_id}")
    
    # Wait for page to load
    time.sleep(5)
    
    # Get snapshot
    snap = requests.get(f"{CAMOFOX}/tabs/{tab_id}/snapshot", params={"userId": USER_ID})
    with open("/tmp/cj_snapshot.json", "w") as f:
        json.dump({"tab_id": tab_id, "snapshot": snap.text}, f)
    print(f"\nSnapshot saved. Tab ID: {tab_id}")
    print(f"Snapshot preview (first 2000 chars):")
    print(snap.text[:2000])
else:
    print(f"Error creating tab: {resp.status_code} {resp.text}")

# Save tab_id for later use
with open("/tmp/cj_tab_id.txt", "w") as f:
    f.write(json.dumps({"tab_id": tab_id, "userId": USER_ID}))
