#!/usr/bin/env python3
"""Create Tirol SEO & Content Kanban board."""
import subprocess, json, sys, os

BASE = "E:/HermesPortable"
PROJECT = "F:/tiroltourismus"
ENV = {**os.environ, "HERMES_KANBAN_BOARD": "tirol-seo-content", "PYTHONPATH": "cids-hermes-agent"}

def kanban(title, *args, parents=None):
    cmd = [title]
    if args: cmd.extend(args)
    for p in (parents or []):
        if p: cmd.extend(["--parent", p])
    r = subprocess.run(
        [sys.executable, "-m", "hermes_cli.main", "kanban", "create", *cmd, "--json"],
        capture_output=True, text=True, timeout=30, cwd=BASE, env=ENV
    )
    if r.returncode != 0:
        print("ERR: " + r.stderr[:200], file=sys.stderr)
        return None
    try:
        return json.loads(r.stdout).get("id")
    except (json.JSONDecodeError, KeyError) as e:
        print("PARSE: " + str(e)[:80], file=sys.stderr)
        return None

B = "PROJEKT-PFAD: " + PROJECT + "\n--\n"

# P0
p0a = kanban("create", "P0a Content-Gap + Keyword-Plan", "--assignee", "seo-architect",
    "--body", B + "Analyse 43 bestehende Blog-Artikel auf Content-Luecken. Liste 25 Standard- + 15 In-Depth-Themen. Ergebnis: keyword-plan.json mit {titel,slug,kategorie,tags,keyword,typ}")
p0b = kanban("create", "P0b Meta-Description Audit", "--assignee", "seo-architect",
    "--body", B + "Alle src/data/*/ index.json scannen. Pruefe beschreibung/kurzbeschreibung/teaser auf Existenz + <=155 Zeichen. meta-audit.json erstellen.", parents=[p0a])

# P1: 25 Standard-Artikel
p1 = []
for b in range(1, 6):
    t = kanban("create", "P1." + str(b) + " Standard-Artikel x5", "--assignee", "content-filler",
        "--body", B + "5 Standard-Artikel (500-800 Woerter) als index.json in src/data/magazin/. Jeder: titel, slug, kategorie, autor, teaser(155), inhalt(md), tags(3-5), datum. 3-5 interne Links im Content. FLUX-Bild-Prompt. Themen aus P0a.")
    if t: p1.append(t)

# P2: 15 In-Depth
p2 = []
for b in range(1, 4):
    t = kanban("create", "P2." + str(b) + " InDepth-Artikel x5", "--assignee", "content-filler",
        "--body", B + "5 In-Depth-Artikel (2500-3500 Woerter). Struktur: Intro, 6-8 H2/H3, Tabelle, FAQ, Fazit. 5-8 interne Links. 3-5 FLUX-Bild-Prompts. Topics aus P0a.")
    if t: p2.append(t)

# P3: FAQ
p3 = kanban("create", "P3 FAQ 25 Fragen", "--assignee", "content-filler",
    "--body", B + "Datei src/data/faq.json erstellen. 25+ Eintraege: {frage, antwort(50-100w), kategorie, tags}. Kategorien: allgemein(5), wandern(4), ski(4), unterkunft(4), gastro(4), anreise(4). Max 2 interne Links/Antwort.", parents=p1[:2])

# P4: Cross-Linking
p4a = kanban("create", "P4a Cross-Link Blog zu Orten/Gastro", "--assignee", "feat-builder",
    "--body", B + "Alle neuen Blog-Artikel scannen. Pruefe ob /orte/, /gastro/, /unterkuenfte/ Links im Content. Fehlende: 2-3 natuerliche Text-Links einfuegen. Tags angleichen fuer cross-collection Matches.", parents=p1 + p2)
p4b = kanban("create", "P4b Cross-Link Blog zu Blog", "--assignee", "feat-builder",
    "--body", B + "Alle 83 Blog-Artikel (alt+neu) via Tags untereinander verlinken. findByTag()-Logik. Pro Artikel: 1 Link zu anderem Blog mit Tag-Overlap. /magazin/serien/ wo sinnvoll.", parents=[p4a])

# P5: FAQ Integration
p5 = kanban("create", "P5 FAQ Querverlinkung zu Blog", "--assignee", "feat-builder",
    "--body", B + "Zu jedem FAQ-Eintrag einen passenden Blog-Artikel verlinken. In Blog-Artikeln FAQ-Hinweis-Block anhaengen. /faq/ Seite erstellen falls fehlt.", parents=[p3, p4b])

# P6: Meta Fix
p6 = kanban("create", "P6 Meta-Descriptions fixen", "--assignee", "seo-architect",
    "--body", B + "meta-audit.json aus P0b einlesen. Alle fehlerhaften Descriptions korrigieren. Max 155 Zeichen. Aus name+ort+region+typ eine gute Description generieren.", parents=[p0b])

# P7: Build
p7 = kanban("create", "P7 Build + QA", "--assignee", "integrator",
    "--body", B + "npm run build. Erwartet 1920+ Seiten. Teste /faq/, /magazin/tags/, Tag-Seiten. Interne Links auf 200 pruefen. git add+commit+push.", parents=[p5, p6])

ids = {"P0a":p0a,"P0b":p0b,"P3":p3,"P4a":p4a,"P4b":p4b,"P5":p5,"P6":p6,"P7":p7}
for i,t in enumerate(p1): ids["P1."+str(i+1)] = t
for i,t in enumerate(p2): ids["P2."+str(i+1)] = t

print("=== Tirol SEO Content ===")
print("Tasks:", len(ids))
for k,v in sorted(ids.items()):
    print("  " + k + ": " + (v or "FAIL"))
