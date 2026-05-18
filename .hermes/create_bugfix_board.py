import subprocess, json, os, sys

BASE = "E:/HermesPortable"
ENV = {**os.environ, "HERMES_KANBAN_BOARD": "tirol-bugfixes", "PYTHONPATH": "cids-hermes-agent"}
PROJECT = "F:\\tiroltourismus"

def kanban(*args):
    r = subprocess.run(
        [sys.executable, "-m", "hermes_cli.main", "kanban", *args, "--json"],
        capture_output=True, text=True, timeout=30, cwd=BASE, env=ENV
    )
    if r.returncode != 0:
        print(f"ERR: {r.stderr[:500]}")
        return None
    try:
        data = json.loads(r.stdout)
        if isinstance(data, list):
            return data
        return data.get("id")
    except (json.JSONDecodeError, KeyError):
        print(f"PARSE_ERR: {r.stdout[:300]}")
        return None

# === LANE A: Events Index (frontend-dev) ===
T1 = kanban("create",
    "T1: Events Index — fehlende Detail-Links + kaputte CSS-Klasse",
    "--assignee", "frontend-dev",
    "--body",
    "PROJEKT-PFAD: " + PROJECT + "\n" +
    "--\n" +
    "BUGS IN: src/pages/events/index.astro\n\n" +
    "BUG 1 — KEINE LINKS ZU DETAILSEITEN:\n" +
    "Event-Cards sind nicht als <a>-Links umschlossen. Besucher sehen die Event-Liste aber k\u00f6nnen nicht auf Detailseiten klicken.\n\n" +
    "FIX: Jede Event-Card in <a href=\"/events/{slug}/\">...</a> wrappen. Der Slug kommt aus e.slug.\n\n" +
    "BUG 2 — KAPUTTE CSS REVEAL-KLASSE:\n" +
    "Zeile 41: class=\"event-card reveal r{(i % 3) + 1}\"\n" +
    "Das ist ein Astro-Template-Ausdruck in normalen Anf\u00fchrungszeichen \u2014 wird als Literal-String 'r{(i % 3) + 1}' ausgegeben, nicht evaluiert.\n\n" +
    "FIX: class={`event-card reveal r${(i % 3) + 1}`} \u2014 Template-Literals mit Backticks verwenden.\n\n" +
    "PR\u00dcFEN: 'npm run build'\n" +
    "--\n" +
    "AKZEPTANZKRITERIEN:\n" +
    "- Event-Cards sind klickbar und f\u00fchren zu /events/<slug>/\n" +
    "- CSS-Klasse wird korrekt als 'r1', 'r2', 'r3' ausgegeben\n" +
    "- Build erfolgreich"
)

# === LANE B: Media/Hero Fixes (frontend-dev, parallel) ===
T2 = kanban("create",
    "T2: Hero aspect-ratio Bug + fehlende Brand-Bilder",
    "--assignee", "frontend-dev",
    "--body",
    "PROJEKT-PFAD: " + PROJECT + "\n" +
    "--\n" +
    "BUGS IN: src/pages/index.astro + src/pages/[locale]/index.astro + public/brand/hero-logos/\n\n" +
    "BUG 1 — ASPECT-RATIO 1/1 VERZERRT HERO-BILDER:\n" +
    "Zeile 363 in index.astro (und [locale]/index.astro):\n" +
    "  .hero-bg img { aspect-ratio:1/1 }\n" +
    "Das zwingt Hero-Landscape-Bilder in ein Quadrat \u2192 verzerrte Darstellung.\n\n" +
    "FIX: aspect-ratio:1/1 entfernen. Das Hero-Bild hat bereits object-fit:cover, das reicht.\n\n" +
    "BUG 2 — FEHLENDE BRAND-BILDER (5 von 6 Konzepten):\n" +
    "public/brand/hero-logos/ existiert nur: konzept1_gipfellinie_20260517_083224\n" +
    "Aber homepage.json referenziert in \"seelen\" 6 Konzepte (konzept1\u2013konzept6).\n" +
    "Die anderen 5 PNGs fehlen \u2192 404 auf der Homepage.\n\n" +
    "FIX: seelen.items in homepage.json auf nur 1 Item reduzieren (nur konzept1).\n" +
    "Oder: fehlende placeholder.png f\u00fcr konzept2\u20136 erstellen.\n" +
    "Pragmatisch: seelen auf [konzept1] reduzieren da keine Originale existieren.\n\n" +
    "PR\u00dcFEN: 'npm run build' + Browser-Check auf / (keine 404er)\n" +
    "--\n" +
    "AKZEPTANZKRITERIEN:\n" +
    "- Hero-Bilder nicht quadratisch verzerrt\n" +
    "- Keine 404 f\u00fcr Brand-Bilder\n" +
    "- Build erfolgreich"
)

