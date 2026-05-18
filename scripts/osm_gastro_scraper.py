#!/usr/bin/env python3
"""
OSM Gastro Scraper for Tirol.
Fetches restaurants, cafes, pubs, bars, bistros, fast_food from OpenStreetMap via Overpass API.
Saves in src/data/gastro/{slug}/index.json format.
Target: 500+ real entries from OSM.

Usage:
    cd F:/tiroltourismus && python scripts/osm_gastro_scraper.py

Environment:
    OSM_OVERPASS_URL    - Overpass API endpoint (default: https://overpass-api.de/api/interpreter)
    OSM_TIMEOUT         - Per-query timeout in seconds (default: 180)
    OSM_SLEEP           - Sleep between region queries (default: 3)
    DRY_RUN             - If set, only show counts, don't write files
"""

import json
import os
import re
import sys
import time
import unicodedata
from collections import defaultdict

import requests

# ── Config ──────────────────────────────────────────────────────────────────

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GASTRO_DIR = os.path.join(PROJECT_DIR, "src", "data", "gastro")
ORTE_DIR = os.path.join(PROJECT_DIR, "src", "data", "orte")
OVERPASS_URL = os.environ.get("OSM_OVERPASS_URL", "https://overpass-api.de/api/interpreter")
OVERPASS_TIMEOUT = int(os.environ.get("OSM_TIMEOUT", "180"))
OVERPASS_QUERY_TIMEOUT = min(OVERPASS_TIMEOUT, 30)  # Must be < Apache's 60s gateway timeout
SLEEP_BETWEEN = int(os.environ.get("OSM_SLEEP", "3"))
DRY_RUN = bool(os.environ.get("DRY_RUN", ""))

# Tirol bounding box (generous, includes border areas)
TIROL_BBOX = (46.4, 10.1, 47.6, 12.9)  # south, west, north, east

# ── Tag mappings ────────────────────────────────────────────────────────────

AMENITY_KATEGORIE = {
    "restaurant": "restaurant",
    "cafe": "cafe",
    "pub": "pub",
    "bar": "bar",
    "bistro": "bistro",
    "fast_food": "imbiss",
    "food_court": "imbiss",
}

KATEGORIE_FARBE = {
    "restaurant": "#D32F2F",
    "cafe": "#8B4513",
    "pub": "#FF8F00",
    "bar": "#7B1FA2",
    "bistro": "#E65100",
    "imbiss": "#388E3C",
}

# Cuisine -> emoji (primary match wins, ordered by specificity)
CUISINE_EMOJI = {
    "pizza": "🍕", "pizzeria": "🍕",
    "italian": "🍝", "pasta": "🍝",
    "asian": "🍜", "chinese": "🥟", "japanese": "🍣", "sushi": "🍣",
    "indian": "🍛",
    "mexican": "🌮", "taco": "🌮",
    "german": "🥨", "austrian": "🥨", "tiroler": "🥨", "tirolean": "🥨",
    "regional": "🥨", "traditional": "🥨", "local": "🥨",
    "osterreichisch": "🥨",
    "seafood": "🦐", "fish": "🐟",
    "grill": "🥩", "steak": "🥩", "steak_house": "🥩",
    "burger": "🍔", "american": "🍔",
    "kebab": "🥙", "doner": "🥙", "döner": "🥙", "turkish": "🥙",
    "greek": "🥗",
    "vegan": "🥗", "vegetarian": "🥗", "healthy": "🥗",
    "ramen": "🍜", "noodle": "🍜",
    "curry": "🍛",
    "bread": "🥖", "bakery": "🥐", "cake": "🍰",
    "coffee": "☕", "coffee_shop": "☕",
    "ice_cream": "🍦", "ice": "🍦",
    "beer": "🍺", "brewery": "🍺",
    "wine": "🍷", "cocktail": "🍸",
    "farm": "🧀", "cheese": "🧀",
    "alp": "🌿", "mountain": "🏔️", "berg": "🏔️",
    "schnitzel": "🥩", "sausage": "🌭", "wurst": "🌭",
    "falafel": "🥙",
    "moroccan": "🥘", "thai": "🍜", "vietnamese": "🍜",
    "korean": "🥘", "spanish": "🥘", "tapas": "🥘",
    "french": "🥖", "swiss": "🧀",
    "gourmet": "🍽️", "international": "🍽️", "fusion": "🍽️",
    "balkan": "🥙", "lebanese": "🥙", "syrian": "🥙",
    "croatian": "🥘", "hungarian": "🥘",
    "mediterranean": "🥗",
    "sandwich": "🥪", "breakfast": "🥞", "brunch": "🥞",
    "pancake": "🥞", "crepe": "🥞", "waffle": "🧇",
    "donut": "🍩",
    "bbq": "🥩", "barbecue": "🥩", "chicken": "🍗",
    "organic": "🥗", "bio": "🥗",
    "halal": "🥙", "kosher": "🥙",
}

