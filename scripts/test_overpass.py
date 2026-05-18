#!/usr/bin/env python3
"""Test Overpass API connectivity."""
import requests
import json

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Simple query: 5 restaurants in Innsbruck
query = """
[out:json][timeout:30];
area["name"="Innsbruck"]["admin_level"="8"]->.searchArea;
node["amenity"="restaurant"](area.searchArea);
out body 5;
"""

print("Test 1: Basic POST with data param")
try:
    resp = requests.post(
        OVERPASS_URL,
        data={"data": query},
        headers={"User-Agent": "TirolTourismus/1.0"},
        timeout=30,
    )
    print(f"  Status: {resp.status_code}")
    print(f"  Headers: {dict(resp.headers)}")
    print(f"  Body (first 300): {resp.text[:300]}")
except Exception as e:
    print(f"  Error: {e}")

print()
print("Test 2: GET request")
try:
    import urllib.parse
    encoded = urllib.parse.quote(query)
    resp = requests.get(
        f"{OVERPASS_URL}?data={encoded}",
        headers={"User-Agent": "TirolTourismus/1.0"},
        timeout=30,
    )
    print(f"  Status: {resp.status_code}")
    print(f"  Body (first 300): {resp.text[:300]}")
except Exception as e:
    print(f"  Error: {e}")

print()
print("Test 3: POST with Accept header")
try:
    resp = requests.post(
        OVERPASS_URL,
        data={"data": query},
        headers={
            "User-Agent": "TirolTourismus/1.0",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=30,
    )
    print(f"  Status: {resp.status_code}")
    print(f"  Body (first 300): {resp.text[:300]}")
except Exception as e:
    print(f"  Error: {e}")