# === LANE C: Data Cleanup (polish-dev, parallel) ===
T3 = kanban("create",
    "T3: Data Cleanup — Backup-Dir + BEZIRK_REGIONS + Duplicate-Links",
    "--assignee", "polish-dev",
    "--body",
    "PROJEKT-PFAD: " + PROJECT + "\n" +
    "--\n" +
    "BETROFFENE DATEIEN:\n" +
    "- src/data/unterkuenfte_backup/ (989 Eintr\u00e4ge \u2014 DELETE)\n" +
    "- src/pages/bezirke/[slug].astro (BEZIRK_REGIONS Mapping)\n" +
    "- src/lib/content.js (BEZIRK_REGIONS Mapping)\n" +
    "- src/pages/events/[slug].astro (Duplicate Webseite-Eintr\u00e4ge)\n\n" +
    "BUG 1 — ORPHAN BACKUP-DIR:\n" +
    "src/data/unterkuenfte_backup/ existiert mit 989 Eintr\u00e4gen \u2014 Backup das nicht ins Repo geh\u00f6rt.\n\n" +
    "FIX: rm -rf src/data/unterkuenfte_backup/\n\n" +
    "BUG 2 — BEZIRK_REGIONS MAPPING-FEHLER:\n" +
    "In src/lib/content.js (Zeile 17) und src/pages/bezirke/[slug].astro (Zeile 17):\n" +
    "  'schwaz': ['schwaz', 'achensee', 'zillertal', 'kaunertal']\n" +
    "Kaunertal geh\u00f6rt geografisch zum Bezirk Landeck, nicht Schwaz!\n\n" +
    "FIX: Kaunertal aus schwaz entfernen und zu landeck hinzuf\u00fcgen:\n" +
    "  'schwaz': ['schwaz', 'achensee', 'zillertal']\n" +
    "  'landeck': ['landeck', 'arlberg', 'kaunertal']\n" +
    "(BEIDE Dateien \u00e4ndern!)\n\n" +
    "BUG 3 — DUPLICATE WEBSEITE-EINTR\u00c4GE IN EVENTS DETAIL:\n" +
    "src/pages/events/[slug].astro Zeilen 79-80:\n" +
    "  entry.link && ... ? { label: 'Webseite', ... } : null,\n" +
    "  entry.webseite && ... ? { label: 'Webseite', ... } : null,\n" +
    "Beide haben label 'Webseite' \u2014 wenn beide Felder gesetzt sind, 2 identische Eintr\u00e4ge.\n\n" +
    "FIX: Einen umlabeln:\n" +
    "  - entry.link \u2192 label: 'Event-Seite'\n" +
    "  - entry.webseite \u2192 label: 'Webseite'\n\n" +
    "PR\u00dcFEN: 'npm run build'\n" +
    "--\n" +
    "AKZEPTANZKRITERIEN:\n" +
    "- unterkuenfte_backup gel\u00f6scht\n" +
    "- Kaunertal korrekt unter Landeck (nicht Schwaz)\n" +
    "- Keine doppelten 'Webseite'-Labels in Events\n" +
    "- Build erfolgreich"
)

