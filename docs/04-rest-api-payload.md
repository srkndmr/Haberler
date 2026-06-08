# 06 — WordPress REST API: Örnek Gönderim Payload'u

> n8n'in `pipeline-bot` Application Password'ü ile WordPress'e nasıl **taslak** dosya
> göndereceğini gösterir. **Her zaman `status: draft`** — asla `publish`.

## Ön koşullar
- ACF "Dosya" alan grubunda **Show in REST API = Yes** (içe aktarılan JSON'da ayarlı).
- `pipeline-bot` kullanıcısının **Application Password**'ü üretilmiş (bkz. `00-kurulum-rehberi.md`, D.1).
- Kimlik doğrulama: HTTP **Basic Auth** → `Authorization: Basic base64(pipeline-bot:UYGULAMA_PAROLASI)`.

## Uç nokta
```
POST https://ALANADI/wp-json/wp/v2/posts
Content-Type: application/json
Authorization: Basic <base64(pipeline-bot:uygulama parolası)>
```

## İki veri yolu

- **Ücretsiz (varsayılan, test edildi):** veriyi `meta` ile gönder. `kaynaklar` ve
  `iddialar` **JSON string** olarak gider. `wp/mu-plugins/haberler-veri.php` bunları
  REST'e açar. ACF PRO gerektirmez.
- **ACF PRO:** `acf/acf-dosya-alan-grubu.json` içe aktarılırsa `acf` anahtarıyla
  gönder (repeater nesne dizileri). Aşağıda her iki örnek de var.

## Örnek payload — ÜCRETSİZ `meta` yolu (test edildi ✅)

```json
{
  "title": "İddia: X kişisi hakkında örgüt bağlantısı öne sürüldü (2 mecra)",
  "status": "draft",
  "content": "Bu dosya otomatik üretilmiş bir TASLAKTIR. Editör/hukuk incelemesi bekliyor.",
  "meta": {
    "haberler_ozet": "İki haber sitesi, bir kişinin geçmişte bir yapıyla bağlantılı olduğunu öne sürdü.",
    "haberler_isim_verilen_suclama": "evet",
    "haberler_isim_suclama_gerekce": "X adlı kişiye örgüt bağlantısı isnadı; hukuk incelemesi gerekir.",
    "haberler_kaynaklar": "[{\"kaynak_adi\":\"Örnek Gazete A\",\"orijinal_url\":\"https://ornek-a.example/haber/123\",\"yayin_tarihi\":\"2026-06-01\",\"arsiv_url\":\"https://web.archive.org/web/2026/https://ornek-a.example/haber/123\"},{\"kaynak_adi\":\"Örnek Gazete B\",\"orijinal_url\":\"https://ornek-b.example/haber/456\",\"yayin_tarihi\":\"2026-06-01\"}]",
    "haberler_iddialar": "[{\"iddia_metni\":\"X kişisi 2014 yılında ByLock kullandı.\",\"siniflandirma\":\"dogrulanamaz\",\"gerekce\":\"Kesinleşmiş mahkeme kararına/belgeye dayandırılmamış.\",\"dayanak_kaynak_url\":\"\"}]"
  }
}
```

> `meta` içindeki `haberler_kaynaklar` ve `haberler_iddialar` değerleri **string**'tir
> (JSON'un string'e gömülü hali). n8n'de `JSON.stringify(...)` ile üretilir.
> Gönderim sonrası sunucu hook'u (`haberler-otomatik-durum.php`) durumu otomatik
> `otomatik-taslak`'a çeker.

## Örnek payload — ACF PRO `acf` yolu (alternatif)

```json
{
  "title": "İddia: X kişisi hakkında örgüt bağlantısı öne sürüldü (5 mecra)",
  "status": "draft",
  "content": "Bu dosya otomatik üretilmiş bir TASLAKTIR. Editör/hukuk incelemesi bekliyor.",
  "acf": {
    "ozet": "Beş haber sitesi, bir kişinin geçmişte bir yapıyla bağlantılı olduğunu öne sürdü. İddia tek bir ilk kaynağa dayanıyor; resmi belge sunulmamış.",
    "isim_verilen_suclama": "evet",
    "isim_verilen_suclama_gerekce": "X adlı kişiye örgüt bağlantısı/suç isnadı yöneltiliyor; zorunlu hukuk incelemesi gerekir.",
    "kaynaklar": [
      {
        "kaynak_adi": "Örnek Gazete A",
        "orijinal_url": "https://ornek-a.example/haber/123",
        "yayin_tarihi": "2026-06-01",
        "arsiv_url": "https://web.archive.org/web/2026/https://ornek-a.example/haber/123",
        "ekran_goruntusu": ""
      },
      {
        "kaynak_adi": "Örnek Gazete B",
        "orijinal_url": "https://ornek-b.example/haber/456",
        "yayin_tarihi": "2026-06-01",
        "arsiv_url": "https://web.archive.org/web/2026/https://ornek-b.example/haber/456",
        "ekran_goruntusu": ""
      }
    ],
    "iddialar": [
      {
        "iddia_metni": "X kişisi 2014 yılında ByLock kullandı.",
        "siniflandirma": "dogrulanamaz",
        "gerekce": "İddia kesinleşmiş bir mahkeme kararına veya bağımsız belgeye dayandırılmamış.",
        "dayanak_kaynak_url": ""
      },
      {
        "iddia_metni": "Bu kişi sabahları yürüyüş yapıyordu.",
        "siniflandirma": "gorus",
        "gerekce": "Olguyla ilgisiz/önemsiz; değerlendirme niteliğinde.",
        "dayanak_kaynak_url": ""
      }
    ]
  }
}
```

> **Not (ekran_goruntusu alanı):** ACF `image` alanı REST üzerinden **medya kütüphanesi ID'si**
> (tam sayı) bekler. Görseli önce `POST /wp-json/wp/v2/media` ile yükle, dönen `id`'yi buraya yaz.
> Sadece URL saklamak istiyorsan ACF alanını `image` yerine `url` tipine çevirebilirsin.

## cURL ile test

```bash
AUTH=$(printf 'pipeline-bot:UYGULAMA PAROLASI' | base64)

curl -sS -X POST "https://ALANADI/wp-json/wp/v2/posts" \
  -H "Authorization: Basic ${AUTH}" \
  -H "Content-Type: application/json" \
  -d @ornek-payload.json
```

Başarılı yanıt: `201 Created` + JSON içinde `"status": "draft"`.
→ WordPress yönetiminde yazı **Taslak** olarak görünür; ana sayfada/akışta **görünmez**.

## PublishPress özel durumunu set etme ("Otomatik Taslak")

Yerleşik `status: draft` taslağı oluşturur. PublishPress'in özel durumu (`otomatik-taslak`)
ayrıca işaretlemek istersen iki yol var:

1. **Basit:** Taslak kalsın; editör panelde durumu elle "Otomatik Taslak"a alsın.
2. **Otomatik (kod):** WP'de bir mu-plugin ile yeni `pipeline-bot` taslaklarını
   `otomatik-taslak` durumuna çek:

```php
<?php
/* Plugin Name: Haberler Otomatik Durum */
add_action('rest_after_insert_post', function ($post, $request, $creating) {
    if (!$creating) return;
    $author = get_post_field('post_author', $post->ID);
    $bot = get_user_by('login', 'pipeline-bot');
    if ($bot && (int)$author === (int)$bot->ID) {
        // Yeni bot taslağını özel duruma al (publish DEĞİL)
        wp_update_post(['ID' => $post->ID, 'post_status' => 'otomatik-taslak']);
    }
}, 10, 3);
```

## Güvenlik / değişmez kurallar
- Payload'da `status` **her zaman** `"draft"`; n8n workflow'unda `"publish"` hiç geçmez.
- Kimlik bilgisi yalnızca n8n Credentials'ta; bu repoda/kodda anahtar yok.
- `isim_verilen_suclama: "evet"` olan dosyalar, hukuk kapısı (bkz. `00`, bölüm F) nedeniyle
  insan onayı + hukuk incelemesi olmadan yayınlanamaz.