DEFAULT_EMOJI = "🍽️"


# ── Helpers ─────────────────────────────────────────────────────────────────

def slugify(text):
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def load_orte_mapping():
    """Load orte data and build mapping: name->region, slug->region, name->slug.
    Also pre-load coordinates for proximity matching."""
    name_to_region = {}
    slug_to_region = {}
    name_to_slug = {}
    all_orte_names = []
    orte_coords = {}  # name -> (lat, lng)

    if not os.path.isdir(ORTE_DIR):
        print(f"WARNING: orte directory not found at {ORTE_DIR}", file=sys.stderr)
        return name_to_region, slug_to_region, name_to_slug, all_orte_names, orte_coords

    for slug in sorted(os.listdir(ORTE_DIR)):
        fp = os.path.join(ORTE_DIR, slug, "index.json")
        if not os.path.isfile(fp):
            continue
        try:
            d = json.load(open(fp, encoding="utf-8"))
        except Exception as e:
            print(f"WARNING: Could not load {fp}: {e}", file=sys.stderr)
            continue
        name = d.get("name", "")
        region = d.get("region", "")
        name_lower = name.lower().strip()
        slug_lower = slug.lower().strip()
        name_to_region[name_lower] = region
        slug_to_region[slug_lower] = region
        name_to_slug[name] = slug
        all_orte_names.append(name)

        # Cache coordinates
        olat = d.get("koordinaten", {}).get("lat")
        olng = d.get("koordinaten", {}).get("lng")
        if olat is not None and olng is not None:
            orte_coords[name] = (float(olat), float(olng))

    return name_to_region, slug_to_region, name_to_slug, all_orte_names, orte_coords


def find_region_and_ort(tags, lat, lng, name_to_region, slug_to_region, name_to_slug, all_orte_names, orte_coords):
    """
    Determine the Tirol ort and region for a POI.
    Priority:
      1. addr:city / addr:place / addr:village / addr:town / addr:suburb
      2. is_in:city / is_in:town / is_in:village
      3. Reverse geocode: find nearest known ort within ~10km
    Returns (ort_name, region)
    """
    # Try OSM address tags
    city_candidates = []
    for key in ["addr:city", "addr:place", "addr:town", "addr:village", "addr:suburb",
                 "is_in:city", "is_in:town", "is_in:village"]:
        val = tags.get(key, "").strip()
        if val:
            city_candidates.append(val)

    for candidate in city_candidates:
        cl = candidate.lower().strip()
        if cl in name_to_region:
            region = name_to_region[cl]
            for fn, slug in name_to_slug.items():
                if fn.lower() == cl:
                    return fn, region
            return candidate, region
        # Try normalized match
        cleaned = re.sub(r"\s+", "", cl)
        for nl, region in name_to_region.items():
            if re.sub(r"\s+", "", nl) == cleaned:
                for fn, slug in name_to_slug.items():
                    if fn.lower() == nl:
                        return fn, region
                return nl, region

    # Fallback: proximity matching using pre-cached coordinates
    if lat is not None and lng is not None and orte_coords:
        best_dist = float("inf")
        best_ort = None
        best_region = None
        for ort_name, (olat, olng) in orte_coords.items():
            if ort_name not in name_to_slug:
                continue
            dist = ((olat - lat) ** 2 + (olng - lng) ** 2) ** 0.5
            if dist < best_dist:
                best_dist = dist
                best_ort = ort_name
                best_region = name_to_region.get(ort_name.lower(), "")

        if best_dist < 0.1 and best_ort:
            return best_ort, best_region

    return None, None


