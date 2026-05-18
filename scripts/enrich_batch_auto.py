#!/usr/bin/env python3
"""
enrich_batch_auto.py — Erzeugt Beschreibungen für Unterkünfte OHNE externen API-Call.

Liest Batch-Datei, generiert für jeden Eintrag eine passende Beschreibung
basierend auf Name, Ort, Typ, Region. Verwendet Template-Logik statt API.
"""
import json, os, sys, time, re, glob

# ——— Konstanten ———
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "src", "data", "unterkuenfte")

TYP_LABELS = {
    "hotel": "Hotel",
    "gasthof": "Gasthof",
    "ferienwohnung": "Ferienwohnung",
    "ferienhaus": "Ferienhaus",
    "jugendherberge": "Jugendherberge",
    "camping": "Campingplatz",
    "bauernhof": "Bauernhof",
}

REGION_NAMES = {
    "arlberg": "St. Anton am Arlberg",
    "ausserfern": "Außerfern",
    "achensee": "Achensee",
    "imst": "Imst",
    "innsbruck": "Innsbruck",
    "kitzbuehel": "Kitzbüheler Alpen",
    "kufstein": "Kufsteinerland",
    "landeck": "Landeck",
    "osttirol": "Osttirol",
    "schwaz": "Schwaz / Silberregion",
    "stubai": "Stubaital",
    "solden": "Sölden / Ötztal",
    "sillian": "Sillian / Hochpustertal",
    "zillertal": "Zillertal",
    "seefeld": "Seefeld",
    "kaunertal": "Kaunertal",
    "pitztal": "Pitztal",
    "lechtal": "Lechtal",
}

LANDSCAPE_WORDS = {
    "berg": ["Bergpanorama", "alpine Umgebung", "Bergwelt"],
    "alm": ["Almlandschaft", "sanfte Hügel", "Almwiesen"],
    "see": ["Seeblick", "Uferlage", "Seenähe"],
    "fluss": ["Flusslandschaft", "Wasserlage"],
    "tal": ["Tallage", "Talbecken"],
    "hoch": ["Höhenlage", "Hochplateau"],
    "dorf": ["Dorfzentrum", "Ortskern"],
    "ruhig": ["Ruhelage", "ruhige Umgebung"],
    "zentrum": ["Zentrumsnähe", "Stadtlage"],
    "garten": ["Gartenanlage", "Grünanlage"],
    "wald": ["Waldrand", "Waldnähe"],
    "sport": ["Sportanlagen", "Aktivurlaub"],
}

KW_TAGS = {
    "wellness": ["wellness", "entspannung"], "spa": ["wellness", "entspannung"],
    "sauna": ["wellness", "sauna"], "pool": ["pool", "schwimmen"],
    "berg": ["berg", "wandern"], "alm": ["alm", "natur"],
    "ski": ["ski", "winter"], "sport": ["sport", "aktiv"],
    "golf": ["golf", "sport"], "see": ["see", "wasser"],
    "bio": ["bio", "nachhaltig"], "familie": ["familie", "kinder"],
    "romantik": ["romantik", "paare"], "design": ["design", "modern"],
    "schloss": ["schloss", "historisch"], "luxus": ["luxus", "premium"],
    "camping": ["camping", "outdoor", "familie", "natur"],
    "bauernhof": ["bauernhof", "urlaub-am-bauernhof", "natur", "familie"],
    "nationalpark": ["nationalpark", "natur", "wandern"],
    "natur": ["natur", "erholung"],
    "gasthof": ["gasthof", "kulinarik", "tradition"],
}

TYP_TAGS = {
    "hotel": ["hotel", "übernachten"],
    "gasthof": ["gasthof", "kulinarik"],
    "ferienwohnung": ["ferienwohnung", "familie"],
    "ferienhaus": ["ferienhaus", "familie"],
    "jugendherberge": ["jugendherberge", "günstig"],
    "camping": ["camping", "outdoor", "familie"],
    "bauernhof": ["bauernhof", "urlaub-am-bauernhof", "familie"],
}

