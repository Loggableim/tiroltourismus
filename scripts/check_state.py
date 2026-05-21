#!/usr/bin/env python3
"""Check current unterkunft state."""
import json, os, glob
current = glob.glob('src/data/unterkuenfte/*/index.json')
backup = glob.glob('src/data/unterkuenfte_backup/*/index.json')
print(f'Current: {len(current)} entries')
print(f'Backup: {len(backup)} entries')
with_region = 0
for f in current:
    d = json.load(open(f))
    if d.get('region'):
        with_region += 1
print(f'With region: {with_region}/{len(current)}')
