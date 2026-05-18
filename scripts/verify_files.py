#!/usr/bin/env python3
"""Verify files for processed batches"""
import json, os

# Check specific files
test_files = [
    "5-sterne-camping-zugspitz-resort/index.json",
    "achensee-camping-schwarzenau/index.json",
    "activehotel-bergkonig/index.json",
    "aktiv-camping-imst/index.json",
    "aktiv-camping-prutz/index.json",
    "aktivhotel-crystal/index.json",
    "aktivhotel-hochfilzer/index.json",
    "all-suite-resorts-paznaun/index.json",
    "alpencamp-siegsdorf/index.json",
]

base = "src/data/unterkuenfte"
for f in test_files:
    full = f"{base}/{f}"
    exists = os.path.exists(full)
    if exists:
        data = json.load(open(full, encoding="utf-8"))
        desc = data.get("beschreibung", "")
        print(f"  {f:50s} ✅ ({len(desc):3d} chars)")
    else:
        print(f"  {f:50s} ❌ MISSING")