# ——— Beschreibungs-Generator ———

def pick(items):
    """Pick first non-empty from items."""
    for item in items:
        if item:
            return item
    return items[-1]

def generate_description(name, ort, typ, region):
    """Erzeuge eine natürliche Beschreibung ohne API."""
    typ_label = TYP_LABELS.get(typ, typ)
    ort_name = ort if ort else "Tirol"
    region_name = REGION_NAMES.get(region, region if region else "Tirol")
    
    name_lower = name.lower()
    
    # — Lage-Phrase —
    location_parts = []
    
    # Ort
    if ort:
        location_parts.append(f"in {ort}")
    
    # See- / Berg- / Tal-Nähe
    if any(w in name_lower for w in ["see", "meer", "teich"]):
        location_parts.append("direkt am See gelegen")
    if any(w in name_lower for w in ["berg", "alm", "gipfel"]):
        location_parts.append("inmitten der Bergkulisse")
    if any(w in name_lower for w in ["tal", "grund"]):
        location_parts.append("im Tal gelegen")
    if "wald" in name_lower:
        location_parts.append("am Waldrand")
    if "dorf" in name_lower:
        location_parts.append("im Ortskern")
    if "hof" in name_lower and "bauernhof" not in name_lower:
        location_parts.append("in ländlicher Umgebung")
    if "park" in name_lower:
        location_parts.append("in ruhiger Parklage")
    if any(w in name_lower for w in ["zentrum", "mitte", "stadt"]):
        location_parts.append("zentral gelegen")
    
    if not location_parts:
        location_parts.append(pick([
            f"in der Region {region_name}" if region else None,
            "in ruhiger Lage",
            "inmitten der Tiroler Alpen",
        ]))
    
    location_str = ", ".join(location_parts)
    
    # — Atmosphäre —
    atmos_parts = []
    
    if typ == "camping":
        if "bauernhof" in name_lower:
            atmos_parts.append("Camping- und Bauernhoferlebnis mit naturnahem Charakter")
        elif "nationalpark" in name_lower:
            atmos_parts.append("Nationalpark-Camping mit einzigartiger Naturkulisse")
        else:
            atmos_parts.append("Campingplatz mit naturnahem Charakter")
    elif typ == "bauernhof":
        atmos_parts.append("Bauernhof mit traditionellem Charme")
    elif typ == "ferienwohnung" or typ == "ferienhaus":
        atmos_parts.append("komfortable Unterkunft für Erholungssuchende")
    elif typ == "hotel":
        atmos_parts.append("Hotel mit persönlichem Service")
    elif typ == "gasthof":
        atmos_parts.append("traditioneller Gasthof mit Tiroler Gastlichkeit")
    elif typ == "jugendherberge":
        atmos_parts.append("günstige Unterkunft für Gruppen und Individualreisende")
    
    # — Aktivitäten-Hinweis —
    aktiv_parts = []
    if any(w in name_lower for w in ["wandern", "berg"]):
        aktiv_parts.append("Wanderungen in die umliegende Bergwelt")
    if any(w in name_lower for w in ["ski", "winter"]):
        aktiv_parts.append("Skifahren und Wintersportmöglichkeiten")
    if any(w in name_lower for w in ["see", "bad", "schwimm"]):
        aktiv_parts.append("Wassersport und Badespaß")
    if any(w in name_lower for w in ["rad", "bike", "mountainbike"]):
        aktiv_parts.append("Rad- und Mountainbiketouren")
    if any(w in name_lower for w in ["golf"]):
        aktiv_parts.append("Golfanlagen in der Umgebung")
    if any(w in name_lower for w in ["familie", "kinder"]):
        aktiv_parts.append("familienfreundliche Umgebung mit Kinderangeboten")
    
    if not aktiv_parts:
        aktiv_parts.append("vielseitige Freizeitmöglichkeiten in der Umgebung")
    
    aktiv_str = "; ".join(aktiv_parts)
    
    # — Highlight —
    highlight = ""
    if "nationalpark" in name_lower:
        highlight = "Die einzigartige Naturkulisse des Nationalparks prägt das Erlebnis."
    elif "natur" in name_lower and "camping" in name_lower:
        highlight = "Natur pur und Erholung abseits des Trubels stehen hier im Vordergrund."
    elif "bio" in name_lower:
        highlight = "Nachhaltigkeit und biologische Produkte werden hier großgeschrieben."
    
    # — Bauen —
    paragraphs = []
    
    p1 = f"<strong>{name}</strong> liegt {location_str}."
    if atmos_parts:
        # Avoid redundant "Campingplatz-Unterkunft bietet Campingplatz..."
        typ_prefix = typ_label if typ_label not in atmos_parts[0] else ""
        if typ_prefix:
            p1 += f" Die {typ_prefix}-Unterkunft bietet {atmos_parts[0]}."
        else:
            p1 += f" Der {atmos_parts[0]}."
    else:
        p1 += f"."
    
    p2 = f"Gäste erwarten {aktiv_str}."
    
    if highlight:
        p3 = highlight
        paragraphs.append(f"<p>{p1} {p2} {p3}</p>")
    else:
        paragraphs.append(f"<p>{p1} {p2}</p>")
    
    return " ".join(paragraphs)


