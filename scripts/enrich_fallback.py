#!/usr/bin/env python3
"""
Fallback enrich script — generates descriptions locally without external API.
Replicates the enrich_batch.py logic but uses template-based description generation.

Usage: python scripts/enrich_fallback.py --file scripts/batches/batch_081.json
"""
import json, os, sys, argparse, glob, re, time

DATA_DIR = os.path.join("F:", os.sep, "tiroltourismus", "src", "data", "unterkuenfte")

# German descriptive templates by type
TEMPLATES = {
    "hotel": [
        "Das <strong>{name}</strong> in {ort} bietet komfortable Gästezimmer und eine einladende Atmosphäre. Die zentrale Lage in {region} macht es zum idealen Ausgangspunkt für Ausflüge in die Tiroler Bergwelt.",
        "Im Herzen von {ort} gelegen, empfängt das <strong>{name}</strong> seine Gäste mit tiroler Gastfreundschaft. Die modern eingerichteten Zimmer und die ruhige Umgebung sorgen für einen erholsamen Aufenthalt.",
        "Das <strong>{name}</strong> in {ort} verbindet traditionellen Charme mit zeitgemäßem Komfort. Gäste genießen die entspannte Atmosphäre und die Nähe zu den schönsten Wanderwegen der Region.",
    ],
    "gasthof": [
        "Der <strong>{name}</strong> in {ort} ist ein traditioneller Gasthof mit gemütlichen Zimmern und regionaler Küche. Die urige Atmosphäre und die herzliche Gastfreundschaft machen den Aufenthalt zu einem besonderen Erlebnis.",
        "Der traditionsreiche <strong>{name}</strong> in {ort} bietet Gästen komfortable Unterkünfte und eine einladende Gaststube. Die Region {region} lädt zu Erkundungen ein.",
        "Im <strong>{name}</strong> in {ort} treffen Genuss und Erholung zusammen. Der Gasthof ist bekannt für seine tiroler Spezialitäten und die gemütlichen, liebevoll eingerichteten Gästezimmer.",
    ],
    "ferienwohnung": [
        "Die <strong>{name}</strong> in {ort} bietet eine gemütliche und voll ausgestattete Ferienwohnung für einen unbeschwerten Urlaub. Die ruhige Lage in {region} ist ideal für Familien und Paare.",
        "In der <strong>{name}</strong> in {ort} finden Gäste ein liebevoll eingerichtetes Zuhause auf Zeit. Die Ferienwohnung überzeugt durch ihre komfortable Ausstattung und die schöne Aussicht auf die Tiroler Alpen.",
        "Die <strong>{name}</strong> in {ort} ist die perfekte Unterkunft für einen erholsamen Urlaub in Tirol. Die gut ausgestattete Ferienwohnung liegt ruhig und dennoch zentral für Ausflüge in die Umgebung.",
    ],
    "ferienhaus": [
        "Das <strong>{name}</strong> in {ort} ist ein geräumiges Ferienhaus für Familien und Gruppen. Die Lage in {region} bietet einen herrlichen Blick auf die umliegende Berglandschaft und zahlreiche Freizeitmöglichkeiten.",
        "Das gemütliche <strong>{name}</strong> in {ort} bietet Platz für einen erholsamen Familienurlaub. Mit seiner großzügigen Ausstattung und dem Garten ist es der ideale Rückzugsort in den Tiroler Alpen.",
    ],
    "jugendherberge": [
        "Die <strong>{name}</strong> in {ort} ist eine moderne Jugendherberge mit preiswerten Übernachtungsmöglichkeiten. Die Lage in {region} ist ideal für Gruppenreisen, Schulklassen und junge Entdecker.",
    ],
    "camping": [
        "Der <strong>{name}</strong> in {ort} bietet Stellplätze für Wohnmobile und Zelte inmitten der Tiroler Natur. Die Anlage in {region} ist der ideale Ausgangspunkt für Outdoor-Aktivitäten und Familienabenteuer.",
        "Auf dem <strong>{name}</strong> in {ort} erleben Gäste Natur pur. Der gepflegte Campingplatz in {region} verfügt über moderne Sanitäranlagen und liegt nah an Wanderwegen und Badeseen.",
    ],
    "bauernhof": [
        "Der <strong>{name}</strong> in {ort} ist ein aktiver Bauernhof mit Gästezimmern und Ferienwohnungen. Urlaub auf dem Bauernhof in {region} bedeutet Natur, Tiere und tiroler Tradition für die ganze Familie.",
    ],
}

# Default fallback if type not matched
DEFAULT_TEMPLATES = [
    "Die Unterkunft <strong>{name}</strong> in {ort} begrüßt Gäste mit tiroler Gastfreundschaft. Die ruhige Lage in der Region {region} lädt zu erholsamen Tagen in den Bergen ein.",
]

TYP_LABEL = {
    "hotel": "Hotel", "gasthof": "Gasthof", "ferienwohnung": "Ferienwohnung",
    "ferienhaus": "Ferienhaus", "jugendherberge": "Jugendherberge",
    "camping": "Campingplatz", "bauernhof": "Bauernhof",
}

