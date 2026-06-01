#!/bin/bash
# Master Translation Cron Script v3
# Läuft alle 30 Minuten, übersetzt fehlende Sprachen nacheinander
# Nutzt Lock-Datei + Process-Check um Duplikate zu vermeiden

BOARD="tirol-uebersetzung"
BASE="F:/tiroltourismus"
LOCK_FILE="/tmp/translate_master.lock"
PYTHON_EXE="/e/HermesPortable/venv/Scripts/python"
ENV="HERMES_KANBAN_BOARD=$BOARD PYTHONPATH=E:/HermesPortable/cids-hermes-agent"
KANBAN="cd E:/HermesPortable && $ENV $PYTHON_EXE -m hermes_cli.main kanban"

# ═══ Lock-Check ═══
if [ -f "$LOCK_FILE" ]; then
  LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null)
  if kill -0 "$LOCK_PID" 2>/dev/null; then
    echo "⏩ Übersetzung läuft bereits (PID $LOCK_PID) – überspringe"
    exit 0
  fi
  rm -f "$LOCK_FILE"
fi

# Prüfe ob translate_language.sh bereits aktiv ist
EXISTING=$(ps aux 2>/dev/null | grep "translate_language" | grep -v grep | head -1)
if [ -n "$EXISTING" ]; then
  echo "⏩ translate_language.sh läuft bereits – überspringe"
  exit 0
fi

echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

echo "============================================"
echo "🌍 TRANSLATION MASTER CHECK  $(date)"
echo "============================================"
cd "$BASE" || exit 1

LANG_TOTAL=5240

# ═══ Check language progress ═══
check_lang() {
  local lang=$1; local total=0
  for cat in gastro unterkuenfte orte camping sehenswuerdigkeiten magazin regionen erlebnisse events; do
    total=$((total + $(find "src/data/$lang/$cat" -name "index.json" 2>/dev/null | wc -l)))
  done
  echo $total
}

# ═══ Complete kanban tasks for a language ═══
complete_lang_kb() {
  local lang="$1"
  case $lang in fr) p="FR" ;; en) p="EN" ;; it) p="IT" ;; es) p="ES" ;; zh) p="ZH" ;; nl) p="NL" ;; cs) p="CS" ;; esac
  local json=$($KANBAN list --json 2>/dev/null)
  for tid in $(echo "$json" | python3 -c "
import json,sys
for t in json.load(sys.stdin):
    if t.get('title','').startswith('$p') and t.get('status') in ('blocked','running'):
        print(t['id'])
" 2>/dev/null); do
    $KANBAN unblock "$tid" 2>/dev/null
    $KANBAN complete "$tid" --summary "$LANG_TOTAL Einträge übersetzt" 2>/dev/null
    echo "  ✅ Kanban $tid complete"
  done
}

echo "--- Status ---"
FR=$(check_lang fr); echo "🇫🇷 FR: $FR/$LANG_TOTAL"
EN=$(check_lang en); echo "🇬🇧 EN: $EN/$LANG_TOTAL"
IT=$(check_lang it); echo "🇮🇹 IT: $IT/$LANG_TOTAL"
ES=$(check_lang es); echo "🇪🇸 ES: $ES/$LANG_TOTAL"
ZH=$(check_lang zh); echo "🇨🇳 ZH: $ZH/$LANG_TOTAL"
NL=$(check_lang nl); echo "🇳🇱 NL: $NL/$LANG_TOTAL"
CS=$(check_lang cs); echo "🇨🇿 CS: $CS/$LANG_TOTAL"
echo ""

if [ "$FR" -lt "$LANG_TOTAL" ]; then
  echo "▶️  FRANZÖSISCH"
  bash scripts/translate_language.sh fr
elif [ "$EN" -lt "$LANG_TOTAL" ]; then
  complete_lang_kb "fr"
  echo "▶️  ENGLISCH"
  bash scripts/translate_language.sh en
elif [ "$IT" -lt "$LANG_TOTAL" ]; then
  complete_lang_kb "en"
  echo "▶️  ITALIENISCH"
  bash scripts/translate_language.sh it
elif [ "$ES" -lt "$LANG_TOTAL" ]; then
  complete_lang_kb "it"
  echo "▶️  SPANISCH"
  bash scripts/translate_language.sh es
elif [ "$ZH" -lt "$LANG_TOTAL" ]; then
  complete_lang_kb "es"
  echo "▶️  CHINESISCH"
  bash scripts/translate_language.sh zh
elif [ "$NL" -lt "$LANG_TOTAL" ]; then
  complete_lang_kb "zh"
  echo "▶️  NIEDERLÄNDISCH"
  # Parallel: alle 9 Kategorien gleichzeitig
  cd "$BASE"
  for cat in gastro unterkuenfte orte camping sehenswuerdigkeiten magazin regionen erlebnisse events; do
    $PYTHON_EXE scripts/translate_worker.py "$cat" nl &
  done
  wait
  git add src/data/nl/
  git commit -m "[i18n] NL translations complete"
  git push origin master
elif [ "$CS" -lt "$LANG_TOTAL" ]; then
  complete_lang_kb "nl"
  echo "▶️  TSCHECHISCH"
  bash scripts/translate_language.sh cs
else
  echo "🎉 ALLE FERTIG! 5240 Einträge in 7 Sprachen"
  complete_lang_kb "cs"
fi
echo "============================================"
