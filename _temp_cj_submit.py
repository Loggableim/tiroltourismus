#!/usr/bin/env python3
"""Toggle CJ promotional property checkboxes and submit"""
import requests, json, time

CAMOFOX = "http://localhost:9377"
TAB_ID = "cfc8f0c1-5672-41a9-b85f-9963c39d0f29"
USER_ID = "cj4"

# First, find all checkboxes and their labels
r = requests.post(f"{CAMOFOX}/tabs/{TAB_ID}/evaluate", json={
    "userId": USER_ID,
    "expression": "Array.from(document.querySelectorAll('[type=checkbox]')).map((cb,i) => ({idx:i, checked:cb.checked, name:cb.getAttribute('name'), label:(cb.closest('label')||{}).innerText||cb.parentElement.innerText||'none'})).filter(x => x.name && x.name.includes('promotional'))"
})
print("Checkboxes:", json.dumps(r.json(), indent=2))

# Toggle Content/Blog/Medien
r2 = requests.post(f"{CAMOFOX}/tabs/{TAB_ID}/evaluate", json={
    "userId": USER_ID,
    "expression": "var cbs = document.querySelectorAll('[type=checkbox]'); for(var i=0; i<cbs.length; i++) { var cb = cbs[i]; var name = cb.getAttribute('name') || ''; var parentText = (cb.closest('label')||{}).innerText || ''; if(name.includes('CONTENT_BLOG') || parentText.includes('Content/Blog')) { cb.checked = true; cb.dispatchEvent(new Event('change', {bubbles:true})); 'TOGGLED Content/Blog: ' + parentText.slice(0,40); break; } } 'done'"
})
print("Toggle Content/Blog:", r2.json())

# Toggle IS_PRIMARY
r3 = requests.post(f"{CAMOFOX}/tabs/{TAB_ID}/evaluate", json={
    "userId": USER_ID,
    "expression": "var cbs = document.querySelectorAll('[type=checkbox]'); for(var i=0; i<cbs.length; i++) { var cb = cbs[i]; var name = cb.getAttribute('name') || ''; var parentText = (cb.closest('label')||{}).innerText || ''; if(name.includes('IS_PRIMARY') || parentText.includes('primäre')) { cb.checked = true; cb.dispatchEvent(new Event('change', {bubbles:true})); 'TOGGLED Primary: ' + parentText.slice(0,40); break; } } 'done'"
})
print("Toggle Primary:", r3.json())

time.sleep(1)

# Submit
r4 = requests.post(f"{CAMOFOX}/tabs/{TAB_ID}/click", json={
    "userId": USER_ID, "ref": "e12"
}, timeout=20)
print("Submit:", r4.json())

time.sleep(4)

# Check result
snap = requests.get(f"{CAMOFOX}/tabs/{TAB_ID}/snapshot", params={"userId": USER_ID})
data = snap.json()
print("URL:", data.get("url"))
snap_text = data.get("snapshot", "")
print("Page preview:", snap_text[:800])
