#!/usr/bin/env python3
"""Test Overpass API with different approaches."""
import requests
import json
import sys

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
query = '[out:json][timeout:30];area(3600167846)->.searchArea;node["amenity"="cafe"](area.searchArea);out body 5;'

approaches = [
    ("POST form-encoded", {"data": {"data": query}}),
    ("POST Accept json", {"data": {"data": query}, "headers": {"Accept": "application/json"}}),
    ("POST no Accept", {"data": {"data": query}, "headers": {"Accept": None}}),
    ("GET with params", {"method": "GET", "params": {"data": query}}),
    ("POST body raw", {"data": query, "headers": {"Content-Type": "text/plain"}}),
    ("POST body json", {"data": query, "headers": {"Content-Type": "application/json"}}),
]

for name, kwargs in approaches:
    try:
        method = kwargs.pop("method", "POST")
        headers = kwargs.pop("headers", {})
        headers.setdefault("User-Agent", "TirolTourismus/1.0")
        # Clean None values
        headers = {k: v for k, v in headers.items() if v is not None}

        if method == "GET":
            resp = requests.get(OVERPASS_URL, **kwargs, headers=headers, timeout=30)
        else:
            resp = requests.post(OVERPASS_URL, **kwargs, headers=headers, timeout=30)

        print(f"[{name}] HTTP {resp.status_code}")
        text = resp.text[:200].replace('\n', '\\n')
        print(f"  Response: {text}")
    except Exception as e:
        print(f"[{name}] Error: {e}")