def get_emoji(tags):
    """Extract emoji from cuisine tag."""
    cuisine = tags.get("cuisine", "").lower().strip()
    if not cuisine:
        return DEFAULT_EMOJI
    cuisines = re.split(r"[;,/]", cuisine)
    for c in cuisines:
        c = c.strip().replace(" ", "_").replace("-", "_")
        if c in CUISINE_EMOJI:
            return CUISINE_EMOJI[c]
    return DEFAULT_EMOJI


def get_tags_list(tags, kategorie):
    """Build a list of tag keywords from available OSM tags."""
    result = [kategorie]
    cuisine = tags.get("cuisine", "").lower()
    if cuisine:
        for c in re.split(r"[;,/]", cuisine):
            c = c.strip().replace(" ", "_")
            if c and len(c) < 30:
                result.append(c)

    for dk in ["diet:vegan", "diet:vegetarian", "diet:gluten_free",
               "diet:lactose_free", "diet:halal", "diet:kosher"]:
        if tags.get(dk) in ("yes", "only"):
            result.append(dk.split(":")[1])

    if tags.get("takeaway") == "yes":
        result.append("takeaway")
    if tags.get("delivery") == "yes":
        result.append("lieferung")
    if tags.get("outdoor_seating") in ("yes", "terrace"):
        result.append("terrasse")
    if tags.get("internet_access") == "wlan" or tags.get("wifi") == "yes":
        result.append("wlan")

    seen = set()
    deduped = []
    for t in result:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped


def get_preis(tags):
    """Estimate price level from OSM tags."""
    charge = tags.get("charge", "")
    if charge:
        return charge
    level = tags.get("level", "")
    if level:
        try:
            n = int(level)
            return "€" * min(max(n, 1), 3)
        except ValueError:
            pass
    return "€"


# ── Overpass Queries ────────────────────────────────────────────────────────

def build_tirol_query(bbox=TIROL_BBOX, include_nodes=True, include_ways=False):
    """
    Build an Overpass QL query for all gastro POIs in Tirol using a bounding box.
    Single-line format (no newlines) to avoid Apache mod_security issues.
    
    Nodes-only query returns ~8000+ entries, which is sufficient for 500+ target.
    Way queries added for restaurant/cafe to catch any missing geometry types.
    """
    s, w, n, e = bbox
    node_types = ["restaurant", "cafe", "pub", "bar", "bistro", "fast_food"]

    parts = [f"[out:json][timeout:{OVERPASS_QUERY_TIMEOUT}];("]

    if include_nodes:
        for amenity in node_types:
            parts.append(f"node({s},{w},{n},{e})[amenity={amenity}];")

    if include_ways:
        # Only restaurant and cafe ways — adding all 6 way types causes gateway timeout
        for amenity in ["restaurant", "cafe"]:
            parts.append(f"way({s},{w},{n},{e})[amenity={amenity}];")

    parts.append(");out center body;")
    return "".join(parts)


def build_region_query(region_name, towns_in_region):
    """
    Build per-region queries as fallback.
    Uses the ort coordinates to build a loose bounding box for the region.
    """
    return None  # We'll use the single bbox query approach only


def run_query(query):
    """Execute an Overpass query and return the parsed JSON result."""
    print(f"  Overpass API ({len(query)} chars)...", end="", flush=True)
    try:
        import time as _time
        _t0 = _time.time()
        print(f"[sending...]", end="", flush=True)
        resp = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers={
                "User-Agent": "OverpassTurbo/1.0",
                "Accept": "application/json",
            },
            timeout=OVERPASS_TIMEOUT + 30,
        )
        _elapsed = _time.time() - _t0
        print(f"[{_elapsed:.1f}s]", end="", flush=True)
        # Read response content with a timeout on content reading
        content = resp.content
        print(f"[{len(content)}bytes]", end="", flush=True)
        if resp.status_code != 200:
            print(f" FAILED (HTTP {resp.status_code})")
            print(f"  Response: {resp.text[:500]}", file=sys.stderr)
            return None

        data = resp.json()
        print(f"[parsed]", end="", flush=True)
        elements = data.get("elements", [])
        print(f" OK ({len(elements)} elements)")
        return elements

    except requests.exceptions.Timeout:
        print(" TIMEOUT")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f" CONNECTION ERROR: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f" JSON ERROR: {e}")
        return None


