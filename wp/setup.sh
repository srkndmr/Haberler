#!/bin/sh
# Haberler — WordPress otomatik kurulum (WP-CLI).
# Yerelde:  docker compose run --rm wpcli /build/setup.sh
# Prod'da:  sunucuda wp-cli kurulu ise WP=... değişkenini ayarlayıp çalıştır.
set -eu

WP="wp --path=/var/www/html"

URL="${SITE_URL:-http://localhost:8091}"
TITLE="${SITE_TITLE:-Bağımsız Medya İzleme}"
ADMIN_USER="${ADMIN_USER:-yonetici}"
ADMIN_PASS="${ADMIN_PASS:-yonetici-parola}"
ADMIN_EMAIL="${ADMIN_EMAIL:-yonetici@example.com}"
BOT_PASS="${BOT_PASS:-bot-parola}"

echo "==> Veritabanı bekleniyor..."
i=0
until $WP db check >/dev/null 2>&1; do
  i=$((i+1)); [ "$i" -gt 40 ] && { echo "DB'ye bağlanılamadı"; exit 1; }
  sleep 3
done

echo "==> WordPress kuruluyor (gerekiyorsa)..."
if ! $WP core is-installed >/dev/null 2>&1; then
  $WP core install \
    --url="$URL" --title="$TITLE" \
    --admin_user="$ADMIN_USER" --admin_password="$ADMIN_PASS" --admin_email="$ADMIN_EMAIL" \
    --skip-email
fi

echo "==> Genel ayarlar..."
$WP rewrite structure '/%postname%/' --hard >/dev/null
$WP option update timezone_string 'Europe/Istanbul' >/dev/null
$WP option update blogdescription 'Doğruluk denetimi ve medya izleme' >/dev/null

echo "==> Eklentiler (best-effort; ağ yoksa atlanır)..."
$WP plugin install publishpress fluentform --activate 2>/dev/null \
  || echo "   (eklenti kurulumu atlandı — mu-plugins zaten temel işlevi sağlıyor)"

echo "==> pipeline-bot kullanıcısı (Contributor)..."
if ! $WP user get pipeline-bot >/dev/null 2>&1; then
  $WP user create pipeline-bot bot@example.com --role=contributor --user_pass="$BOT_PASS" >/dev/null
fi

echo "==> pipeline-bot Application Password..."
# Varsa eskiyi temizleyip yeniden üret (porcelain = sadece parolayı yazar)
$WP user application-password delete pipeline-bot --all >/dev/null 2>&1 || true
APP_PASS=$($WP user application-password create pipeline-bot n8n-pipeline --porcelain)
echo "   APP_PASS=$APP_PASS"

echo "==> Hukuk Danışmanı örnek kullanıcısı..."
$WP user get hukukcu >/dev/null 2>&1 || \
  $WP user create hukukcu hukukcu@example.com --role=hukuk_danismani --user_pass="hukukcu-parola" >/dev/null

echo "==> Sayfalar..."
for P in "Günlük İzleme Akışı" "Arşiv" "Metodoloji" "Künye" "İletişim / Düzeltme Talebi"; do
  EXIST=$($WP post list --post_type=page --field=post_title --format=csv 2>/dev/null | grep -Fx "$P" || true)
  if [ -z "$EXIST" ]; then
    $WP post create --post_type=page --post_status=publish \
      --post_title="$P" --post_content="(Taslak içerik — docs/ klasöründen doldurun.)" >/dev/null
  fi
done

# Application Password'ü build dizinine yaz (REST testleri okuyabilsin)
echo "$APP_PASS" > /build/.app_password 2>/dev/null || true

echo ""
echo "============================================================"
echo " Kurulum tamam."
echo "  Site:        $URL"
echo "  Admin:       $ADMIN_USER / $ADMIN_PASS"
echo "  pipeline-bot Application Password: $APP_PASS"
echo "============================================================"
echo " Roller, durumlar, veri alanları ve hukuk kapısı mu-plugins'ten otomatik aktif."