def generate_tags(name, typ, region):
    """Generate tags — same logic as enrich_batch.py"""
    tags = set()
    typ_tags = {
        "hotel": ["hotel", "übernachten"],
        "gasthof": ["gasthof", "kulinarik"],
        "ferienwohnung": ["ferienwohnung", "familie"],
        "ferienhaus": ["ferienhaus", "familie"],
        "jugendherberge": ["jugendherberge", "günstig"],
        "camping": ["camping", "outdoor", "familie"],
        "bauernhof": ["bauernhof", "urlaub-am-bauernhof", "familie"],
    }
    tags.update(typ_tags.get(typ, ["übernachten"]))
    # Add region if known
    if region:
        # Map regions to friendly tags
        region_map = {
            "innsbruck": "innsbruck-region",
            "ausserfern": "ausserfern",
            "kufstein": "kufstein",
            "kitzbuehel": "kitzbühel",
            "zillertal": "zillertal",
            "osttirol": "osttirol",
            "achensee": "achensee",
            "imst": "imst",
            "landeck": "landeck",
            "stubai": "stubaital",
        }
        if region in region_map:
            tags.add(region_map[region])
        else:
            tags.add(region)
    kw_map = {
        "wellness": ["wellness", "entspannung"], "spa": ["wellness", "entspannung"],
        "sauna": ["wellness", "sauna"], "pool": ["pool", "schwimmen"],
        "berg": ["berg", "wandern"], "alm": ["alm", "natur"],
        "ski": ["ski", "winter"], "sport": ["sport", "aktiv"],
        "golf": ["golf", "sport"], "see": ["see", "wasser"],
        "bio": ["bio", "nachhaltig"], "familie": ["familie", "kinder"],
        "romantik": ["romantik", "paare"], "design": ["design", "modern"],
        "schloss": ["schloss", "historisch"], "luxus": ["luxus", "premium"],
    }
    name_lower = name.lower()
    for kw, taglist in kw_map.items():
        if kw in name_lower:
            tags.update(taglist)
    return sorted(tags)[:6]

def generate_amenities(entry):
    """Derive amenities from name — same as enrich_batch.py"""
    name_lower = entry.get("name", "").lower()
    implied = set()
    if any(w in name_lower for w in ["wellness", "spa", "sauna"]):
        implied.add("sauna")
    if any(w in name_lower for w in ["pool", "bad", "schwimm"]):
        implied.add("pool")
    if any(w in name_lower for w in ["golf"]):
        implied.add("golfplatz")
    if any(w in name_lower for w in ["camping"]):
        implied.add("stromanschluss")
        implied.add("sanitäranlagen")
    return sorted(implied)

def generate_description_local(name, ort, typ, region):
    """Generate a description using templates (no external API)."""
    import random
    templates = TEMPLATES.get(typ, DEFAULT_TEMPLATES)
    template = random.choice(templates)
    ort_str = ort if ort else "Tirol"
    region_str = region if region else "Tirol"
    # Build the text
    text = template.format(name=name, ort=ort_str, region=region_str)
    # Wrap in <p> tags
    return f"<p>{text}</p>"

def process_batch_file(batch_path):
    """Process a single batch file."""
    batch_data = json.load(open(batch_path, encoding="utf-8"))
    print(f"Verarbeite {batch_path}: {len(batch_data)} Einträge")
    enriched = 0
    for item in batch_data:
        filepath = item["filepath"]
        if item.get("hat_beschreibung", True):
            print(f"  {item['name']}: bereits vorhanden ✅")
            continue
        if not os.path.exists(filepath):
            print(f"  {item['name']}: Datei nicht gefunden ❌")
            continue
        entry = json.load(open(filepath, encoding="utf-8"))
        print(f"  {item['name']} in {item.get('ort','?')}...", end=" ")
        # Generate description
        desc = generate_description_local(item["name"], item.get("ort", ""), item.get("typ", ""), item.get("region", ""))
        if desc:
            entry["beschreibung"] = desc
        # Tags
        if not entry.get("tags") or len(entry.get("tags", [])) < 2:
            new_tags = generate_tags(item["name"], item.get("typ", ""), item.get("region", ""))
            if new_tags:
                entry["tags"] = new_tags
        # Amenities
        if not entry.get("ausstattung"):
            entry["ausstattung"] = generate_amenities(entry)
        # Tier
        if not entry.get("tier"):
            entry["tier"] = "basic"
        # Write
        json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        enriched += 1
        print(f"✅")
        time.sleep(0.2)
    print(f"\n✅ {enriched} Einträge angereichert in {os.path.basename(batch_path)}")
    return enriched

def main():
    parser = argparse.ArgumentParser(description="Fallback Batch-Verarbeitung (lokal, kein API-Key nötig)")
    parser.add_argument("--file", required=True, help="Batch-JSON-Datei verarbeiten")
    args = parser.parse_args()
    process_batch_file(args.file)

if __name__ == "__main__":
    main()
