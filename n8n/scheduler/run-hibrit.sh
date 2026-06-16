#!/bin/sh
# Günlük HİBRİT pipeline (Gemini kanıt + Claude analiz -> WordPress taslak).
# Sırlar .env'den. Düşük tempo (Gemini ücretsiz kotasını korumak için).
set -eu

DIR="$(cd "$(dirname "$0")" && pwd)"
set -a
[ -f "$DIR/.env" ] && . "$DIR/.env"
set +a
: "${GEMINI_API_KEY:?HATA: GEMINI_API_KEY (.env)}"
: "${ANTHROPIC_API_KEY:?HATA: ANTHROPIC_API_KEY (.env)}"
: "${WP_APP_PASS:?HATA: WP_APP_PASS (.env)}"

LOG="$DIR/hibrit.log"
echo "===== $(date '+%Y-%m-%d %H:%M:%S') hibrit başladı =====" >> "$LOG"

# Kümeleme sonrası zaten ~4-5 farklı haber; tavan 8, küme arası 25s (kota/RPM dostu)
HIBRIT_LIMIT="${HIBRIT_LIMIT:-8}" HIBRIT_SLEEP="${HIBRIT_SLEEP:-25}" \
  python3 "$DIR/../hibrit-pipeline.py" >> "$LOG" 2>&1

echo "===== $(date '+%Y-%m-%d %H:%M:%S') bitti =====" >> "$LOG"
