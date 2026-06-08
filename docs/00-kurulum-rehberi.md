# 00 — Kurulum Rehberi (Sıfırdan, Tıkla-Geç)

> Bu rehber teknik olmayan bir ekip içindir. Her adım numaralıdır; sırayla uygula.
> Kod gereken yerlerde hazır kod bloğu verilmiştir — sadece kopyala-yapıştır.
> Toplam süre: ~2-3 saat (DNS yayılması hariç).

İçindekiler:
- [A. Alan adı + Hosting](#a-alan-adı--hosting)
- [B. WordPress.org kurulumu](#b-wordpressorg-kurulumu)
- [C. Eklentilerin kurulumu](#c-eklentilerin-kurulumu)
- [D. Kullanıcı rolleri ve yetkiler](#d-kullanıcı-rolleri-ve-yetkiler)
- [E. İş akışı durumları (PublishPress)](#e-iş-akışı-durumları-publishpress)
- [F. Hukuk kapısı (PublishPress Checklists)](#f-hukuk-kapısı-publishpress-checklists)
- [G. ACF alan grubunu içe aktar](#g-acf-alan-grubunu-içe-aktar)
- [H. Sayfaların oluşturulması](#h-sayfaların-oluşturulması)
- [I. Düzeltme talebi formu](#i-düzeltme-talebi-formu)
- [J. Kurulum sonrası kontrol listesi](#j-kurulum-sonrası-kontrol-listesi)

---

## A. Alan adı + Hosting

WordPress.com **değil**, WordPress.org (kendi sunucunda) kuruyoruz.

1. Bir alan adı al (örn. Namecheap, GoDaddy, İsimtescil). Örnek: `medyaizleme.org`.
2. Bir **paylaşımlı hosting** veya küçük VPS al. Başlangıç için yeterli olanlar:
   - Paylaşımlı: Turhost, Natro, Hostinger (cPanel'li "WordPress hosting" paketi yeterli).
   - VPS (ileride n8n'i de aynı sunucuya kurmak istersen): Hetzner CX22, DigitalOcean 2GB.
   > Not: n8n'i WordPress ile **aynı paylaşımlı hostinge kuramazsın** (Docker/Node gerektirir).
   > n8n için ayrı bir VPS ya da n8n Cloud kullanılacak — bkz. `01-n8n-kurulum-ve-workflow.md`.
3. Hosting panelinde (cPanel) **SSL sertifikası**nı aç: cPanel → *Security* → *SSL/TLS Status* →
   alan adını seç → **Run AutoSSL** (Let's Encrypt, ücretsiz). Sitenin `https://` ile açıldığını doğrula.
4. Alan adının DNS'ini hostinge yönlendir (registrar panelinde nameserver'ları hostingin verdiği
   değerlerle değiştir). Yayılması 1-24 saat sürebilir.

---

## B. WordPress.org kurulumu

1. cPanel'e gir → **Softaculous Apps Installer** (veya "WordPress Manager") → **WordPress** → *Install Now*.
2. Formu doldur:
   - **Choose Protocol:** `https://`
   - **Choose Domain:** alan adın
   - **In Directory:** burayı **boş bırak** (sitenin kökünde olsun: `medyaizleme.org`).
   - **Site Name:** `Bağımsız Medya İzleme`
   - **Site Description:** `Doğruluk denetimi ve medya izleme`
   - **Admin Username:** `yonetici` (asla `admin` kullanma — güvenlik).
   - **Admin Password:** güçlü bir parola üret, bir parola yöneticisine kaydet.
   - **Admin Email:** yöneticinin e-postası.
   - **Select Language:** `Türkçe`
3. *Install* → bitince `https://ALANADI/wp-admin` adresine git, yönetici hesabıyla gir.
4. **Ayarlar → Kalıcı Bağlantılar (Permalinks):** `Yazı adı` (post name) seç, kaydet.
   (REST API ve temiz URL'ler için gerekli.)
5. **Ayarlar → Genel:** Site Başlığı/Slogan'ı doğrula, *Saat Dilimi* = `İstanbul`.
6. (Önerilen) Bir güvenlik eklentisi: **Wordfence Security** (ücretsiz) kur, varsayılan ayarlarla aktif et.

---

## C. Eklentilerin kurulumu

Her biri için: **Eklentiler → Yeni Ekle** → adını ara → *Şimdi Kur* → *Etkinleştir*.

| # | Eklenti | Ne işe yarar |
|---|---|---|
| 1 | **PublishPress Planner** (PublishPress) | Özel iş akışı durumları + bildirimler |
| 2 | **PublishPress Checklists** | Yayın öncesi zorunlu kontrol kutuları (hukuk kapısı) |
| 3 | **PublishPress Capabilities** | Özel rol oluşturma (Hukuk Danışmanı) |
| 4 | **Advanced Custom Fields** (ACF) | Yapılandırılmış "Dosya" alanları |
| 5 | **Fluent Forms** | Düzeltme talebi / iletişim formu |
| 6 | **Wordfence Security** (opsiyonel) | Güvenlik |

> Hepsi ücretsiz katmanlarıyla bu proje için yeterlidir.

---

## D. Kullanıcı rolleri ve yetkiler

### D.1 — `pipeline-bot` kullanıcısı (n8n için, Contributor)

1. **Kullanıcılar → Yeni Ekle**.
2. Kullanıcı adı: `pipeline-bot` · E-posta: çalışan bir adres (örn. `bot@alanadi`).
3. **Rol: Katılımcı (Contributor)** seç. *(Katılımcı yazı oluşturabilir ama YAYINLAYAMAZ.)*
4. *Yeni Kullanıcı Ekle*.
5. **Application Password üret** (ana parola asla otomasyona verilmez):
   - **Kullanıcılar → pipeline-bot → Düzenle** → en altta **Application Passwords**.
   - Ad: `n8n-pipeline` yaz → *Add New Application Password*.
   - Ekrandaki **24 haneli parolayı kopyala** (örn. `abcd EFGH ijkl ...`). Bir daha gösterilmez.
   - Bu parola `01-n8n` rehberinde n8n credentials'a girilecek.

### D.2 — "Hukuk Danışmanı" özel rolü (PublishPress Capabilities)

1. **Capabilities → Add New** (PublishPress Capabilities menüsü).
2. **Role Name:** `Hukuk Danışmanı` · **Role ID:** `hukuk_danismani`.
3. **Copy capabilities from:** `Contributor` (temel al), sonra şu yetkileri **işaretle**:
   - `read`, `edit_posts`, `edit_others_posts`, `edit_published_posts` *(düzenleyebilsin)*
   - `moderate_comments` *(yorum/durum notu bırakabilsin)*
   - **`publish_posts` → KAPALI** *(tek başına yayınlayamasın)*
4. Kaydet. Sonra her hukukçu için: **Kullanıcılar → Yeni Ekle** → rol = **Hukuk Danışmanı**.

> Kod tercih edersen, eklenti yerine bir mu-plugin de kullanabilirsin —
> `wp-content/mu-plugins/roller.php` oluştur:
> ```php
> <?php
> /* Plugin Name: Haberler Rolleri */
> add_action('init', function () {
>     add_role('hukuk_danismani', 'Hukuk Danışmanı', [
>         'read' => true,
>         'edit_posts' => true,
>         'edit_others_posts' => true,
>         'edit_published_posts' => true,
>         'moderate_comments' => true,
>         'publish_posts' => false,   // tek başına yayınlayamaz
>         'delete_posts' => false,
>     ]);
> });
> ```

### D.3 — Yönetici / Editör (tek "Yayınla" yetkisi)

- Yönetici zaten **Administrator**. Yayınlama yetkisi **yalnızca** Administrator ve Editor'dedir.
- Başka kimseye `publish_posts` verme. Yayın kararı tek elde kalsın.

| Rol | Yazı oluştur | Düzenle | Durum değiştir | **Yayınla** |
|---|---|---|---|---|
| `pipeline-bot` (Contributor) | ✅ | kendi taslağı | ❌ | ❌ |
| Hukuk Danışmanı | ✅ | ✅ | ✅ | ❌ |
| Yönetici (Administrator/Editor) | ✅ | ✅ | ✅ | **✅ (tek)** |

---

## E. İş akışı durumları (PublishPress)

Zincir: `Otomatik Taslak` → `Doğrulama` → `Hukuk İncelemesi` → `Yayına Hazır` → `Yayında`

> `Yayında`, WordPress'in yerleşik **Published** durumudur; onu oluşturmuyoruz.
> Diğer 4 durumu özel statü olarak ekliyoruz.

### E.1 — Özel durumları oluştur

1. **PublishPress → Statuses → Add New Status**. Her biri için tekrarla:

   | Durum adı (Name) | Renk önerisi | Açıklama |
   |---|---|---|
   | `Otomatik Taslak` | gri | n8n'in ürettiği ham taslak |
   | `Doğrulama` | sarı | Editör iddiaları/kaynakları kontrol ediyor |
   | `Hukuk İncelemesi` | turuncu | İsim verilen suçlama → hukukçu inceliyor |
   | `Yayına Hazır` | mavi | Onaylandı, yayın bekliyor |

2. Her durumu kaydet. (Slug'lar otomatik: `otomatik-taslak`, `dogrulama`, `hukuk-incelemesi`, `yayina-hazir`.)
   Bu slug'ları not et — n8n ve REST API'de kullanılacak.

### E.2 — Geçiş bildirimleri (PublishPress Notifications)

1. **PublishPress → Notifications → Add New**.
2. Her kritik geçiş için bir bildirim kuralı oluştur:

   | Bildirim | When (event) | Who receives |
   |---|---|---|
   | Yeni taslak geldi | Status changes to **Otomatik Taslak** | Editörler |
   | Doğrulama tamam, hukuk gerek | Status changes to **Hukuk İncelemesi** | Hukuk Danışmanları |
   | Hukuk onayladı | Status changes to **Yayına Hazır** | Yönetici |

3. Her kuralda **Content** sekmesinde konu/gövde şablonunu bırak (varsayılan yeterli),
   **Receivers** sekmesinde ilgili rolü seç. Kaydet.

> SMTP: Bildirim e-postalarının düşmesi için bir SMTP eklentisi (örn. **FluentSMTP**, ücretsiz)
> kurup bir gönderim servisi (Brevo/SendGrid ücretsiz katman) bağlaman önerilir.

---

## F. Hukuk kapısı (PublishPress Checklists)

Amaç: `isim_verilen_suclama = evet` ise, "Hukuk onayı alındı" işaretlenmeden ilerlenemesin.

1. **PublishPress → Checklists**.
2. **Add custom item** → ad: `Hukuk onayı alındı`.
3. Bu maddeyi **Required (zorunlu)** yap ve **"Prevent publishing"** (yayını engelle) seçeneğini aç.
4. (Koşullu zorunluluk) Checklists ücretsiz sürümü "ACF alanına göre koşul" sunmuyorsa,
   maddeyi **her zaman zorunlu** bırak ve editöre talimat ver:
   *"İsim verilen suçlama yoksa bu kutuyu işaretleyip geçebilirsin; varsa yalnızca Hukuk Danışmanı işaretler."*
5. **Daha sağlam (kod ile sert kural):** Aşağıdaki snippet'i `wp-content/mu-plugins/hukuk-kapisi.php`
   dosyasına koy. `isim_verilen_suclama = evet` olan bir yazı, `Hukuk İncelemesi` durumundan
   geçmeden `Yayına Hazır` veya `publish` durumuna **geçemez**:

   ```php
   <?php
   /* Plugin Name: Haberler Hukuk Kapısı */
   add_filter('wp_insert_post_data', function ($data, $postarr) {
       if (($data['post_type'] ?? '') !== 'post') return $data;
       $post_id = $postarr['ID'] ?? 0;
       if (!$post_id) return $data;

       $isim_suclama = get_field('isim_verilen_suclama', $post_id); // 'evet' | 'hayir'
       $hedef = $data['post_status']; // 'yayina-hazir' | 'publish' | ...
       $kilitli = ['yayina-hazir', 'publish'];

       if ($isim_suclama === 'evet' && in_array($hedef, $kilitli, true)) {
           $hukuk_onay = get_post_meta($post_id, '_hukuk_onayi', true); // checklist set eder
           if ($hukuk_onay !== '1') {
               // Hukuk onayı yoksa durumu Hukuk İncelemesi'ne sabitle
               $data['post_status'] = 'hukuk-incelemesi';
           }
       }
       return $data;
   }, 10, 2);
   ```
   > `_hukuk_onayi` meta'sını, Hukuk Danışmanı onayladığında set eden küçük bir kutu/checklist
   > maddesi kullan. (PublishPress Checklists "Hukuk onayı alındı" maddesini bu meta'ya bağlayabilirsin
   > ya da hukukçu için basit bir ACF `true_false` alanı eklersin.)

---

## G. ACF alan grubunu içe aktar

1. **ACF → Araçlar (Tools)** → **Import Field Groups**.
2. `acf/acf-dosya-alan-grubu.json` dosyasını seç → **Import**.
3. **ACF → Field Groups → "Dosya"** açılır. İçinde şunları gör:
   `Özet`, `İsim verilen suçlama var mı?`, `Kaynaklar (repeater)`, `İddialar (repeater)`.
4. Alan grubunda **Settings → Show in REST API = Yes** olduğunu doğrula
   (JSON'da `show_in_rest: 1` ayarlı; n8n'in ACF alanlarını doldurabilmesi için şart).
5. Herhangi bir yazı düzenleme ekranını aç, alanların göründüğünü kontrol et.

---

## H. Sayfaların oluşturulması

**Sayfalar → Yeni Ekle** ile 5 sayfa oluştur (içerik taslakları ayrı dosyalarda):

1. **Günlük İzleme Akışı** — yalnızca `Yayında` dosyalar, tarihe göre.
   - En kolayı: bu sayfayı sitenin **ana sayfası** yap (Ayarlar → Okuma → "Son yazılarınız")
     veya bir "Yazılar" listesi bloğu kullan. Sadece **Published** yazılar görünür (taslaklar görünmez).
2. **Arşiv** — aranabilir/filtrelenebilir.
   - Bir arama bloğu + kategori/etiket filtresi ekle. (İleri düzey filtre için *FacetWP* veya
     *Search & Filter* eklentisi opsiyonel.) Filtre boyutları: kaynak, tarih, sınıflandırma.
3. **Metodoloji** — içeriği `docs/02-metodoloji-sayfasi.md`'den taslak olarak yapıştır.
4. **Künye** — içeriği `docs/03-kunye-sayfasi.md`'den yapıştır (hukukçu adları için yer tutucu).
5. **İletişim / Düzeltme Talebi** — Fluent Forms formunu göm (bkz. bölüm I).

6. **Menü:** Görünüm → Menüler → bu 5 sayfayı ana menüye ekle.

---

## I. Düzeltme talebi formu

1. **Fluent Forms → New Form → Blank Form**.
2. Alanları ekle: `Ad` (text), `E-posta` (email), `İlgili dosya linki` (URL), `Mesaj` (textarea).
3. **Settings → Form Settings:** "Sadece talep topla" — **otomatik yayın/aksiyon yok**.
   E-posta bildirimini yöneticiye yönlendir (Settings → Notifications).
4. Formu kaydet → kısa kodunu kopyala → "İletişim / Düzeltme Talebi" sayfasına yapıştır.
5. KVKK notu ekle: *"Gönderdiğiniz bilgiler yalnızca düzeltme talebinizi değerlendirmek için kullanılır."*

---

## J. Kurulum sonrası kontrol listesi

- [ ] Site `https://` ile açılıyor, SSL geçerli.
- [ ] `pipeline-bot` = Contributor, Application Password üretildi ve kaydedildi.
- [ ] "Hukuk Danışmanı" rolü var, `publish_posts` kapalı.
- [ ] 4 özel durum oluşturuldu, slug'lar not edildi.
- [ ] Geçiş bildirimleri kuruldu, test e-postası düştü.
- [ ] PublishPress Checklists "Hukuk onayı alındı" zorunlu + (varsa) mu-plugin hukuk kapısı aktif.
- [ ] ACF "Dosya" alan grubu içe aktarıldı, **Show in REST API = Yes**.
- [ ] 5 sayfa oluşturuldu, menüye eklendi.
- [ ] Düzeltme talebi formu çalışıyor, otomatik aksiyon yok.
- [ ] **Test:** REST API ile `status=draft` bir yazı gönderildi → "Otomatik Taslak"ta göründü,
      hiçbir şey otomatik yayınlanmadı (bkz. `04-rest-api-payload.md`).

> Sıradaki adım: `01-n8n-kurulum-ve-workflow.md`.
