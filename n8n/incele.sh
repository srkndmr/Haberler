#!/bin/sh
# Haber linkini incele: URL'yi çek → kanıt + RAG → Claude analiz → WordPress taslak.
# Kullanım:  sh incele.sh "https://ornek-haber-sitesi.com/haber-linki"
set -eu
DIR="$(cd "$(dirname "$0")" && pwd)"
set -a; [ -f "$DIR/scheduler/.env" ] && . "$DIR/scheduler/.env"; set +a
if [ $# -lt 1 ]; then
  echo "Kullanım: sh incele.sh \"<haber linki>\""; exit 1
fi
HIBRIT_RAG="${HIBRIT_RAG:-1}" python3 "$DIR/hibrit-pipeline.py" "$1"