# === LANE D: JS Prod Cleanup (polish-dev, parallel) ===
T4 = kanban("create",
    "T4: JS Production Cleanup — console.log + GA check",
    "--assignee", "polish-dev",
    "--body",
    "PROJEKT-PFAD: " + PROJECT + "\n" +
    "--\n" +
    "BETROFFENE DATEIEN:\n" +
    "- src/scripts/lemon-squeezy.js\n" +
    "- src/components/ContactForm.tsx\n\n" +
    "BUG 1 — CONSOLE.LOG IN PRODUKTION:\n" +
    "src/scripts/lemon-squeezy.js enth\u00e4lt console.log Statements:\n" +
    "- Zeile 141: console.log('[Tirol] Returning from checkout:', checkoutId)\n" +
    "- Zeile 170: console.log('[Tirol] Tier set to', tier, 'after checkout!')\n\n" +
    "Diese sind f\u00fcr Nutzer im Browser sichtbar und unprofessionell.\n\n" +
    "FIX: console.log Zeilen entfernen. console.error + console.warn BEHALTEN (wichtig f\u00fcr Debugging).\n\n" +
    "BUG 2 — GA REFERENZ OHNE INIT-CHECK:\n" +
    "src/components/ContactForm.tsx Zeile 96:\n" +
    "  if (typeof window !== 'undefined' && (window as any).trackEvent) {\n" +
    "    (window as any).trackEvent('Kontakt', ...);\n" +
    "  }\n" +
    "trackEvent wird nirgends definiert/initialisiert.\n\n" +
    "FIX: Zusatz-Check ob gtag verf\u00fcgbar oder trackEvent vorher als No-Op definieren:\n" +
    "  const track = (window as any).trackEvent || (window as any).gtag || (() => {});\n" +
    "  track('Kontakt', ...);\n\n" +
    "PR\u00dcFEN: 'npm run build'\n" +
    "--\n" +
    "AKZEPTANZKRITERIEN:\n" +
    "- Keine console.log Statements mehr im JS (error/warn bleiben)\n" +
    "- GA trackEvent robust gegen fehlende Initialisierung\n" +
    "- Build erfolgreich"
)

# === SYNTHESIS ===
T5 = kanban("create",
    "T5: Integrations-Review — Build + Smoke-Test + Commit",
    "--assignee", "integrator",
    "--parent", T1, "--parent", T2, "--parent", T3, "--parent", T4,
    "--body",
    "PROJEKT-PFAD: " + PROJECT + "\n" +
    "--\n" +
    "AUFGABE: Build-Test, Smoke-Check + Git Commit\n\n" +
    "ABH\u00c4NGIG VON: T1\u2013T4 (alle m\u00fcssen done sein)\n\n" +
    "SCHRITTE:\n" +
    "1. 'npm run build' \u2014 bei Fehlern analysieren und fixen\n" +
    "2. Pr\u00fcfen ob alle 4 Lanes korrekt umgesetzt wurden:\n" +
    "   - T1: Events haben Links + richtige CSS-Klassen\n" +
    "   - T2: Kein aspect-ratio:1/1 mehr auf Hero, keine 404 Brand-Bilder\n" +
    "   - T3: unterkuenfte_backup gel\u00f6scht, BEZIRK_REGIONS korrigiert, keine Duplicate-Labels\n" +
    "   - T4: Keine console.log in Prod-JS, GA robust\n" +
    "3. Build gr\u00fcn \u2192 git add -A, git commit, git push\n" +
    "4. Bei Build-Fehlern: Task blocken mit detailliertem Error\n\n" +
    "COMMIT-MESSAGE:\n" +
    "[bugfix] Events Index + Media + Data Cleanup + JS Prod Fixes\n\n" +
    "- Events Index: Detail-Links + korrekte CSS-Reveal-Klassen\n" +
    "- Hero: aspect-ratio:1/1 entfernt (verzerrte Bilder)\n" +
    "- Brand-Bilder: fehlende Konzepte bereinigt\n" +
    "- Data: unterkuenfte_backup gel\u00f6scht\n" +
    "- BEZIRK_REGIONS: Kaunertal \u2192 Landeck (war f\u00e4lschlich Schwaz)\n" +
    "- Events Detail: Duplicate-Label 'Webseite' gefixt\n" +
    "- JS: console.log Statements in Produktion entfernt\n" +
    "- GA trackEvent: robust gegen fehlende Initialisierung\n\n" +
    "PR\u00dcFEN: Build gr\u00fcn, dann commit + push\n" +
    "--\n" +
    "AKZEPTANZKRITERIEN:\n" +
    "- Build: gr\u00fcn\n" +
    "- Commit + Push auf remote"
)

print("=== ALLE TASKS ERSTELLT ===")
print(f"T1: {T1}")
print(f"T2: {T2}")
print(f"T3: {T3}")
print(f"T4: {T4}")
print(f"T5: {T5}")