def build_regions_from_orte(name_to_slug):
    """Build region->[town_names] mapping from orte data."""
    regions = defaultdict(list)
    for ort_name, slug in name_to_slug.items():
        fp = os.path.join(ORTE_DIR, slug, "index.json")
        if os.path.isfile(fp):
            d = json.load(open(fp, encoding="utf-8"))
            region = d.get("region", "")
            regions[region].append(ort_name)
    return dict(regions)


# ── Processing ──────────────────────────────────────────────────────────────

def process_element(el, name_to_region, slug_to_region, name_to_slug, all_orte_names, orte_coords):
    """Convert an OSM element to our gastro format. Returns dict or None."""
    tags = el.get("tags", {})
    if not tags:
        return None

    name = tags.get("name", "").strip()
    if not name:
        return None

    amenity = tags.get("amenity", "")
    kategorie = AMENITY_KATEGORIE.get(amenity, amenity)
    if not kategorie:
        return None

    lat = el.get("lat")
    lng = el.get("lon")
    if lat is None and "center" in el:
        lat = el["center"].get("lat")
        lng = el["center"].get("lon")
    if lat is None:
        return None

    ort, region = find_region_and_ort(tags, lat, lng, name_to_region, slug_to_region,
                                       name_to_slug, all_orte_names)
    if not ort or not region:
        return None

    base_slug = slugify(name)
    ort_slug = slugify(ort)
    slug = f"{base_slug}-{ort_slug}"
    slug = re.sub(r"-+", "-", slug)

    entry = {
        "name": name,
        "slug": slug,
        "region": region,
        "ort": ort,
        "kategorie": kategorie,
        "kurzbeschreibung": "",
        "beschreibung": "",
        "emoji": get_emoji(tags),
        "farbe": KATEGORIE_FARBE.get(kategorie, "#757575"),
        "adresse": format_address(tags),
        "telefon": tags.get("phone", tags.get("contact:phone", "")),
        "email": tags.get("email", tags.get("contact:email", "")),
        "webseite": tags.get("website", tags.get("contact:website", "")),
        "preis": get_preis(tags),
        "tags": get_tags_list(tags, kategorie),
        "status": "published",
        "koordinaten": {
            "lat": str(round(lat, 6)),
            "lng": str(round(lng, 6)),
        },
        "bilder": [],
        "hero_bild": None,
    }

    return entry


def format_address(tags):
    """Build an address string from OSM addr tags."""
    street = tags.get("addr:street", "")
    housenumber = tags.get("addr:housenumber", "")
    postcode = tags.get("addr:postcode", "")
    city = tags.get("addr:city", "")

    parts = []
    if street and housenumber:
        parts.append(f"{street} {housenumber}")
    elif street:
        parts.append(street)
    elif housenumber:
        parts.append(housenumber)
    if postcode:
        if city:
            parts.append(f"{postcode} {city}")
        else:
            parts.append(postcode)
    elif city:
        parts.append(city)
    return ", ".join(parts) if parts else ""


