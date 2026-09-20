#!/usr/bin/env bash
# Drain: Kontinuierliche Worker bis alle Lücken gefüllt sind.
# Startet je Sprache:Collection einen Worker mit hohem Limit.
# Läuft im Hintergrund, loggt nach /tmp/tirol_drain_<lang>_<coll>.log

cd /f/tiroltourismus || exit 1

# Größte verbleibende Lücken (Stand: nach erstem Catch-up)
declare -a JOBS=(
  "zh:gastro"
  "cs:gastro"
  "es:gastro"
  "en:unterkuenfte"
  "nl:gastro"
  "it:gastro"
  "en:camping"
  "zh:orte"
)

for job in "${JOBS[@]}"; do
  lang="${job%%:*}"
  coll="${job##*:}"
  nohup python scripts/translate_worker.py "$coll" "$lang" --limit 1500 >> "/tmp/tirol_drain_${lang}_${coll}.log" 2>&1 &
  echo "started: $lang/$coll (pid $!)"
  sleep 2
done

echo "all drain workers started"
