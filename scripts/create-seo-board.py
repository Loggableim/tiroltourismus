#!/usr/bin/env python3
"""Create kanban board for Tirol SEO Content Sprint."""
import subprocess, json, sys, os

BASE = "E:/HermesPortable"
ENV = {**os.environ, "HERMES_KANBAN_BOARD": "tirol-seo-content", "PYTHONPATH": "cids-hermes-agent"}
PROJECT = "F:/tiroltourismus"

def kanban(*args):
    r = subprocess.run([sys.executable, "-m", "hermes_cli.main", "kanban", *args, "--json"],
        capture_output=True, text=True, timeout=30, cwd=BASE, env=ENV)
    if r.returncode != 0:
        print(f"ERR: {r.stderr[:200]}", file=sys.stderr)
        return None
    try: return json.loads(r.stdout).get("id")
    except: return None

# === Phase 0: SEO Grundlage ===
s1 = kanban("create", "S0 - SEO Guideline + Keyword Plan", "--assignee", "seo-architect",
    "--body", f"PROJEKT-PFAD: {PROJECT}\n--\nAUFGABE: SEO-Richtlinie erstellen: Keyword-Plan pro Seite (Startseite, Regionen, Orte, Sehenswuerdigkeiten, Gastro, Unterkuenfte, Camping, Erlebnisse, Events, Magazin). Keyword-Cluster: Wandern, Ski, Familie, Kulinarik, Wellness, Kultur, Natur, Events. Longtail-Keywords identifizieren. writing-plans skill laden.\n--\nBETROFFENE DATEIEN: .hermes/plans/seo-guideline.md, .hermes/plans/keyword-plan.md")
s2 = kanban("create", "S1 - Meta Descriptions Audit + Optimierung", "--assignee", "seo-architect",
    "--body", f"PROJEKT-PFAD: {PROJECT}\n--\nAUFGABE: Alle 1843 Seiten meta description checken. Fehlende ergaenzen (120-160 Zeichen, Keyword-vorne, CTA). Fuer: regionen, orte, sehenswuerdigkeiten, gastro, unterkuenfte, camping, erlebnisse, events, magazin.\n--\nMethode: BaseLayout.astro hat standard-description. Collection-[slug].astro Seiten haben eigene description. Pruefe ob alle [slug].astro Seiten descriptions im DetailPage-Aufruf haben.")

# === Phase 1: FAQ ===
faq = kanban("create", "F1 - FAQ 25 Fragen erstellen", "--assignee", "content-filler",
    "--body", f"PROJEKT-PFAD: {PROJECT}\n--\nAUFGABE: src/pages/magazin/faq.astro erstellen mit 25 FAQ-Fragen zu Tirol-Tourismus. 50-100 Woerter pro Antwort. JSON-LD Schema.org/FAQPage einbetten.\nThemen: Anreise, Unterkunft, Wandern, Ski, Familie, Kulinarik, Wetter, Events, Regionen.\n--\nBETROFFENE DATEIEN: src/pages/magazin/faq.astro (neu)")