def write_gastro_entry(entry, dry_run=False):
    """Write a single gastro entry to disk."""
    slug = entry["slug"]
    dir_path = os.path.join(GASTRO_DIR, slug)
    file_path = os.path.join(dir_path, "index.json")
    if dry_run:
        return True
    os.makedirs(dir_path, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)
    return True


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("OSM Gastro Scraper für Tirol")
    print("=" * 60)

    # Load orte mapping
    print("\n📂 Lade Ortsdaten...")
    name_to_region, slug_to_region, name_to_slug, all_orte_names = load_orte_mapping()
    print(f"   {len(name_to_slug)} Orte geladen")

    # Check existing gastro entries
    existing_slugs = set()
    name_lower_to_slug = {}
    if os.path.isdir(GASTRO_DIR):
        for s in os.listdir(GASTRO_DIR):
            fp = os.path.join(GASTRO_DIR, s, "index.json")
            if os.path.isfile(fp):
                existing_slugs.add(s)
                try:
                    d = json.load(open(fp, encoding="utf-8"))
                    key = (d.get("name", "").lower(), d.get("ort", "").lower())
                    name_lower_to_slug[key] = s
                except Exception:
                    pass
    print(f"   {len(existing_slugs)} bestehende Gastro-Einträge")

    # Build regions
    regions = build_regions_from_orte(name_to_slug)
    print(f"\n🗺️  Regionen: {len(regions)}")
    for r in sorted(regions):
        print(f"   {r}: {len(regions[r])} Orte")

    # Run Overpass query (nodes first - gives ~8000+ entries)
    print(f"\n🔍 Führe Overpass-Query für Tirol aus (bbox)...")
    query = build_tirol_query(include_nodes=True, include_ways=False)
    elements = run_query(query)

    # Fallback: try with ways for restaurant/cafe if no results
    if not elements:
        print("\n⚠️  Versuche Query mit Ways...")
        query = build_tirol_query(include_nodes=True, include_ways=True)
        elements = run_query(query)

    if not elements:
        print("\n❌ Keine Daten von Overpass erhalten.")
        sys.exit(1)

    print(f"\n📊 {len(elements)} Elemente von Overpass erhalten")

    # Process elements
    print(f"\n🔄 Verarbeite Elemente...")
    new_entries = []
    stats = {
        "skipped_no_name": 0,
        "skipped_no_region": 0,
        "skipped_duplicate": 0,
        "skipped_error": 0,
    }

    for el in elements:
        try:
            entry = process_element(el, name_to_region, slug_to_region, name_to_slug, all_orte_names)
        except Exception as e:
            print(f"   Fehler bei Element {el.get('id', '?')}: {e}", file=sys.stderr)
            stats["skipped_error"] += 1
            continue

        if entry is None:
            tags = el.get("tags", {})
            if not tags.get("name", "").strip():
                stats["skipped_no_name"] += 1
            else:
                stats["skipped_no_region"] += 1
            continue

        # Check duplicate by (name, ort)
        key = (entry["name"].lower(), entry["ort"].lower())
        if key in name_lower_to_slug:
            stats["skipped_duplicate"] += 1
            continue

        # Handle slug collision
        if entry["slug"] in existing_slugs:
            counter = 2
            while f"{entry['slug']}-{counter}" in existing_slugs:
                counter += 1
            entry["slug"] = f"{entry['slug']}-{counter}"

        new_entries.append(entry)
        existing_slugs.add(entry["slug"])
        name_lower_to_slug[key] = entry["slug"]

    # Print results
    print(f"\n📊 Ergebnisse:")
    print(f"   Gesamt von OSM: {len(elements)}")
    print(f"   Kein Name: {stats['skipped_no_name']}")
    print(f"   Keine Tirol-Zuordnung: {stats['skipped_no_region']}")
    print(f"   Duplikate (bereits vorhanden): {stats['skipped_duplicate']}")
    print(f"   Fehler: {stats['skipped_error']}")
    print(f"   ➜ Neue Einträge: {len(new_entries)}")

    region_counts = defaultdict(int)
    kategorie_counts = defaultdict(int)
    for e in new_entries:
        region_counts[e["region"]] += 1
        kategorie_counts[e["kategorie"]] += 1

    print(f"\n📊 Neue Einträge nach Region:")
    for r in sorted(region_counts):
        print(f"   {r}: {region_counts[r]}")

    print(f"\n📊 Neue Einträge nach Kategorie:")
    for k in sorted(kategorie_counts):
        print(f"   {k}: {kategorie_counts[k]}")

    if DRY_RUN:
        print(f"\n🔸 DRY RUN - Keine Dateien geschrieben")
        return

    # Write entries
    print(f"\n💾 Schreibe {len(new_entries)} Einträge...")
    written = 0
    for entry in new_entries:
        try:
            write_gastro_entry(entry, dry_run=False)
            written += 1
        except Exception as e:
            print(f"   Fehler beim Schreiben von {entry['slug']}: {e}", file=sys.stderr)

    print(f"\n✅ Fertig! {written} neue Gastro-Einträge aus OSM gespeichert.")
    print(f"   Gesamt jetzt: {len(existing_slugs)} Einträge (inkl. bestehender)")

    # Save stats
    stats["total_from_osm"] = len(elements)
    stats["new_entries"] = len(new_entries)
    stats["total_after_merge"] = len(existing_slugs)
    stats["by_region"] = dict(region_counts)
    stats["by_kategorie"] = dict(kategorie_counts)
    stats["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    stats_path = os.path.join(PROJECT_DIR, "scripts", "osm_gastro_scraper_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"   Statistiken: {stats_path}")


if __name__ == "__main__":
    main()
