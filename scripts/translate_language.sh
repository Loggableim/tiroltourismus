#!/bin/bash
# Orchestrator: Übersetzt ALLE Kategorien für eine Zielsprache
# Nutzung: bash scripts/translate_language.sh <sprache> [--limit N]
#   --limit N: Nur N Einträge PRO KATEGORIE übersetzen (Testmodus)

LANG=$1
LIMIT=""
[ "$2" = "--limit" ] && LIMIT="--limit $3"

BASE="F:/tiroltourismus"

echo "============================================"
echo "🌍 START Übersetzung DE → ${LANG^^}"
echo "📅 $(date)"
echo "============================================"

# ── Kategorien nach Größe sortiert (größte zuerst) ──
CATEGORIES=("gastro" "unterkuenfte" "orte" "camping" "sehenswuerdigkeiten" "magazin" "regionen" "erlebnisse" "events")

for cat in "${CATEGORIES[@]}"; do
  echo ""
  echo "════════════════════════════════════════════"
  echo "📂 Kategorie: $cat"
  echo "════════════════════════════════════════════"
  
  cd "$BASE"
  /e/HermesPortable/venv/Scripts/python scripts/translate_worker.py "$cat" "$LANG" $LIMIT
  
  echo "✅ ${cat} → ${LANG} abgeschlossen"
done

echo ""
echo "============================================"
echo "🏁 ALLE KATEGORIEN FÜR ${LANG^^} ÜBERSETZT"
echo "📅 $(date)"
echo "============================================"
