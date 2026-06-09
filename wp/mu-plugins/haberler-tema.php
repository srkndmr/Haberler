<?php
/**
 * Plugin Name: Haberler — Tema / Özel CSS
 * Description: Ön yüz tasarım katmanı (editör tipografisi, masthead, dosya değerlendirme kutusu,
 *              fact-check kartları, sınıflandırma rozetleri, arşiv). Tema bağımsız.
 *              Not: Üretimde fontları self-host edin (KVKK/gizlilik).
 */
if (!defined('ABSPATH')) exit;

// Editör fontları
add_action('wp_head', function () {
    echo '<link rel="preconnect" href="https://fonts.googleapis.com">';
    echo '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>';
    echo '<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600;6..72,700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">';
}, 5);

add_action('wp_head', function () {
    ?>
<style id="haberler-tema">
:root{
  --hb-ink:#11181c; --hb-text:#2a3036; --hb-muted:#646e78; --hb-line:#e7e9ec;
  --hb-bg:#ffffff; --hb-soft:#f6f7f9; --hb-accent:#0f4c5c; --hb-accent2:#0a6b5e;
  --serif:"Newsreader",Georgia,"Times New Roman",serif;
  --sans:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
  --c-dogru:#1a7f37; --c-kismen:#9a6700; --c-yanlis:#cf222e; --c-dogrulanamaz:#57606a; --c-mesnetsiz:#c2410c; --c-gorus:#7c3aed;
  --shadow:0 1px 2px rgba(16,24,40,.05),0 8px 24px -16px rgba(16,24,40,.18);
}
body{ color:var(--hb-text); background:var(--hb-bg); font-family:var(--sans);
  line-height:1.7; -webkit-font-smoothing:antialiased; font-size:17px; }
a{ color:var(--hb-accent); text-underline-offset:2px; } a:hover{ color:var(--hb-accent2); }

/* Masthead (tema başlığı + menü) */
.wp-block-site-title{ font-family:var(--serif)!important; font-weight:700; letter-spacing:-.01em; }
.wp-block-site-title a{ color:var(--hb-ink)!important; text-decoration:none; }
.wp-block-navigation{ font-family:var(--sans); font-weight:500; font-size:.92rem; }
.wp-block-navigation__container{ flex-wrap:wrap; }
.wp-block-navigation a{ color:var(--hb-text)!important; }
header.wp-block-template-part, .wp-site-blocks > header{ border-bottom:1px solid var(--hb-line); }
/* Tema'nın varsayılan footer'ını (demo linkler + "Designed with WordPress") gizle;
   yalnızca kendi footer'ımız (footer.hb-footer) kalsın */
footer.wp-block-template-part{ display:none !important; }

/* Başlıklar + okuma kolonu */
.entry-title, .wp-block-post-title{ font-family:var(--serif); font-weight:700; letter-spacing:-.018em;
  line-height:1.18; color:var(--hb-ink); font-size:clamp(1.9rem,4vw,2.7rem); max-width:880px; margin-inline:auto; }
.entry-content, .wp-block-post-content{ font-size:1.12rem; color:var(--hb-text); }
/* Anasayfada tema sayfa başlığını gizle (hero kendi başlığını taşır) */
.home .wp-block-post-title, .home .entry-title{ display:none; }
/* Anasayfada tema'nın çift büyük üst boşluğunu kıs */
.home main.wp-block-group{ margin-top:1.2rem !important; }
.home main .wp-block-group.alignfull.has-global-padding{ padding-top:0 !important; }
.entry-content h2, .wp-block-post-content h2{ font-family:var(--serif); color:var(--hb-ink); font-weight:600;
  font-size:1.5rem; letter-spacing:-.01em; margin-top:2.1rem; padding-bottom:.3rem; border-bottom:2px solid var(--hb-soft); }
.entry-content p{ margin:.9rem 0; }

/* İkonlar (ince çizgi) */
.hb-ic{ width:1.05em; height:1.05em; vertical-align:-.16em; margin-right:.45em; color:var(--hb-accent); }
.hb-verdict__kicker .hb-ic{ width:1em; height:1em; margin-right:.35em; }

/* ---- Dosya ---- */
.hb-dosya{ max-width:740px; margin:2.2rem auto 0; }
.hb-disclaimer{ font-size:.92rem; border-radius:12px; padding:12px 16px; margin:12px 0 18px; }
.hb-disclaimer--top{ background:#fff8e6; border:1px solid #f3d27a; color:#6b5200; }
.hb-disclaimer--bottom{ background:var(--hb-soft); border:1px solid var(--hb-line); color:var(--hb-muted); font-size:.88rem; }

/* Değerlendirme kutusu (verdict) */
.hb-verdict{ background:linear-gradient(180deg,#fbfdfd, #f2f7f7); border:1px solid #d8e6e6;
  border-radius:16px; padding:18px 20px; margin:18px 0 24px; box-shadow:var(--shadow); }
.hb-verdict__kicker{ font-size:.74rem; font-weight:700; letter-spacing:.1em; color:var(--hb-accent); }
.hb-verdict__chips{ margin:10px 0 6px; display:flex; flex-wrap:wrap; gap:6px; }
.hb-verdict__note{ font-size:.86rem; color:var(--hb-muted); }

.hb-gd{ background:#eef4f4; border-left:4px solid var(--hb-accent); border-radius:0 12px 12px 0;
  padding:16px 20px; line-height:1.75; font-size:1.05rem; }

/* Lejant */
.hb-legend{ font-size:.86rem; background:var(--hb-soft); border:1px solid var(--hb-line);
  border-radius:12px; padding:12px 16px; margin:12px 0 18px; }
.hb-legend-row{ margin:5px 0; color:var(--hb-muted); }

/* İddia kartları */
.hb-iddia{ border:1px solid var(--hb-line); border-left-width:5px; border-radius:14px;
  padding:16px 18px; margin:16px 0; background:#fff; box-shadow:var(--shadow); }
.hb-iddia__metin{ font-family:var(--serif); font-weight:600; color:var(--hb-ink); margin:.6rem 0 .5rem;
  font-size:1.2rem; line-height:1.4; }
.hb-iddia__satir{ margin:.4rem 0; color:var(--hb-text); font-size:1rem; }
.hb-iddia__satir b{ color:var(--hb-ink); font-weight:600; }
.hb-iddia__dayanak{ font-size:.9rem; }
.hb-iddia--dogru{ border-left-color:var(--c-dogru); } .hb-iddia--kismen_dogru{ border-left-color:var(--c-kismen); }
.hb-iddia--yanlis{ border-left-color:var(--c-yanlis); } .hb-iddia--dogrulanamaz{ border-left-color:var(--c-dogrulanamaz); }
.hb-iddia--mesnetsiz{ border-left-color:var(--c-mesnetsiz); } .hb-iddia--gorus{ border-left-color:var(--c-gorus); }

/* Rozet (pill) */
.hb-chip{ display:inline-block; color:#fff; font-size:.74rem; font-weight:600; font-family:var(--sans);
  letter-spacing:.01em; padding:4px 11px; border-radius:999px; margin:0 4px 2px 0; }
.hb-chip--dogru{ background:var(--c-dogru); } .hb-chip--kismen_dogru{ background:var(--c-kismen); }
.hb-chip--yanlis{ background:var(--c-yanlis); } .hb-chip--dogrulanamaz{ background:var(--c-dogrulanamaz); }
.hb-chip--mesnetsiz{ background:var(--c-mesnetsiz); } .hb-chip--gorus{ background:var(--c-gorus); }

/* Kaynaklar (pill liste) */
.hb-kaynaklar{ list-style:none; padding:0; margin:.6rem 0; display:flex; flex-direction:column; gap:8px; }
.hb-kaynaklar li{ background:var(--hb-soft); border:1px solid var(--hb-line); border-radius:10px; padding:10px 14px; }
.hb-kaynaklar strong{ color:var(--hb-ink); }

/* ---- Akış / arşiv kartı ---- */
.hb-ozet-kart{ margin:.5rem 0 .2rem; color:var(--hb-text); }
.hb-kaynak-sayi{ font-size:.84rem; color:var(--hb-muted); }
.hb-filtre{ display:flex; gap:12px; flex-wrap:wrap; align-items:end; margin:1.2rem 0;
  padding:16px; background:var(--hb-soft); border:1px solid var(--hb-line); border-radius:14px; }
.hb-filtre label{ font-size:.82rem; font-weight:500; color:var(--hb-muted); }
.hb-filtre select, .hb-filtre input{ padding:8px 10px; border:1px solid #ccd2d8; border-radius:10px; background:#fff; font-family:var(--sans); }
.hb-btn{ padding:9px 20px; background:var(--hb-accent); color:#fff; border:0; border-radius:10px; cursor:pointer; font-weight:600; }
.hb-btn:hover{ background:var(--hb-accent2); }
.hb-kart{ border:1px solid var(--hb-line); border-radius:16px; padding:18px 20px; margin:16px 0;
  background:#fff; box-shadow:var(--shadow); transition:transform .12s,box-shadow .12s; }
.hb-kart:hover{ transform:translateY(-2px); box-shadow:0 14px 30px -18px rgba(16,24,40,.35); }
.hb-kart__baslik{ font-family:var(--serif); font-size:1.25rem; font-weight:600; color:var(--hb-ink); text-decoration:none; line-height:1.3; }
.hb-kart__baslik:hover{ color:var(--hb-accent); }
.hb-kart__meta{ font-size:.82rem; color:var(--hb-muted); margin:6px 0 10px; }

/* ---- Hero (ana sayfa) ---- */
.home .wp-block-post-content{ padding-top:.5rem; }
.hb-hero{ max-width:820px; margin:.5rem auto 1.5rem; text-align:center !important; padding:.5rem 1rem 0; }
.hb-hero > *, .hb-hero p, .hb-hero h1{ text-align:center !important; margin-left:auto; margin-right:auto; }
.hb-hero__kicker{ font-size:.78rem; font-weight:700; letter-spacing:.14em;
  color:var(--hb-accent); margin:0 0 .6rem; }
.hb-hero__title{ font-family:var(--serif); font-weight:700; letter-spacing:-.02em; line-height:1.12;
  font-size:clamp(2rem,5vw,3.1rem); color:var(--hb-ink); margin:.2rem auto .8rem; text-wrap:balance; }
.hb-hero__sub{ font-size:1.12rem; color:var(--hb-muted); max-width:52ch; margin:0 auto 1.2rem;
  text-align:center; text-wrap:balance; }
.hb-hero__actions{ display:flex; gap:20px; justify-content:center; align-items:center; flex-wrap:wrap; margin-top:.6rem; }
.hb-hero__cta{ display:inline-flex; align-items:center; gap:8px; background:var(--hb-accent); color:#fff!important;
  font-weight:600; font-size:1rem; padding:13px 28px; border-radius:10px;
  box-shadow:0 8px 18px -10px rgba(15,76,92,.7); transition:background .15s, transform .12s, box-shadow .12s; }
.hb-hero__cta:hover{ background:var(--hb-accent2); transform:translateY(-1px);
  box-shadow:0 12px 22px -10px rgba(15,76,92,.6); text-decoration:none!important; }
.hb-hero__link{ font-weight:600; color:var(--hb-accent)!important; border-bottom:1.5px solid transparent;
  padding-bottom:1px; transition:border-color .15s; }
.hb-hero__link:hover{ border-bottom-color:currentColor; text-decoration:none!important; }

/* ---- Bölüm + Kart ızgarası ---- */
.hb-section{ max-width:1080px; margin:2.4rem auto 0; padding-inline:1rem; }
.hb-section__title{ font-family:var(--serif); font-weight:600; font-size:1.7rem; color:var(--hb-ink);
  text-align:center; margin:0 0 1.2rem; }
.hb-grid{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:18px; margin:0; }
.hb-kart__ozet{ color:var(--hb-text); font-size:.96rem; margin:.5rem 0 .7rem; }
.hb-kart__chips{ margin-top:.4rem; }

/* ---- Footer ---- */
.hb-footer{ margin-top:3rem; border-top:1px solid var(--hb-line); background:var(--hb-soft); }
.hb-footer__in{ max-width:860px; margin-inline:auto; padding:2rem 1.2rem 2.4rem; }
.hb-footer__brand{ font-family:var(--serif); font-weight:700; font-size:1.2rem; color:var(--hb-ink); margin:0 0 .3rem; }
.hb-footer__desc{ color:var(--hb-muted); font-size:.95rem; max-width:60ch; margin:0 0 1rem; }
.hb-footer__nav{ display:flex; flex-wrap:wrap; gap:18px; font-weight:500; font-size:.95rem; margin-bottom:1rem; }
.hb-footer__legal{ color:var(--hb-muted); font-size:.82rem; border-top:1px solid var(--hb-line); padding-top:1rem; margin:0; }

@media (max-width:640px){ body{ font-size:16px; } .entry-content,.wp-block-post-content{ padding-inline:6px; }
  .hb-grid{ grid-template-columns:1fr; } }
</style>
    <?php
}, 99);
