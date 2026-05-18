#!/usr/bin/env python3
"""Append a description to an accommodation index.json file."""
import json, sys

filepath = sys.argv[1]
description = sys.argv[2]
entry = json.load(open(filepath, encoding="utf-8"))
entry["beschreibung"] = description

# Ensure tags
if not entry.get("tags") or len(entry.get("tags", [])) < 2:
    typ = entry.get("typ", "")
    typ_tags = {
        "hotel": ["hotel", "übernachten"],
        "gasthof": ["gasthof", "kulinarik"],
        "ferienwohnung": ["ferienwohnung", "familie"],
        "ferienhaus": ["ferienhaus", "familie"],
        "jugendherberge": ["jugendherberge", "günstig"],
        "camping": ["camping", "outdoor", "familie"],
        "bauernhof": ["bauernhof", "urlaub-am-bauernhof", "familie"],
    }
    tags = set(typ_tags.get(typ, ["übernachten"]))
    entry["tags"] = sorted(tags)[:6]

if not entry.get("ausstattung"):
    entry["ausstattung"] = []

if not entry.get("tier"):
    entry["tier"] = "basic"

json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"✅ {filepath} updated")
