"""
T4: JSON-Schema Validierung + Data Quality Report
Prueft alle Collections auf Daten-Integritaet
"""
import json, os, sys

PROJECT = r"F:\tiroltourismus"
DATA = os.path.join(PROJECT, "src", "data")
REPORT = os.path.join(DATA, "_quality_report.json")

COLLECTIONS = ["orte", "unterkuenfte", "erlebnisse", "gastro", "events", "regionen", "sehenswuerdigkeiten", "camping"]

REQUIRED_FIELDS = {
    "orte": ["name", "slug", "region", "kurzbeschreibung", "koordinaten"],
    "unterkuenfte": ["name", "slug", "typ", "ort", "region", "beschreibung", "koordinaten"],
    "erlebnisse": ["name", "slug", "kategorie", "ort", "region", "beschreibung", "koordinaten"],
    "gastro": ["name", "slug", "ort", "region", "koordinaten"],
    "events": ["name", "slug", "kategorie", "ort", "region", "beschreibung", "koordinaten"],
    "regionen": ["name", "slug", "kurzbeschreibung", "koordinaten"],
    "sehenswuerdigkeiten": ["name", "slug", "ort", "region", "beschreibung", "koordinaten"],
    "camping": ["name", "slug", "ort", "region", "beschreibung", "koordinaten"],
}

issues = []
stats = {}

for coll in COLLECTIONS:
    coll_dir = os.path.join(DATA, coll)
    if not os.path.isdir(coll_dir):
        stats[coll] = {"status": "NOT_FOUND"}
        issues.append({"collection": coll, "slug": "", "field": "", "severity": "critical",
                       "msg": f"Collection directory not found: {coll_dir}"})
        continue
    
    entries = [d for d in os.listdir(coll_dir) 
               if os.path.isdir(os.path.join(coll_dir, d)) and not d.startswith("_")]
    
    coll_issues = 0
    required = REQUIRED_FIELDS.get(coll, ["name", "slug"])
    
    all_slugs = set()
    broken_refs_orte = 0
    broken_refs_region = 0
    empty_coords = 0
    empty_images = 0
    missing_fields = 0
    
    for slug in entries:
        idx_path = os.path.join(coll_dir, slug, "index.json")
        if not os.path.exists(idx_path):
            issues.append({"collection": coll, "slug": slug, "field": "index.json", "severity": "critical",
                           "msg": f"Missing index.json"})
            coll_issues += 1
            continue
        
        try:
            data = json.load(open(idx_path, encoding="utf-8"))
        except Exception as e:
            err_msg = "Invalid JSON: " + str(e)[:100]
            issues.append({"collection": coll, "slug": slug, "field": "index.json", "severity": "critical",
                           "msg": err_msg})
            coll_issues += 1
            continue
        
        # Required fields
        for field in required:
            if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
                issues.append({"collection": coll, "slug": slug, "field": field, "severity": "error",
                               "msg": f"Missing required field: {field}"})
                missing_fields += 1
        
        # Koordinaten
        coords = data.get("koordinaten", {})
        if isinstance(coords, dict):
            lat = coords.get("lat") or coords.get("latitude") or coords.get("lat")
            lng = coords.get("lng") or coords.get("longitude") or coords.get("lon")
            if not lat or not lng:
                issues.append({"collection": coll, "slug": slug, "field": "koordinaten", "severity": "warning",
                               "msg": f"Missing or empty coordinates"})
                empty_coords += 1
            else:
                try:
                    if not (46.0 <= float(lat) <= 48.0) or not (9.0 <= float(lng) <= 13.0):
                        issues.append({"collection": coll, "slug": slug, "field": "koordinaten", "severity": "warning",
                                       "msg": f"Coordinates outside Tirol: lat={lat}, lng={lng}"})
                except:
                    pass
        
        # Bilder
        bilder = data.get("bilder", [])
        if isinstance(bilder, list) and len(bilder) == 0:
            issues.append({"collection": coll, "slug": slug, "field": "bilder", "severity": "info",
                           "msg": f"Empty bilder array"})
            empty_images += 1
        
        # Duplikat-Prüfung
        if slug in all_slugs:
            issues.append({"collection": coll, "slug": slug, "field": "slug", "severity": "error",
                           "msg": f"Duplicate slug within collection"})
        all_slugs.add(slug)
        
        # Beschreibungs-Länge
        desc = data.get("beschreibung", "") or data.get("kurzbeschreibung", "") or ""
        if desc and len(desc) < 50:
            issues.append({"collection": coll, "slug": slug, "field": "beschreibung", "severity": "info",
                           "msg": f"Very short description ({len(desc)} chars)"})
        
        cross_ref_ort = data.get("ort", "")
        cross_ref_region = data.get("region", "")
        
    # Cross-Collection Referenzen
    stats[coll] = {
        "entries": len(entries),
        "issues": coll_issues,
        "missing_fields": missing_fields,
        "empty_coords": empty_coords,
        "empty_images": empty_images,
    }

