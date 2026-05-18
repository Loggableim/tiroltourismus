#!/usr/bin/env python3
"""Create all kanban tasks for the tirol-maps sprint."""
import subprocess, json, sys, os

BASE = "E:/HermesPortable"
ENV = {**os.environ, "HERMES_KANBAN_BOARD": "tirol-maps", "PYTHONPATH": "cids-hermes-agent"}
PROJECT = "F:/tiroltourismus"

def kanban(*args):
    r = subprocess.run(
        [sys.executable, "-m", "hermes_cli.main", "kanban", *args, "--json"],
        capture_output=True, text=True, timeout=30, cwd=BASE, env=ENV
    )
    if r.returncode != 0:
        print("ERR: " + r.stderr[:300], file=sys.stderr)
        return None
    try:
        return json.loads(r.stdout).get("id")
    except (json.JSONDecodeError, KeyError) as e:
        print("PARSE ERR: " + str(e)[:100], file=sys.stderr)
        return None

# Phase A: Daten-Grundlage
a1 = kanban("create", "A1 - GeoJSON Regionsgrenzen (13 Tiroler Regionen)",
    "--assignee", "backend-dev",
    "--body", "PROJEKT-PFAD: " + PROJECT + "\n--\nAUFGABE: 13 Regionen src/data/regionen/<slug>/index.json um grenzen-Feld ergaenzen.\nPolygon-Koordinaten via Overpass API holen (osmRelation), auf 10-20 Pkte simplifizieren.")
if not a1: sys.exit(1)

a2 = kanban("create", "A2 - findNearby() in content.js",
    "--assignee", "backend-dev",
    "--body", "PROJEKT-PFAD: " + PROJECT + "\n--\nAUFGABE: findNearby(entry, collection, locale, limit=6) in src/lib/content.js.\nFiltert entries nach Ort/Region, distanzbasiert falls koordinaten vorhanden.")
if not a2: sys.exit(1)

# Phase B: Regionen-Karte
b1 = kanban("create", "B1 - LeafletMap Polygon-Support (GeoJSON, Styling, Hover)",
    "--assignee", "frontend-dev",
    "--body", "PROJEKT-PFAD: " + PROJECT + "\n--\nAUFGABE: LeafletMap.jsx um polygons-prop erweitern.\nGeoJSON-Layer mit Dark-Theme (transparenter fill, leuchtender border, hover-highlight, tooltip).")
if not b1: sys.exit(1)

b2 = kanban("create", "B2 - Regionen-Karte in regionen/[slug]",
    "--assignee", "frontend-dev",
    "--body", "PROJEKT-PFAD: " + PROJECT + "\n--\nAUFGABE: src/pages/[locale]/regionen/[slug].astro finden.\nSectionMap mit Polygon + Ortsmarkern einbauen.")
if not b2: sys.exit(1)

# Phase C: Umgebungs-POIs
c1 = kanban("create", "C1 - Nearby POIs auf Detailseiten (Multi-Marker)",
    "--assignee", "feat-builder",
    "--body", "PROJEKT-PFAD: " + PROJECT + "\n--\nAUFGABE: Detailseiten um nahe POIs erweitern.\nNutzt findNearby(). Kategorie-Emojis: sehenswuerdigkeiten grej, gastro orange, unterkuenfte blue, camping green, erlebnisse pink, orte purple.")
if not c1: sys.exit(1)

c2 = kanban("create", "C2 - Marker-Clustering fuer viele POIs",
    "--assignee", "frontend-dev",
    "--body", "PROJEKT-PFAD: " + PROJECT + "\n--\nAUFGABE: Markerclustering in LeafletMap.jsx.\n>8 Marker = Cluster mit Counter. Klick zoomt rein.")
if not c2: sys.exit(1)

# Phase D: Uebersichts-Karten
d1 = kanban("create", "D1 - Uebersichts-Karte Collection-Indexseiten",
    "--assignee", "feat-builder",
    "--body", "PROJEKT-PFAD: " + PROJECT + "\n--\nAUFGABE: Indexseiten (sehenswuerdigkeiten, gastro, unterkuenfte, camping, erlebnisse, orte) SectionMap mit ALLEN published Eintraegen als Marker.")
if not d1: sys.exit(1)

d2 = kanban("create", "D2 - Karten-Filterleiste (Kategorie/Region)",
    "--assignee", "frontend-dev",
    "--body", "PROJEKT-PFAD: " + PROJECT + "\n--\nAUFGABE: Filter-Leiste ueber Uebersichts-Karte: Nach Kategorie/Region filtern. React-Insel. Marker live hide/show.")
if not d2: sys.exit(1)

# Phase E: Polish
e1 = kanban("create", "E1 - Design Refinements (Animation, Responsive, Dark-Mode)",
    "--assignee", "polish-dev",
    "--body", "PROJEKT-PFAD: " + PROJECT + "\n--\nAUFGABE: Marker-Appear-Animation, Polygon Hover Glow, Dark-Mode Toggle, Mobile 250px/Desktop 380px, Loading-Skeleton.")
if not e1: sys.exit(1)

e2 = kanban("create", "E2 - Build-Test + QA",
    "--assignee", "integrator",
    "--body", "PROJEKT-PFAD: " + PROJECT + "\n--\nAUFGABE: Build testen. Alle Kartentypen verifizieren. Dark/Light, Mobile/Desktop.")
if not e2: sys.exit(1)

ids = {"A1": a1, "A2": a2, "B1": b1, "B2": b2, "C1": c1, "C2": c2, "D1": d1, "D2": d2, "E1": e1, "E2": e2}
print("=== Tirol Maps Board ===")
for k, v in ids.items():
    print("  " + k + " -> " + (v if v else "FAILED"))
print("======================")
