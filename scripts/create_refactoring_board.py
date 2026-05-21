#!/usr/bin/env python3
"""Create all refactoring tasks on tirol-6sprachen board."""
import subprocess, json, sys, os, time

HERMES_BASE = "E:/HermesPortable"
BOARD = "tirol-6sprachen"
PROJECT = "F:/tiroltourismus"
PROFILE = "backend-dev"

ENV = {**os.environ,
    "HERMES_KANBAN_BOARD": BOARD,
    "PYTHONPATH": f"{HERMES_BASE}/cids-hermes-agent"
}
CLI = [sys.executable, "-m", "hermes_cli.main", "kanban"]

def kanban(*args):
    cmd = CLI + list(args) + ["--json"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=ENV, cwd=HERMES_BASE)
    if r.returncode != 0:
        print(f"  ❌ {' '.join(args[:3])}: {r.stderr[:150]}", flush=True)
        return None
    try:
        return json.loads(r.stdout)["id"]
    except:
        print(f"  ❌ PARSING FAILED: {r.stdout[:200]}", flush=True)
        return None

PB = f"PROJEKT-PFAD: {PROJECT}"

print("=" * 60)
print("🏗️  TIROL 6-SPRACHEN REFACTORING")
print("=" * 60)

# ── PHASE 1: BaseLayout + languages.js (Foundation) ──
print("\n--- 🔥 PHASE 1: Foundation (BaseLayout + languages.js) ---")
p1_tasks = {}

# T1: languages.js aktualisieren
t = kanban("create", "P1-1 languages.js erweitern", "--body", 
    f"{PB}\nFüge IT/ES/ZH zu LANGUAGES_READY hinzu. Aktuell: ['de','en','fr'] → ['de','en','fr','it','es','zh'].\nDatei: src/lib/languages.js\nSetze ready=true für alle 6 Sprachen.", "--assignee", PROFILE)
if t: p1_tasks["languages"] = t; print(f"  ✅ P1-1 → {t}")
time.sleep(0.2)

# T2: BaseLayout langCode/fullLocale/localePrefix generalisieren
t = kanban("create", "P1-2 BaseLayout Locale-Helper", "--body",
    f"{PB}\nErsetze in src/layouts/BaseLayout.astro die harten de/en-Checks:\n"
    "- Zeile 33: langCode = locale === 'en' ? 'en' : 'de' → dynamisch\n"
    "- Zeile 34: fullLocale = locale === 'en' ? 'en_US' : 'de_AT' → Map mit DE/de_AT, EN/en_US, FR/fr_FR, IT/it_IT, ES/es_ES, ZH/zh_CN\n"
    "- Zeile 35: localePrefix = locale === 'en' ? '/en' : '' → localePrefix(locale) importieren\n"
    "- Zeile 36: siteDesc locale-bewusst machen (LANGUAGES.find().name)\n"
    "- Zeilen 117, 118, 136: JSON-LD descriptions locale-bewusst", "--assignee", PROFILE, "--parent", p1_tasks.get("languages",""))
if t: p1_tasks["baselocale"] = t; print(f"  ✅ P1-2 → {t}")
time.sleep(0.2)

# T3: BaseLayout Nav-Labels auf 6 Sprachen
t = kanban("create", "P1-3 BaseLayout Nav-Labels 6 Sprachen", "--body",
    f"{PB}\nDie Nav-Labels in BaseLayout.astro (Zeile 49-109) sind nur DE/EN.\n"
    "Ersetze das Ternary durch eine Map navLabels[locale] = {{...}} mit Einträgen für fr, it, es, zh.\n"
    "Für fehlende Sprachen: Fallback zu Englisch.\n"
    "Nutze die LANGUAGES-Konstante für die Sprachauswahl.", "--assignee", PROFILE, "--parent", p1_tasks.get("baselocale",""))
if t: p1_tasks["navlabels"] = t; print(f"  ✅ P1-3 → {t}")
time.sleep(0.2)

# T4: BaseLayout Footer + Alternates locale-bewusst
t = kanban("create", "P1-4 BaseLayout Footer Links + hreflang", "--body",
    f"{PB}\nFooter-Links in BaseLayout.astro: /agb/, /datenschutz/, /impressum/\n"
    "müssen locale-Prefix bekommen: /fr/agb/, /fr/datenschutz/\n"
    "hreflang-Links (Zeile 159-160) sind schon dynamisch via switchLangPath – prüfen ob's funktioniert.\n"
    "og:locale (Zeile 178) auf fullLocale setzen.", "--assignee", PROFILE, "--parent", p1_tasks.get("baselocale",""))
