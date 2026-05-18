"""Check progress of both batch processes."""
import json, os

for coll in ["unterkuenfte", "camping"]:
    pf = f"F:/tiroltourismus/scripts/.progress_{coll}.json"
    if os.path.exists(pf):
        d = json.load(open(pf))
        print(f"{coll}: {len(d)} entries processed")
    else:
        print(f"{coll}: no progress file yet")