# Cross-Collection: welche orte existieren tatsaechlich?
orte_slugs = set()
orte_dir = os.path.join(DATA, "orte")
if os.path.isdir(orte_dir):
    orte_slugs = {d for d in os.listdir(orte_dir) if os.path.isdir(os.path.join(orte_dir, d))}

region_slugs = set()
region_dir = os.path.join(DATA, "regionen")
if os.path.isdir(region_dir):
    region_slugs = {d for d in os.listdir(region_dir) if os.path.isdir(os.path.join(region_dir, d))}

for coll in COLLECTIONS:
    if coll in ("orte", "regionen"):
        continue
    coll_dir = os.path.join(DATA, coll)
    if not os.path.isdir(coll_dir):
        continue
    for slug in os.listdir(coll_dir):
        idx_path = os.path.join(coll_dir, slug, "index.json")
        if not os.path.exists(idx_path):
            continue
        try:
            data = json.load(open(idx_path, encoding="utf-8"))
        except:
            continue
        ref_ort = data.get("ort", "")
        if ref_ort and ref_ort not in orte_slugs:
            issues.append({"collection": coll, "slug": slug, "field": "ort", "severity": "error",
                           "msg": f"Cross-ref to non-existent ort: '{ref_ort}'"})
        ref_region = data.get("region", "")
        if ref_region and ref_region not in region_slugs:
            issues.append({"collection": coll, "slug": slug, "field": "region", "severity": "error",
                           "msg": f"Cross-ref to non-existent region: '{ref_region}'"})

# Report schreiben
report = {
    "generated_at": __import__("datetime").datetime.now().isoformat(),
    "total_issues": len(issues),
    "by_severity": {},
    "stats": stats,
    "issues": issues,
}

for iss in issues:
    sev = iss["severity"]
    report["by_severity"][sev] = report["by_severity"].get(sev, 0) + 1

json.dump(report, open(REPORT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

print(f"=== QUALITY REPORT ===")
print(f"Total Issues: {report['total_issues']}")
print(f"  critical: {report['by_severity'].get('critical',0)}")
print(f"  error:    {report['by_severity'].get('error',0)}")
print(f"  warning:  {report['by_severity'].get('warning',0)}")
print(f"  info:     {report['by_severity'].get('info',0)}")
print()
for coll, s in stats.items():
    if isinstance(s, dict):
        print(f"{coll:20s}: {s.get('entries',0):5d} entries | issues: {s.get('issues',0):3d} | missing: {s.get('missing_fields',0):3d} | no-coords: {s.get('empty_coords',0):3d}")
print(f"\nReport saved to: {REPORT}")

# Auch als Task-Ergebnis
print(f"\nSUMMARY: {report['total_issues']} issues found across {len(stats)} collections")
