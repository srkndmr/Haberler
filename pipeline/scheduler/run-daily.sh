#!/bin/sh
# Günlük doğruluk denetimi pipeline'ı (zamanlanmış çalıştırıcı).
# Kanıtlanmış canli-pipeline-test.py'yi sırlar .env'den okuyarak çalıştırır.
# WordPress'e HER ZAMAN draft gönderir (sunucu hook'u otomatik-taslak'a çeker).
set -eu

DIR="$(cd "$(dirname "$0")" && pwd)"
[ -f "$DIR/.env" ] && . "$DIR/.env"

: "${ANTHROPIC_API_KEY:?HATA: ANTHROPIC_API_KEY tanımlı değil (.env oluşturun)}"
: "${WP_APP_PASS:?HATA: WP_APP_PASS tanımlı değil (.env oluşturun)}"

LOG="$DIR/pipeline.log"
echo "===== $(date '+%Y-%m-%d %H:%M:%S') çalıştırılıyor =====" >> "$LOG"

ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-claude-haiku-4-5-20251001}" \
WP_URL="${WP_URL:-http://localhost:8091}" \
WP_USER="${WP_USER:-pipeline-bot}" \
WP_APP_PASS="$WP_APP_PASS" \
LIMIT="${LIMIT:-10}" \
python3 "$DIR/../canli-pipeline-test.py" >> "$LOG" 2>&1

echo "===== $(date '+%Y-%m-%d %H:%M:%S') bitti =====" >> "$LOG"
