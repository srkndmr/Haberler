# Zamanlanmış Otomasyon (günlük pipeline)

Kanıtlanmış `n8n/canli-pipeline-test.py` akışını **her gün otomatik** çalıştırır:
RSS çek → FETÖ filtresi → Claude analiz → WordPress **otomatik-taslak**.

> Bu, n8n grafiğinin tam UI kurulumuna alternatif, **hemen çalışan** yoldur.
> n8n grafiği iskelet olduğu için (scrape extractor, arşiv ayrıştırma vb. UI'da
> tamamlanmalı), günlük otomasyonu bu script ile başlatmak en hızlısıdır.

## Açma (3 adım — anahtarınız yenilenince)

1. **Sırları gir:**
   ```bash
   cd /Users/apple/Haberler/n8n/scheduler
   cp .env.example .env
   # .env'i düzenle: YENİ Anthropic anahtarı + pipeline-bot Application Password
   ```
2. **Elle test et** (önce bir kez):
   ```bash
   sh run-daily.sh && tail -n 30 pipeline.log
   ```
3. **Günlük zamanla (macOS launchd, 07:00):**
   ```bash
   cp com.haberler.pipeline.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.haberler.pipeline.plist
   ```

## Durdurma
```bash
launchctl unload ~/Library/LaunchAgents/com.haberler.pipeline.plist
```

## Notlar
- `.env` **git'e girmez** (gitignore). Anahtarı asla repoya yazmayın.
- `LIMIT` ile günlük işlenecek dosya sayısını sınırlayın (maliyet kontrolü).
- Loglar: `pipeline.log`, `launchd.out.log`, `launchd.err.log` (hepsi gitignore).
- Prod'da: WordPress URL'sini (`WP_URL`) canlı alan adıyla değiştirin; scheduler'ı
  WP/n8n sunucusunda cron veya systemd timer ile kurun.
- **Alternatif (n8n UI):** Workflow zaten içe aktarıldı + WP credential bağlı.
  n8n arayüzünde (http://localhost:5678) Anthropic credential'ını ekleyip
  Schedule node'unu aktif ederseniz aynı işi n8n yürütür.
