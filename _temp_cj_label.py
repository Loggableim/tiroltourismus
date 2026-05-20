#!/usr/bin/env python3
"""Click checkbox labels directly for React SPA compatibility"""
import requests, json, time

CAMOFOX = "http://localhost:9377"
TAB_ID = "cfc8f0c1-5672-41a9-b85f-9963c39d0f29"
USER_ID = "cj4"

# Find the label element that wraps the Content/Blog/Medien checkbox and click it
r = requests.post(f"{CAMOFOX}/tabs/{TAB_ID}/evaluate", json={
    "userId": USER_ID,
    "expression": """
var cbs = document.querySelectorAll('[type=checkbox]');
for(var i=0; i<cbs.length; i++) {
    var cb = cbs[i];
    var label = cb.closest('label');
    var name = cb.getAttribute('name') || '';
    if(name.includes('CONTENT_BLOG') && label) {
        label.click();
        'CLICKED label: ' + (label.innerText || '').slice(0,50);
        break;
    }
}
'done'
"""
})
print("Label click Content/Blog:", r.json())

# Find and click the IS_PRIMARY label
r2 = requests.post(f"{CAMOFOX}/tabs/{TAB_ID}/evaluate", json={
    "userId": USER_ID,
    "expression": """
var cbs = document.querySelectorAll('[type=checkbox]');
for(var i=0; i<cbs.length; i++) {
    var cb = cbs[i];
    var label = cb.closest('label');
    var name = cb.getAttribute('name') || '';
    if(name.includes('IS_PRIMARY') && label) {
        label.click();
        'CLICKED label: ' + (label.innerText || '').slice(0,50);
        break;
    }
}
'done'
"""
})
print("Label click Primary:", r2.json())

time.sleep(1)

# Re-check state
r3 = requests.post(f"{CAMOFOX}/tabs/{TAB_ID}/evaluate", json={
    "userId": USER_ID,
    "expression": "Array.from(document.querySelectorAll('[type=checkbox]')).filter(cb => {var n=cb.getAttribute('name')||''; return n.includes('CONTENT_BLOG') || n.includes('IS_PRIMARY')}).map(cb => ({name: cb.getAttribute('name'), checked: cb.checked}))"
})
print("After click:", json.dumps(r3.json(), indent=2))

# Try submit again
time.sleep(1)
r4 = requests.post(f"{CAMOFOX}/tabs/{TAB_ID}/click", json={
    "userId": USER_ID, "ref": "e12"
}, timeout=20)
print("Submit:", r4.json())

time.sleep(4)
snap = requests.get(f"{CAMOFOX}/tabs/{TAB_ID}/snapshot", params={"userId": USER_ID})
data = snap.json()
print("URL:", data.get("url"))
text = data.get("snapshot", "")
if "Änderung vorgenommen werden" in text:
    idx = text.find("Änderung")
    print("Error:", text[idx:idx+300])
else:
    # Check for success - looking for the create button again or table
    idx = text.find("Werbeplattform")
    if idx >= 0:
        print(text[max(0,idx-100):idx+400])
    else:
        print(text[:1000])
