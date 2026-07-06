#!/bin/sh
# Günlük RAG arşiv güncellemesi: makaleler + transkriptler + embedding.
# hibrit pipeline'dan ÖNCE çalışır ki Claude güncel referans arşivini kullansın.
# Sırlar .env'den (GEMINI_API_KEY embedding için).
set -eu

DIR="$(cd "$(dirname "$0")" && pwd)"
set -a
[ -f "$DIR/.env" ] && . "$DIR/.env"
set +a
: "${GEMINI_API_KEY:?HATA: GEMINI_API_KEY (.env)}"

RAG="$DIR/../../rag"
LOG="$DIR/rag.log"
echo "===== $(date '+%Y-%m-%d %H:%M:%S') RAG güncelleme başladı =====" >> "$LOG"

python3 "$RAG/ingest_all.py" >> "$LOG" 2>&1

echo "===== $(date '+%Y-%m-%d %H:%M:%S') bitti =====" >> "$LOG"
