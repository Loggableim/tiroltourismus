"""Detailed progress check."""
import json, os, time

for coll in ["unterkuenfte", "camping"]:
    pf = f"F:/tiroltourismus/scripts/.progress_{coll}.json"
    if os.path.exists(pf):
        d = json.load(open(pf))
        mod_time = os.path.getmtime(pf)
        last_updated = time.strftime('%H:%M:%S', time.localtime(mod_time))
        print(f"{coll}: {len(d)} entries (last update: {last_updated})")
        if len(d) >= 3:
            print(f"  Last 3: {d[-3:]}")
    else:
        print(f"{coll}: no progress file")