# === Phase 2: Kurz-Artikel (500+ words) ===
# 5 Batches a 4-5 Artikel
artikels = [
    ("Wandern & Bergsport", "wandern", [
        ("Die 10 schoensten Wanderwege Tirols fuer Einsteiger", "Wanderwege, leichte Touren, Panorama"),
        ("Wandern mit Kindern in Tirol – familienfreundliche Touren", "Familienwanderungen, kinderwagentauglich"),
        ("Huettenwanderungen in Tirol – von Alm zu Alm", "Almhuetten, Einkehren, Geniesserwanderung"),
        ("Die schoensten Bergseen Tirols – erfrischende Ziele", "Bergseen, Baden, Natur"),
    ]),
    ("Ski & Winterurlaub", "ski", [
        ("Die besten Skigebiete Tirols 2026 im Vergleich", "Skigebiete, Pisten, Schneesicherheit"),
        ("Winterurlaub in Tirol – was muss man wissen?", "Pauschale, Anreise, Ausruestung"),
        ("Ski fahren mit Familie in Tirol – kinderfreundliche Gebiete", "Familien-Skigebiete, Kinderpisten"),
        ("Apres-Ski in Tirol – die besten Adressen", "Apres-Ski, Partys, Hittendorf"),
    ]),
    ("Kulinarik & Genuss", "kulinarik", [
        ("Tiroler Kueche – Traditionelle Gerichte & Spezialitaeten", "Tiroler Groestl, Knoedel, Speck"),
        ("Die besten Huetten in Tirol zum Einkehren", "Huettenwirte, Almgastronomie, Jause"),
        ("Weinbau in Tirol – suedliche Haenge, edle Tropfen", "Weinberge, Suedtirol, Genuss"),
        ("Kulinarische Events in Tirol – Genussmessen & Co", "Genussfestivals, Bauernmaerkte"),
    ]),
    ("Familie & Aktivurlaub", "familie", [
        ("Familienurlaub in Tirol – die besten Tipps", "Hotels, Aktivitaeten, Kinder"),
        ("Die schoensten Freizeitparks und Erlebnisbaeder Tirols", "Aqua Dome, Erlebnispark, Rutschen"),
        ("Tiere und Natur in Tirol – Alpenzoo, Bauernhoefe & Co", "Alpenzoo, Kinderbauernhof, Naturerlebnis"),
        ("Sommerurlaub in Tirol – was tun bei Regen?", "Schlechtwetter, Alternativprogramm"),
    ]),
    ("Kultur & Events", "kultur", [
        ("Die schoensten Sehenswuerdigkeiten in Tirol", "Schloesser, Burgen, Altstaedte"),
        ("Kulturhighlights in Innsbruck – Goldenes Dachl & Co", "Innsbruck, Altstadt, Hofburg"),
        ("Die 5 schoensten Almen Tirols", "Almen, Genusswandern, Einkehren"),
        ("Wellness in Tirol – die besten Thermen & Spa-Resorts", "Therme, Spa, Erholung"),
    ]),
]

artikel_ids = []
for jahrgang, thema, titel_liste in artikels:
    for titel, keywords in titel_liste:
        slug = titel.lower().replace(" ","-").replace("–","").replace("?","").replace("ä","ae").replace("ö","oe").replace("ü","ue").replace("ß","ss").replace("--","-")[:60]
        slug = "".join(c for c in slug if c.isalnum() or c in "-_")
        tid = kanban("create", f"MAG-{thema}: {titel[:55]}", "--assignee", "content-filler",
            "--body", f"PROJEKT-PFAD: {PROJECT}\n--\nTITEL: {titel}\nTHEMA: {thema}\nSLUG: {slug}\nKATEGORIE: {jahrgang}\nTAGS: {keywords}\n--\nAUFGABE: src/data/magazin/{slug}/index.json erstellen. 500+ Woerter. Einleitung, 3-4 Zwischenueberschriften, Fazit. Keywords natuerlich einbauen. Max 5 Saetze pro Absatz.\n--\nAKZEPTANZKRITERIEN:\n- 500-700 Woerter\n- Keywords in H2-Ueberschriften\n- Verlinkung auf existierende Artikel/Seiten im Text")
        if tid: artikel_ids.append(tid)

# === Phase 3: In-Depth Artikel (2500+ words) ===
indephs = [
    ("Wandern in Tirol – Der ultimative Guide fuer alle Levels",
     "wandern", "wanderparadies-tirol", "wanderwege, alpenverein, outdoor"),
    ("Skiurlaub in Tirol – Alles von Vorbereitung bis Abfahrt",
     "ski", "skifahren-arlberg", "skiurlaub, pistenguide, wintersport"),
    ("Tiroler Kueche von A-Z – Die kulinarische Reise durchs Land",
     "kulinarik", "tiroler-kulinarik", "knoedel, tiroler-spezialitaeten, genuss"),
    ("Familienurlaub Tirol – Der komplette Reisefuehrer",
     "familie", "familienurlaub-tirol", "familienhotels, kinderaktivitaeten, tipps"),
    ("Innsbruck entdecken – Der grosse City-Guide",
     "kultur", "innsbruck-city-guide", "innsbruck, sehenswuerdigkeiten, city-trip"),
    ("Wellness in Tirol – Die besten Adressen fuer Erholungssuchende",
     "wellness", "wellness-thermen-tirol", "wellnesshotel, spa, thermen"),
    ("Events & Festivals in Tirol 2026 – Der Jahreskalender",
     "events", "kitzbuehel-events", "feste, konzerte, tradition"),
    ("Oetztal Reisefuehrer – Aktivurlaub im Sueden Tirols",
     "wandern", "wanderwege-oetztal", "oetztal, gaugler, soelden"),
    ("Zillertal Reisefuehrer – Tal der Vielfalt",
     "familie", "wanderparadies-zillertal", "zillertal, mayrhofen, aktiv"),
    ("Stubaital Reisefuehrer – Natur pur vor Innsbrucks Haustuer",
     "wandern", "stubaital-familien", "stubaital, gleischerstrasse, wanderparadies"),
    ("Arlberg – Das ultimative Ski-Paradies",
     "ski", "skifahren-arlberg", "arlberg, st-anton, lech"),
    ("Kaunertal – Gletscherski und wilde Natur",
     "ski", "skifahren-kaunertal", "kaunertal, gletscher, fechter"),
]

