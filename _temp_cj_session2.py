#!/usr/bin/env python3
"""Re-import cookies and start fresh CJ session"""
import browser_cookie3, json, requests, time

CAMOFOX = "http://localhost:9377"
USER_ID = "cj_onboarding2"

cookie_file = r"C:\Users\logga\AppData\Roaming\Zen\Profiles\3t1ky4e4.Default (release)\cookies.sqlite"

# Delete old session first
requests.delete(f"{CAMOFOX}/sessions/{USER_ID}")

# Get fresh cookies
cj = browser_cookie3.firefox(cookie_file=cookie_file, domain_name="members.cj.com")
cookies = []
for c in cj:
    cookies.append({"name": c.name, "value": c.value, "domain": c.domain.lstrip("."), 
            "path": c.path or "/", "secure": bool(c.secure), "httpOnly": False})

# Also cj.com cookies
for domain in ["cj.com", "signin.cj.com"]:
    try:
        cj2 = browser_cookie3.firefox(cookie_file=cookie_file, domain_name=domain)
        existing = {(c['domain'], c['name']) for c in cookies}
        for c in cj2:
            d = c.domain.lstrip(".")
            if (d, c.name) not in existing:
                cookies.append({"name": c.name, "value": c.value, "domain": d,
                    "path": c.path or "/", "secure": bool(c.secure), "httpOnly": False})
    except:
        pass

print(f"Cookies extrahiert: {len(cookies)}")

# Import
resp = requests.post(f"{CAMOFOX}/sessions/{USER_ID}/cookies", json={"cookies": cookies}, timeout=15)
print(f"Import: {resp.json()}")

# Create tab -> go to account settings general
resp = requests.post(f"{CAMOFOX}/tabs", json={
    "userId": USER_ID,
    "sessionKey": "cj",
    "url": "https://members.cj.com/member/app/publisher/account/settings/general"
}, timeout=30)

tab_id = resp.json()["tabId"]
print(f"Tab ID: {tab_id}")

time.sleep(4)

# Click Edit button
snap = requests.get(f"{CAMOFOX}/tabs/{tab_id}/snapshot", params={"userId": USER_ID})
print(f"\n--- SNAPSHOT (Ausschnitt) ---")
lines = snap.text.split('\n')
for line in lines[:60]:
    print(line)

# Save tab_id
with open("/tmp/cj_tab2.txt", "w") as f:
    f.write(tab_id)
print(f"\nTab ID saved: {tab_id}")
