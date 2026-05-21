#!/usr/bin/env python3
import os
print(f"OPENCODE_GO_API_KEY: length={len(os.environ.get('OPENCODE_GO_API_KEY', ''))}")
print(f"OPENCODE_GO_API_KEY: '{os.environ.get('OPENCODE_GO_API_KEY', 'NOT SET')[:10]}...'")
# Also check if there's a way to read from hermes config
import json
config_path = os.path.expanduser("E:/HermesPortable/home/config.yaml")
print(f"Config exists: {os.path.exists(config_path)}")
