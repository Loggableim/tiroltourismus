#!/usr/bin/env bash
# Catch-up: Parallele Worker für die größten Übersetzungs-Lücken
# Startet je Sprache einen Worker für die größte Collection.
# Läuft im Hintergrund, loggt nach /tmp/tirol_catchup_<lang>.log

cd /f/tiroltourismus || exit 1

# Sprache:Collection Paare mit den größten Lücken
declare -a JOBS=(
  "zh:gastro"
  "cs:gastro"
  "es:gastro"
  "en:unterkuenfte"
  "nl:gastro"
  "it:gastro"
  "zh:orte"
  "es:orte"
)

for job in "${JOBS[@]}"; do
  lang="${job%%:*}"
  coll="${job##*:}"
  nohup python scripts/translate_worker.py "$coll" "$lang" --limit 400 >> "/tmp/tirol_catchup_${lang}_${coll}.log" 2>&1 &
  echo "started: $lang/$coll (pid $!)"
  sleep 2  # Stagger to avoid API burst
done

echo "all workers started"
