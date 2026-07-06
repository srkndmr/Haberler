# Hero Arka Plan Görseli — OpenArt AI Prompt

Sitenin hero bandı koyu petrol-yeşili → siyah gradyan (#0e4453 → #062028) +
altın aksan (#b78a3c). Arka plan görseli **koyu, sakin, ortası düşük kontrast**
olmalı ki üstündeki beyaz başlık okunur kalsın. Metin/harf/yüz/bayrak İÇERMEMELİ.

Model önerisi: **FLUX.1** (OpenArt'ta "FLUX" veya "Flux Dev"). En/boy: **16:9**
(1920×1080 veya daha geniş 21:9 / 2560×1080). Kalite: yüksek.

---

## 1) ANA PROMPT (kopyala–yapıştır — İngilizce)

```
A dark, cinematic, editorial background for a legal fact-checking platform.
Deep petrol-teal to near-black gradient (#0e4453 to #062028), matte and moody.
Subtle, elegant motifs barely emerging from shadow: a faint engraved scale of
justice on the right side, overlapping translucent sheets of paper and faint
halftone newsprint texture on the edges, a single soft shaft of cool light
falling diagonally like light revealing truth in darkness. Muted brushed-gold
accents, very restrained. Fine film grain, premium, sophisticated, dignified.
Negative space and low contrast in the center for text overlay. No text, no
letters, no faces, no flags, no logos. Wide aspect, atmospheric depth.
```

## 2) NEGATİF PROMPT

```
text, letters, words, typography, watermark, signature, logo, faces, people,
flags, national symbols, neon, glow, oversaturated, bright center, cluttered
center, cartoon, 3d render, low quality, jpeg artifacts, busy, chaotic
```

## 3) AYARLAR
- **Aspect ratio:** 16:9 (arka plan için 21:9 de güzel durur)
- **Steps:** 30–40 · **Guidance/CFG:** 3–5 (FLUX düşük CFG sever)
- **Adet:** 4 üret, en koyu ve ortası en boş olanı seç
- Çıktı **çok açık/parlak** gelirse prompt'a `darker, low-key lighting` ekle

---

## Alternatif konseptler (istersen dene)

**A — Minimal / dokusal (en güvenli, metin en okunur):**
```
Minimal dark petrol-teal to black gradient background, subtle paper-fiber and
faint halftone dot texture, a thin diagonal beam of soft cool light, restrained
brushed-gold hairline accents near the edges, fine grain, matte, elegant,
lots of empty low-contrast space in the center. No text, no symbols.
```

**B — İçtihat/adalet dokusu (daha anlamlı):**
```
Atmospheric dark background evoking law and scrutiny: faint layered legal
documents and a barely-visible balance scale dissolving into deep teal-black
shadow on the right third, soft volumetric light from top-left, muted gold
highlights, cinematic, sober, high-end editorial. Center kept dark and clean
for overlaid white text. No readable text, no faces, no flags.
```

---

## Siteye koyma (görsel hazır olunca)
Görseli `wp/mu-plugins/` yanına değil, `web` görsellerine koyacağız; sonra hero'ya
CSS ile gradyanın ALTINA, düşük opaklıkta bindiririz (metin okunurluğu için):

```css
.hb-hero{
  background:
    linear-gradient(160deg, rgba(14,68,83,.86), rgba(6,32,40,.94)),
    url("/wp-content/uploads/hero-bg.jpg") center/cover no-repeat;
}
```
Böylece görsel arkada hafifçe görünür, başlık net kalır. Görseli indirince bana
ver, CSS'i ekleyip canlıya alayım.
```
