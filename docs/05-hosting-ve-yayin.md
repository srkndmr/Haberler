# 05 — Hosting Satın Alma + Yayına Çıkış Kontrol Listesi

Bu adımların bir kısmı **yalnızca sizin yapabileceğiniz** işlerdir (hesap açma,
para harcama, alan adı satın alma). Onları ✋ ile işaretledim. Geri kalanını,
erişim/kimlik bilgilerini verdiğiniz anda **ben yapılandırırım**.

## 1. Satın alınacaklar ✋ (sizde)

| # | Kalem | Öneri | Tahmini maliyet |
|---|---|---|---|
| 1 | **Alan adı** | `.org` / `.com` (örn. medyaizleme.org) | ~150-400 ₺/yıl |
| 2 | **WordPress hosting** | cPanel'li paylaşımlı (Turhost/Natro/Hostinger) | ~1.000-2.500 ₺/yıl |
| 3 | **n8n için sunucu** | Küçük VPS (Hetzner CX22 / DigitalOcean 2GB) — WordPress'e kurulamaz | ~4-6 $/ay |
| 4 | **Anthropic API anahtarı** | console.anthropic.com → yeni anahtar + harcama limiti | kullanım kadar (~haber başına 0.1-0.3 cent) |
| 5 | **(Opsiyonel) E-posta** | Brevo/SendGrid ücretsiz katman (bildirimler için) | 0 ₺ |

> Not: n8n'i ayrı VPS yerine **n8n Cloud** ile de alabilirsiniz (kurulum yok, aylık ücret).

## 2. Bana iletmeniz gerekenler ✋

Satın aldıktan sonra şunları (güvenli şekilde) paylaşın:
- Hosting **cPanel** girişi (veya beni "yapılandırıcı" olarak ekleyin)
- Alan adı **DNS panel** erişimi (veya Cloudflare'a ekleyin)
- VPS **SSH** erişimi (n8n için)
- **YENİ** Anthropic anahtarı (sohbete değil; scheduler `.env`'ine ya da Vercel/sunucu env'ine)

## 3. Benim yapacaklarım (erişim gelince)

- [ ] cPanel'de WordPress kurulumu (`docs/00`) + SSL (AutoSSL)
- [ ] `wp/mu-plugins/*` sunucuya kopyalama + `wp/setup.sh` ile rol/kullanıcı/sayfa kurulumu
- [ ] Sayfa içeriklerini girme (`docs/02`, `docs/03`)
- [ ] DNS: alan adını hostinge yönlendirme + `www` + SSL doğrulama
- [ ] VPS'e Docker + n8n kurulumu (`docs/01` Seçenek A)
- [ ] n8n workflow + credential (WP + Anthropic) bağlama, Schedule aktif
- [ ] **VEYA** scheduler ile günlük otomasyon (`n8n/scheduler/`) — WP_URL'yi canlı alan adına çevirerek
- [ ] Düzeltme talebi formu (Fluent Forms) + KVKK metni
- [ ] Üretim duman testi: bir taslak üret → otomatik-taslak → editör/hukuk akışı → yayın

## 4. Yayın öncesi ZORUNLU (kod değil, süreç) ✋

- [ ] **Hukuk danışmanı** belirlendi; Künye'de gerçek isim; Metodoloji avukat onaylı
- [ ] İzlenecek kaynak listesi + anahtar kelimeler son hali (`n8n/` config)
- [ ] KVKK aydınlatma + düzeltme süreci yazılı
- [ ] İlk 5-10 dosya **elle** gözden geçirilip yayınlandı (otomasyona güvenmeden)

## 5. Go-live sırası (özet)

```
Domain+Hosting al → WP kur (setup.sh) → içerik gir → SSL →
VPS+n8n VEYA scheduler → kaynak/anahtar kelime ayarı → Anthropic bağla →
hukuk onayı → duman testi → soft launch (sınırlı) → tam yayın
```

> Tahmini süre (erişimler hazır + hukukçu varsa): **MVP ~8-10 gün**, tam sürüm ~3-4 hafta
> (ayrıntılı kırılım için proje konuşmasındaki faz tablosuna bakın).
