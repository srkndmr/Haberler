#!/bin/sh
# Linkten Haber İncele — izleyici (sürekli). WP kuyruğunu yoklar, işleri Opus ile analiz eder.
set -eu

DIR="$(cd "$(dirname "$0")" && pwd)"
set -a
[ -f "$DIR/.env" ] && . "$DIR/.env"
set +a
: "${ANTHROPIC_API_KEY:?HATA: ANTHROPIC_API_KEY (.env)}"
: "${WP_APP_PASS:?HATA: WP_APP_PASS (.env)}"

LOG="$DIR/incele.log"
echo "===== $(date '+%Y-%m-%d %H:%M:%S') izleyici başladı =====" >> "$LOG"
exec python3 "$DIR/../incele_watch.py" --loop "${INCELE_SLEEP:-20}" >> "$LOG" 2>&1
