# wp/ — Çalışan WordPress İnşası (yerel + prod-hazır kod)

Bu klasör, platformun **kodla kurulan** halidir: elle tıklama yerine drop-in
mu-plugin'ler + WP-CLI scripti + yerel Docker test ortamı. `docs/00-kurulum-rehberi.md`
elle kurulum içindir; burası onun otomatik/kodlu karşılığıdır.

## İçerik

```
wp/
├── docker-compose.yml          # WordPress + MariaDB + WP-CLI (yerel test)
├── setup.sh                    # WP-CLI otomatik kurulum (rol/kullanıcı/sayfa/permalink)
└── mu-plugins/                 # Drop-in eklentiler (her ortamda otomatik aktif)
    ├── haberler-roller.php         # "Hukuk Danışmanı" rolü (publish YOK)
    ├── haberler-durumlar.php       # Özel durumlar: Otomatik Taslak/Doğrulama/Hukuk İncelemesi/Yayına Hazır
    ├── haberler-veri.php           # Dosya alanları = post meta (REST'e açık) + admin kutusu  [ACF PRO GEREKMEZ]
    ├── haberler-hukuk-kapisi.php   # isim_verilen_suclama=evet → onaysız yayın ENGELLİ
    └── haberler-otomatik-durum.php # pipeline-bot taslakları → "Otomatik Taslak"
```

## Veri katmanı kararı: ücretsiz meta (ACF PRO değil)

Görevdeki "ücretsiz katman" hedefi için dikkat: ACF'nin **repeater** alanı
(kaynaklar + iddialar) **ACF PRO** özelliğidir; ücretsiz ACF desteklemez.
Bu yüzden çalışan inşa, veriyi **post meta** olarak tutar (`haberler-veri.php`):

| Alan (meta key) | Tip | REST |
|---|---|---|
| `haberler_ozet` | metin | açık |
| `haberler_isim_verilen_suclama` | `evet`/`hayir` | açık |
| `haberler_isim_suclama_gerekce` | metin | açık |
| `haberler_kaynaklar` | **JSON string** (çoklu mecra) | açık |
| `haberler_iddialar` | **JSON string** (iddia+sınıflandırma) | açık |
| `_hukuk_onayi` | `0`/`1` | KAPALI (sadece yetkili rol) |

> **ACF PRO alırsanız:** `acf/acf-dosya-alan-grubu.json`'u içe aktarıp repeater'ları
> kullanabilirsiniz; o zaman n8n payload'unda `meta` yerine `acf` anahtarı gönderin.
> İki yol da `docs/04-rest-api-payload.md`'de.

## Yerelde çalıştırma (Docker)

```bash
cd wp
docker compose up -d
docker compose run --rm -e SITE_URL=http://localhost:8091 wpcli /build/setup.sh
```

- Site:  http://localhost:8091  ·  Admin: `http://localhost:8091/wp-admin`
- Yönetici: `yonetici` / `yonetici-parola`
- Hukukçu (örnek): `hukukcu` / `hukukcu-parola`  (rol: Hukuk Danışmanı)
- pipeline-bot: Contributor — setup çıktısındaki **Application Password**'ü kullanın.

Kapatma / sıfırlama:
```bash
docker compose down       # durdur (veri kalır)
docker compose down -v    # tamamen sıfırla (volume sil)
```

## Doğrulama (otomatik test — hepsi GEÇTİ ✅)

Temiz volume'den kurulup şu 5 kontrol koşuldu, **5/5 GEÇTİ**:

| # | Test | Beklenen | Sonuç |
|---|---|---|---|
| A1 | Bot REST ile taslak + meta gönderir | `kaynaklar` meta REST'te roundtrip | ✅ |
| A2 | Bot taslağının durumu | `otomatik-taslak`'a çevrilir | ✅ |
| B1 | `isim=evet`, onay YOK iken `publish` | `hukuk-incelemesi`ne geri döner | ✅ |
| B2 | `_hukuk_onayi=1` sonrası `publish` | `publish` olur | ✅ |
| C  | Bot (Contributor) `status:publish` dener | `rest_cannot_publish` (403) | ✅ |

Yani üç değişmez güvence kanıtlandı: **otomasyon yayınlayamaz**, **bot çıktısı
otomatik taslağa düşer**, **isim verilen suçlama hukuk onayı olmadan yayınlanamaz**.

## Prod'a taşıma notları

1. **mu-plugins**: `wp/mu-plugins/*.php` → sunucuda `wp-content/mu-plugins/`'e kopyala.
   Hiçbir aktivasyon gerekmez; otomatik yüklenir.
2. **setup.sh**: Sunucuda WP-CLI varsa `SITE_URL=https://alanadi ./setup.sh` ile çalıştır
   (veya `docs/00`'daki elle adımları izle).
3. **`WP_ENVIRONMENT_TYPE`**: Yerelde `local` **gerekli** (Application Password'ler
   HTTP'de yalnızca `local` ortamda çalışır). **Prod'da HTTPS** olduğu için bu satıra
   gerek yoktur; ortam `production` kalabilir.
4. **ACF**: İstersen ACF PRO + `acf/...json`; istemezsen meta yolu zaten yeterli.
5. **PublishPress** (opsiyonel): bildirim/akış arayüzü için. Durumlar zaten mu-plugin'den
   geldiği için PublishPress olmadan da iş akışı çalışır.

## Sorun giderme

- **REST `rest_not_logged_in` / `rest_cannot_create` (bot auth çökmesi):**
  Ortam `production` + HTTP ise Application Password reddedilir. Yerelde
  `WP_ENVIRONMENT_TYPE=local` (compose'da ayarlı) olduğundan emin ol; prod'da HTTPS kullan.
- **`wp config` "not writable":** wp-config kök kullanıcıya ait olabilir; biz env
  değişkeni kullandığımız için dosya düzenlemeye gerek yok.
- **Uploads yazılamıyor uyarısı:** görsel yükleme için `wp-content/uploads` izinleri;
  testleri etkilemez.