if t: p1_tasks["footer"] = t; print(f"  ✅ P1-4 → {t}")
time.sleep(0.2)

p1_master = kanban("create", "P1-MASTER Foundation", "--body",
    f"{PB}\nPhase 1 komplett: languages.js + BaseLayout lokalisiert.\n"
    "Basis für alle weiteren Phasen. Build-test nach Abschluss.",
    "--assignee", PROFILE)
for _, tid in p1_tasks.items():
    if tid: kanban("link", "--parent", p1_master, "--child", tid)
    time.sleep(0.1)
print(f"  ✅ P1-MASTER → {p1_master}")
time.sleep(0.2)

# ── PHASE 2: Bestehende [locale]-Seiten erweitern ──
print("\n--- 🏗️  PHASE 2: [locale]-Seiten für FR+IT+ES+ZH öffnen ---")
# Diese hängen von Phase 1 ab
for pt in p1_tasks.values():
    if pt: p1_parents = pt
    break

t2_1 = kanban("create", "P2-1 [locale]/index.astro erweitern", "--body",
    f"{PB}\nDatei: src/pages/[locale]/index.astro\n"
    "getStaticPaths() von ['de','en'] auf LANGUAGES_READY umstellen.\n"
    "Die t-Objekte (welcome/en/heute/regionen etc.) sind hardcode für de/en –\n"
    "für FR/IT/ES/ZH: readSingleton('homepage', locale) nutzen.\n"
    "Falls kein FR-homepage.json existiert → graceful fallback zu DE-Texten.", "--assignee", PROFILE,
    "--parent", p1_master)
print(f"  ✅ P2-1 → {t2_1}")
time.sleep(0.2)

t2_2 = kanban("create", "P2-2 [locale]/regionen/index.astro + [slug].astro", "--body",
    f"{PB}\nBeide Dateien in src/pages/[locale]/regionen/:\n"
    "- index.astro: getStaticPaths() auf LANGUAGES_READY\n"
    "- [slug].astro: const locales = LANGUAGES_READY\n"
    "Beide haben hardcode t-Objekte (de/en) – für andere Sprachen Fallback zu EN.", "--assignee", PROFILE,
    "--parent", p1_master)
print(f"  ✅ P2-2 → {t2_2}")
time.sleep(0.2)

p2_master = kanban("create", "P2-MASTER [locale]-Seiten", "--body",
    f"{PB}\nPhase 2: 3 Dateien erweitert.\nBuild-Test: /fr/, /fr/regionen/ sollten nicht mehr 404 geben.",
    "--assignee", PROFILE, "--parent", p1_master)
kanban("link", "--parent", p2_master, "--child", t2_1)
kanban("link", "--parent", p2_master, "--child", t2_2)
print(f"  ✅ P2-MASTER → {p2_master}")
time.sleep(0.2)

# ── PHASE 3: content.js locale-defaults ──
print("\n--- 📂 PHASE 3: content.js locale-Parameter ---")
t3_1 = kanban("create", "P3-1 content.js locale-Defaults fixen", "--body",
    f"{PB}\nDatei: src/lib/content.js\n"
    "- findNearby(entry, coll, 'de', limit) → findNearby(entry, coll, locale, limit)\n"
    "- findByTag(tag, 'de') → findByTag(tag, locale)\n"
    "- autoLinkContent(html, entry, 'de') → autoLinkContent(html, entry, locale)\n"
    "- findRelated(coll, slug, 'de') → findRelated(coll, slug, locale)\n"
    "Wichtig: Caller auf allen Detailseiten müssen locale übergeben.", "--assignee", PROFILE,
    "--parent", p1_master)
print(f"  ✅ P3-1 → {t3_1}")
time.sleep(0.2)

p3_master = kanban("create", "P3-MASTER content.js locale", "--body",
    f"{PB}\ncontent.js Funktionen können jetzt locale entgegennehmen.",
    "--assignee", PROFILE, "--parent", p1_master, "--parent", t3_1)
print(f"  ✅ P3-MASTER → {p3_master}")
time.sleep(0.2)

# ── PHASE 4: Kategorie-Seiten (massiv ~22 Dateien) ──  
print("\n--- 🔥 PHASE 4: Kategorie-Seiten locale-fähig (22 Dateien) ---")
# Gastro
t4_g = kanban("create", "P4-1 Gastro: index + [slug] locale", "--body",
    f"{PB}\nErstelle/ändere:\n"
    "- src/pages/[locale]/gastro/index.astro (Liste) → readCollection('gastro', locale)\n"
    "- src/pages/[locale]/gastro/[slug].astro (Detail) → readEntry('gastro', slug, locale)\n"
    "getStaticPaths() über LANGUAGES_READY iterieren für locale.\n"
    "Alte Datei src/pages/gastro/ bleibt für DE-Root-Pfad bestehen.", "--assignee", PROFILE,
    "--parent", p2_master, "--parent", p3_master)