indepth_ids = []
for titel, thema, related_slug, tags in indephs:
    slug = titel.lower().replace(" ","-").replace("–","").replace("?","").replace("ä","ae").replace("ö","oe").replace("ü","ue").replace("ß","ss").replace("--","-")[:60]
    slug = "".join(c for c in slug if c.isalnum() or c in "-_")
    tid = kanban("create", f"DEPTH-{thema}: {titel[:55]}", "--assignee", "content-filler",
        "--body", f"PROJEKT-PFAD: {PROJECT}\n--\nTITEL: {titel}\nTHEMA: {thema}\nSLUG: {slug}\nTAGS: {tags}\nVERWANDT: {related_slug}\n--\nAUFGABE: src/data/magazin/{slug}/index.json erstellen. 2500+ Woerter. Struktur: Einleitung, 6-8 Kapitel mit H2, Fazit, Quellen. Keywords natuerlich. Tiefgehende Recherche, praktische Tipps.\n--\nAKZEPTANZKRITERIEN:\n- 2500-3500 Woerter\n- 6+ Abschnitte mit H2\n- Verlinkung auf existierende Seiten\n- Exakte Daten, Oeffnungszeiten wo sinnvoll")
    if tid: indepth_ids.append(tid)

# === Phase 4: Bilder (FLUX) ===
bild_batch = kanban("create", "IMG - FLUX Bilder + WebP fuer alle Artikel", "--assignee", "content-filler",
    "--body", f"PROJEKT-PFAD: {PROJECT}\n--\nAUFGABE: Fuer alle Magazin-Artikel FLUX-Bilder generieren und als WebP speichern. 1024x1024, Tourismus-Motive passend zum Artikelthema. Sichern unter src/assets/images/magazin/{slug}.webp. hero_bild im JSON aktualisieren.\n--\nMethode: SiliconFlow API (FLUX.1-schnell), 3 parallel, ThreadPoolExecutor. keyword: 'alpine tourism photography style'")

# === Phase 5: Cross-Linking ===
xlink = kanban("create", "LINK - Cross-Linking + Interne Verlinkung", "--assignee", "seo-architect",
    "--body", f"PROJEKT-PFAD: {PROJECT}\n--\nAUFGABE: Querverlinkung via Tags: Jeder Artikel, Ort, Restaurant, Sehenswuerdigkeit bekommt am Ende 'Weitere Beitraege' via findByTag(). Sicherstellen dass 1-2 interne Links pro Seite im Content sind. Tags in Artikeln pruefen auf existierende Seiten.\n--\nBETROFFENE DATEIEN: src/pages/*/[slug].astro, src/lib/content.js")

# === Phase 6: Bild-Optimierung + Build ===
opt = kanban("create", "OPT - WebP Konvertierung + Build", "--assignee", "polish-dev",
    "--body", f"PROJEKT-PFAD: {PROJECT}\n--\nAUFGABE: Alle hero_bild PNGs nach WebP konvertieren (quality 85). build testen. 1843+ Seiten. page count dokumentieren.")

print("=== Board erstellt ===")
print(f"SEO: {s1}, {s2}")
print(f"FAQ: {faq}")
print(f"Blog Kurz: {len(artikel_ids)} Tasks")
print(f"Blog Depth: {len(indepth_ids)} Tasks")
print(f"Bilder: {bild_batch}")
print(f"Linking: {xlink}")
print(f"Optimierung: {opt}")
print(f"Total: {2 + 1 + len(artikel_ids) + len(indepth_ids) + 1 + 1 + 1} Tasks")
