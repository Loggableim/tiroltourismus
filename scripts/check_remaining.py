#!/usr/bin/env python3
"""Quick script to check remaining NL gastro entries needing translation."""
import sys
sys.path.insert(0, 'scripts')
from translate_worker import get_remaining

remaining = get_remaining('gastro', 'nl')
print(f"Total remaining NL gastro entries: {len(remaining)}")
for r in remaining[:5]:
    print(f"  - {r}")
if len(remaining) > 5:
    print(f"  ... and {len(remaining)-5} more")