print(f"  ✅ P4-1 → {t4_g}")
time.sleep(0.2)

t4_u = kanban("create", "P4-2 Unterkünfte: index + [slug] locale", "--body",
    f"{PB}\nAnalog zu Gastro:\n"
    "src/pages/[locale]/unterkuenfte/index.astro + [slug].astro\n"
    "readCollection('unterkuenfte', locale) + readEntry('unterkuenfte', slug, locale)\n"
    "getStaticPaths() über LANGUAGES_READY. DE-Root-Pfad bleibt.", "--assignee", PROFILE,
    "--parent", p2_master, "--parent", p3_master)
print(f"  ✅ P4-2 → {t4_u}")
time.sleep(0.2)

t4_o = kanban("create", "P4-3 Orte: index + [slug] locale", "--body",
    f"{PB}\nsrc/pages/[locale]/orte/index.astro + [slug].astro\n"
    "Analog zu Gastro. readCollection('orte', locale).", "--assignee", PROFILE,
    "--parent", p2_master, "--parent", p3_master)
print(f"  ✅ P4-3 → {t4_o}")
time.sleep(0.2)

t4_c = kanban("create", "P4-4 Camping: index + [slug] locale", "--body",
    f"{PB}\nsrc/pages/[locale]/camping/index.astro + [slug].astro", "--assignee", PROFILE,
    "--parent", p2_master, "--parent", p3_master)
print(f"  ✅ P4-4 → {t4_c}")
time.sleep(0.2)

t4_s = kanban("create", "P4-5 Sehenswürdigkeiten: index + [slug] locale", "--body",
    f"{PB}\nsrc/pages/[locale]/sehenswuerdigkeiten/index.astro + [slug].astro", "--assignee", PROFILE,
    "--parent", p2_master, "--parent", p3_master)
print(f"  ✅ P4-5 → {t4_s}")
time.sleep(0.2)

t4_m = kanban("create", "P4-6 Magazin: index + [slug] + tag + tags + faq locale", "--body",
    f"{PB}\nsrc/pages/[locale]/magazin/:\n"
    "- index.astro\n"
    "- [slug].astro\n"
    "- tag/[tag].astro\n"
    "- tags/index.astro\n"
    "- faq.astro\n"
    "5 Dateien! readCollection('magazin', locale) etc.", "--assignee", PROFILE,
    "--parent", p2_master, "--parent", p3_master)
print(f"  ✅ P4-6 → {t4_m}")
time.sleep(0.2)

t4_e = kanban("create", "P4-7 Erlebnisse: index + [slug] locale", "--body",
    f"{PB}\nsrc/pages/[locale]/erlebnisse/index.astro + [slug].astro", "--assignee", PROFILE,
    "--parent", p2_master, "--parent", p3_master)
print(f"  ✅ P4-7 → {t4_e}")
time.sleep(0.2)

t4_ev = kanban("create", "P4-8 Events: index + [slug] + eintragen locale", "--body",
    f"{PB}\nsrc/pages/[locale]/events/:\n"
    "- index.astro\n"
    "- [slug].astro\n"
    "- eintragen/index.astro (3 Dateien)", "--assignee", PROFILE,
    "--parent", p2_master, "--parent", p3_master)
print(f"  ✅ P4-8 → {t4_ev}")
time.sleep(0.2)

t4_b = kanban("create", "P4-9 Bezirke: index + [slug] locale", "--body",
    f"{PB}\nsrc/pages/[locale]/bezirke/index.astro + [slug].astro", "--assignee", PROFILE,
    "--parent", p2_master, "--parent", p3_master)
print(f"  ✅ P4-9 → {t4_b}")
time.sleep(0.2)

p4_master = kanban("create", "P4-MASTER Kategorie-Seiten (22 Dateien)", "--body",
    f"{PB}\n9 Kategorien mit insgesamt ~22 Dateien in [locale]/ verschoben.\n"
    "Alte Root-Seiten bleiben für DE-Kompatibilität.\n"
    "Build-Test nach Abschluss: /fr/gastro/, /it/orte/ etc.", "--assignee", PROFILE,
    "--parent", p2_master)
print(f"  ✅ P4-MASTER → {p4_master}")
time.sleep(0.2)

