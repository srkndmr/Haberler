# Haberler — Bağımsız Medya İzleme & Doğruluk Denetimi Platformu

Belirli bir konudaki (bu kurulumda: **FETÖ / Fetullahçı Terör Örgütü** ile ilgili)
haberleri günlük otomatik toplayan, arşivleyen, içindeki somut iddiaları ayıklayan
ve bu iddiaları kanıta karşı test eden bir **doğruluk denetimi (fact-checking)**
ve **medya izleme** platformu.

Yığın: **WordPress.org** (içerik + iş akışı) + **n8n** (otomasyon) + **Anthropic / Claude** (analiz).

---

## 🔒 Değişmez İlkeler (kodun ve sürecin her yerinde geçerli)

1. **AI hâkim değil, analiz asistanıdır.** Her iddia kanıta dayanarak
   `doğru / kısmen doğru / yanlış / doğrulanamaz / görüş` olarak sınıflandırılır;
   her sınıflandırmanın bir **gerekçesi** ve **dayanak kaynağı** olur.
   Emin değilse **`doğrulanamaz`** der. Sonuç önceden belli **değildir**.
2. **Olgu ile yorum ayrılır.** Yorum/değerlendirme cümlesi `görüş` etiketlenir; "yalan" denmez.
3. **İnsan onayı olmadan hiçbir içerik yayınlanmaz.** Otomasyon yalnızca **taslak** üretir.
   Yayın yetkisi teknik olarak bile otomasyona verilmez.
4. **İsim verilen kişi/kurum hakkında ağır niteleme** içeren her dosya,
   yayından önce **zorunlu hukuk incelemesinden** geçer.
5. **Şeffaflık zorunlu:** açık metodoloji sayfası + her dosyada orijinal kaynağa link + kanıt arşivi.
6. **Masumiyet karinesi.** Hukuki/cezai nitelemeler (örgüt üyeliği, suç isnadı) mahkemelerin işidir.
   Platform bunları **kaynağına atfedilen iddialar** olarak ele alır; kendisi suç/üyelik hükmü vermez.

---

## 📁 Dosya rehberi

| Dosya | İçerik | Görev çıktısı |
|---|---|---|
| `docs/00-kurulum-rehberi.md` | Sıfırdan: hosting + WordPress kurulumu + eklenti + rol + iş akışı durumları + ACF + sayfalar (numaralı, tıkla-geç) | 1 |
| `acf/acf-dosya-alan-grubu.json` | ACF "Dosya" alan grubu — içe aktarılabilir JSON | 2 |
| `docs/02-metodoloji-sayfasi.md` | Metodoloji sayfası taslak metni | 3 |
| `docs/03-kunye-sayfasi.md` | Künye sayfası taslak metni | 3 |
| `docs/01-n8n-kurulum-ve-workflow.md` | n8n self-host kurulumu + node-node akış açıklaması + credentials | 4 |
| `n8n/haberler-pipeline.workflow.json` | n8n workflow — içe aktarılabilir iskelet | 4 |
| `prompts/ai-analiz-sistem-promptu.md` | AI analiz adımı sistem promptu + katı JSON şeması | 5 |
| `docs/04-rest-api-payload.md` | WordPress REST API örnek gönderim payload'u + alan eşleme | 6 |
| `wp/` | **Çalışan inşa:** Docker test ortamı + WP-CLI setup + drop-in mu-plugins (roller, durumlar, veri, hukuk kapısı). 5/5 test geçti. Bkz. `wp/README.md` | — |

## ⚡ Hızlı başlangıç (çalışan yerel kurulum)

```bash
cd wp
docker compose up -d
docker compose run --rm -e SITE_URL=http://localhost:8091 wpcli /build/setup.sh
# → http://localhost:8091/wp-admin   (yonetici / yonetici-parola)
```
Roller, özel durumlar, REST'e açık veri alanları ve hukuk kapısı mu-plugin'lerden
otomatik aktif olur. Detay ve doğrulama testleri: `wp/README.md`.

## 🚦 Önerilen kurulum sırası

1. `docs/00-kurulum-rehberi.md` → WordPress'i ayağa kaldır, rolleri/durumları/ACF'yi kur.
2. `acf/acf-dosya-alan-grubu.json` → ACF'ye içe aktar.
3. `docs/02-metodoloji-sayfasi.md` + `docs/03-kunye-sayfasi.md` → sayfaları taslak olarak gir.
4. `docs/01-n8n-kurulum-ve-workflow.md` + `n8n/haberler-pipeline.workflow.json` → n8n'i kur, workflow'u içe aktar.
5. `prompts/ai-analiz-sistem-promptu.md` → AI node'una promptu yapıştır.
6. `docs/04-rest-api-payload.md` → REST gönderimini test et.

## İş akışı durum zinciri

`Otomatik Taslak` → `Doğrulama` → `Hukuk İncelemesi` → `Yayına Hazır` → `Yayında`

> **Sert kural:** ACF'de `isim_verilen_suclama = evet` olan bir dosya,
> `Hukuk İncelemesi` durumundan ve "Hukuk onayı alındı" kontrol kutusundan
> geçmeden `Yayına Hazır`a **geçemez**.
