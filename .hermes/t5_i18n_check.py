"""
T5: i18n-Completion-Check
Prueft welche Sprachen Luecken haben
"""
import json, os

PROJECT = r"F:\tiroltourismus"
PAGES = os.path.join(PROJECT, "src", "pages")
DATA = os.path.join(PROJECT, "src", "data")

LOCALES = ["en", "fr", "es", "it", "nl", "zh"]
LOCALE_DIR = os.path.join(PAGES, "[locale]")

# Seiten die in jeder Sprache existieren muessen
REQUIRED_PAGES = [
    "index.astro",
    "404.astro", 
    "500.astro",
    "faq/index.astro",
    "impressum/index.astro",
    "datenschutz/index.astro",
    "agb/index.astro",
    "kontakt/index.astro",
    "ueber-uns/index.astro",
    "suche/index.astro",
    "preise/index.astro",
    "newsletter/index.astro",
    "merkliste/index.astro",
    "login.astro",
    "dashboard.astro",
    "fuer-betriebe/index.astro",
    "camping/index.astro",
    "camping/[slug].astro",
    "orte/index.astro",
    "orte/[slug].astro",
    "regionen/index.astro",
    "regionen/[slug].astro",
    "unterkuenfte/index.astro",
    "unterkuenfte/[slug].astro",
    "erlebnisse/index.astro",
    "erlebnisse/[slug].astro",
    "gastro/index.astro",
    "gastro/[slug].astro",
    "sehenswuerdigkeiten/index.astro",
    "sehenswuerdigkeiten/[slug].astro",
    "events/index.astro",
    "events/[slug].astro",
    "magazin/index.astro",
    "magazin/[slug].astro",
    "magazin/faq.astro",
    "bezirke/index.astro",
    "bezirke/[slug].astro",
    "wappen/index.astro",
]

def collect_pages(base_dir):
    """Recursively find all .astro and .md files"""
    pages = set()
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if f.endswith((".astro", ".md")):
                rel_path = os.path.relpath(os.path.join(root, f), base_dir)
                pages.add(rel_path.replace("\\", "/"))
    return pages

print("=== i18n COMPLETION CHECK ===")
print()

# Check locale pages
de_pages = collect_pages(PAGES)
locale_pages_by_lang = {}

for loc in LOCALES:
    loc_dir = os.path.join(LOCALE_DIR.replace("[locale]", loc) if LOCALE_DIR else "", "")
    # Actually [locale] is the dynamic routing dir, the actual dirs are per-locale
    # Let's look at pages/[locale]/ subdirs which are actual lang dirs
    pass

# Better approach: find actual lang directories (subdirs under pages)
all_dirs = [d for d in os.listdir(PAGES) if os.path.isdir(os.path.join(PAGES, d)) and len(d) in (2, 5)]
lang_dirs = {}
for d in all_dirs:
    lang_dir = os.path.join(PAGES, d)
    pages_set = collect_pages(lang_dir)
    lang_dirs[d] = pages_set
    print(f"  {d}: {len(pages_set)} pages")

print()

# Also check pages root (German)
# Main pages
main_pages = collect_pages(PAGES)
root_pages = {p for p in main_pages if "/" not in p}
subdir_pages = {p for p in main_pages if "/" in p}

print(f"DE (root): {len(main_pages)} total pages")

# Check which required pages exist in each lang
missing = {}
for loc, pages in lang_dirs.items():
    missing[loc] = []
    for req in REQUIRED_PAGES:
        if req not in pages:
            missing[loc].append(req)

print()
print("=== FEHLENDE SEITEN PRO SPRACHE ===")
for loc, misses in sorted(missing.items()):
    misses_filtered = [m for m in misses if not m.endswith("/[slug].astro")]  # slug pages might not exist as index
    if misses_filtered:
        print(f"\n{loc}: {len(misses_filtered)} missing")
        for m in misses_filtered:
            print(f"  - {m}")

# Check data translation directories
print()
print("=== DATA i18n CHECK ===")
data_i18n_issues = []
for coll in ["orte", "regionen", "unterkuenfte", "gastro", "erlebnisse", "sehenswuerdigkeiten", "events", "camping"]:
    coll_dir = os.path.join(DATA, coll)
    if not os.path.isdir(coll_dir):
        continue
    for slug in os.listdir(coll_dir):
        slug_dir = os.path.join(coll_dir, slug)
        if not os.path.isdir(slug_dir):
            continue
        i18n_dir = os.path.join(slug_dir, "i18n")
        if not os.path.isdir(i18n_dir):
            # Count how many items have NO i18n at all
            pass
            continue
        # Check which languages have translation files
        i18n_files = {f.replace(".json","") for f in os.listdir(i18n_dir) if f.endswith(".json")}
        missing_langs = [l for l in LOCALES if l not in i18n_files]
        if missing_langs:
            data_i18n_issues.append({"slug": f"{coll}/{slug}", "missing": missing_langs})

# Aggregate
coll_i18n_counts = {}
for iss in data_i18n_issues:
    c = iss["slug"].split("/")[0]
    coll_i18n_counts[c] = coll_i18n_counts.get(c, 0) + 1

for coll, cnt in sorted(coll_i18n_counts.items()):
    print(f"  {coll}: {cnt} items with missing i18n files")

print()
print(f"Total items with i18n gaps: {len(data_i18n_issues)}")
if len(data_i18n_issues) > 0:
    print(f"  Sample: {data_i18n_issues[0]}")

print()
print("=== EMPFEHLUNGEN ===")
# Generate prioritized list
critical = []
for loc, misses in missing.items():
    for m in misses:
        if "404" in m or "500" in m:
            critical.append(f"{loc}: {m}")
print(f"Critical (404/500 missing): {len(critical)}")
for c in critical:
    print(f"  ! {c}")

print()
print("SUMMARY: Checked " + str(len(lang_dirs)) + " languages, " + str(len(REQUIRED_PAGES)) + " required pages per language")