# ── PHASE 5: Statische Seiten ──
print("\n--- 📝 PHASE 5: Statische Seiten (11 Dateien) ---")
t5_1 = kanban("create", "P5-1 AGB + Datenschutz + Impressum locale", "--body",
    f"{PB}\n3 Dateien: src/pages/[locale]/agb|datenschutz|impressum/index.astro\n"
    "Rechtstexte via readSingleton('agb'|'datenschutz'|'impressum', locale)\n"
    "Falls keine Übersetzung existiert → DE-Text als Fallback.", "--assignee", PROFILE,
    "--parent", p2_master)
print(f"  ✅ P5-1 → {t5_1}")
time.sleep(0.2)

t5_2 = kanban("create", "P5-2 FAQ + Kontakt + ÜberUns locale", "--body",
    f"{PB}\nsrc/pages/[locale]/faq|kontakt|ueber-uns/index.astro\n"
    "FAQ ist data-getrieben (readSingleton('faq', locale)).\n"
    "Kontakt/ÜberUns: Text über i18n-Map oder readSingleton.", "--assignee", PROFILE,
    "--parent", p2_master)
print(f"  ✅ P5-2 → {t5_2}")
time.sleep(0.2)

t5_3 = kanban("create", "P5-3 Preise + Newsletter + FürBetriebe + Suche locale", "--body",
    f"{PB}\nsrc/pages/[locale]/preise|newsletter|fuer-betriebe|suche/index.astro\n"
    "Suche: locale-aware Such-Index.\n"
    "Preise/Newsletter/FürBetriebe: Text via readSingleton.", "--assignee", PROFILE,
    "--parent", p2_master)
print(f"  ✅ P5-3 → {t5_3}")
time.sleep(0.2)

t5_4 = kanban("create", "P5-4 Merkliste locale", "--body",
    f"{PB}\nsrc/pages/[locale]/merkliste/index.astro\n"
    "Wishlist-Seite locale-bewusst machen.", "--assignee", PROFILE,
    "--parent", p2_master)
print(f"  ✅ P5-4 → {t5_4}")
time.sleep(0.2)

p5_master = kanban("create", "P5-MASTER Statische Seiten (11 Dateien)", "--body",
    f"{PB}\n11 statische Seiten als [locale]/ verfügbar.\n"
    "Build-Test: /fr/agb/, /it/kontakt/ etc.", "--assignee", PROFILE,
    "--parent", p2_master)
print(f"  ✅ P5-MASTER → {p5_master}")
time.sleep(0.2)

# ── PHASE 6: Astro Config + Sitemap ──
print("\n--- 🌐 PHASE 6: Astro Config + Sitemap ---")
t6_1 = kanban("create", "P6-1 astro.config locale + Sitemap", "--body",
    f"{PB}\nastro.config.mjs:\n"
    "- i18n-Konfiguration: defaultLocale='de', locales=['de','en','fr','it','es','zh']\n"
    "- routing: {{ prefixDefaultLocale: false }} (DE bleibt /, rest /en/ /fr/ etc.)\n"
    "- sitemap mit hreflang für alle Sprachen\n"
    "Build-Test nach Abschluss: Alle generierten Seiten checken.", "--assignee", PROFILE,
    "--parent", p1_master)
print(f"  ✅ P6-1 → {t6_1}")
time.sleep(0.2)

# ── PHASE 7: Build + Deploy ──
print("\n--- 🚀 PHASE 7: Build + Deploy ---")
t7_1 = kanban("create", "P7-1 Build-Test + Bugfixes", "--body",
    f"{PB}\n'cd {PROJECT} && npm run build' ausführen.\n"
    "Fehler fixen: fehlende Imports, falsche Pfade, etc.\n"
    "Build muss erfolgreich durchlaufen.", "--assignee", PROFILE)
print(f"  ✅ P7-1 → {t7_1}")
time.sleep(0.2)

t7_2 = kanban("create", "P7-2 Deploy auf GitHub Pages", "--body",
    f"{PB}\n'cd {PROJECT} && git add -A && git commit -m \"[i18n] 6-Sprachen-Architektur\" && git push'\n"
    "GitHub Actions baut und deployed automatisch.\n"
    "Nach Deploy: /fr, /en/regionen/, /fr/gastro/x/ testen.", "--assignee", PROFILE,
    "--parent", t7_1)
print(f"  ✅ P7-2 → {t7_2}")
time.sleep(0.2)

print(f"\n{'='*60}")
print(f"🏁 BOARD COMPLETE: 24 Tasks in 7 Phasen")
print(f"{'='*60}")
print(f"\nLos geht's mit Phase 1!")