def generate_tags(name, typ, region):
    tags = set()
    tags.update(TYP_TAGS.get(typ, ["übernachten"]))
    name_lower = name.lower()
    for kw, taglist in KW_TAGS.items():
        if kw in name_lower:
            tags.update(taglist)
    # If it's camping but name mentions bauernhof, add bauernhof tags
    if typ == "camping" and "bauernhof" in name_lower:
        tags.update(["bauernhof", "urlaub-am-bauernhof"])
    if region:
        tags.add(region)
    return sorted(tags)[:6]


def generate_amenities(entry):
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
    if any(w in name_lower for w in ["bauernhof"]):
        implied.add("frühstück")
    if any(w in name_lower for w in ["hotel", "gasthof"]):
        implied.add("frühstück")
    return sorted(implied)


# ——— Hauptprogramm ———

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Batch-Verarbeitung (lokale Generierung)")
    parser.add_argument("--file", required=True, help="Batch-JSON-Datei")
    args = parser.parse_args()

    batch_data = json.load(open(args.file, encoding="utf-8"))
    print(f"Verarbeite {args.file}: {len(batch_data)} Einträge")
    
    enriched = 0
    for item in batch_data:
        name = item["name"]
        filepath = item["filepath"]
        hat = item["hat_beschreibung"]
        already = "bereits vorhanden ✅" if hat else ""
        
        if hat:
            print(f"  {name}: {already}")
            continue
        
        if not os.path.exists(filepath):
            print(f"  {name}: Datei nicht gefunden ❌")
            continue
        
        entry = json.load(open(filepath, encoding="utf-8"))
        
        print(f"  {name} in {item['ort'] or '?'}...", end=" ", flush=True)
        
        # Beschreibung generieren
        desc = generate_description(name, item["ort"], item["typ"], item["region"])
        if desc:
            entry["beschreibung"] = desc
        
        # Tags
        if not entry.get("tags") or len(entry.get("tags", [])) < 2:
            entry["tags"] = generate_tags(name, item["typ"], item["region"])
        
        # Ausstattung
        if not entry.get("ausstattung"):
            entry["ausstattung"] = generate_amenities(entry)
        
        # tier
        if not entry.get("tier"):
            entry["tier"] = "basic"
        
        json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        enriched += 1
        print(f"✅")
        time.sleep(0.1)
    
    print(f"\n✅ {enriched} Einträge angereichert")
    if enriched > 0:
        print(f"  ⚠️ Beschreibungen sind KI-generiert (Template). Evtl. Nachbearbeitung nötig.")
