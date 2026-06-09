<?php
/**
 * Plugin Name: Haberler — Tema / Özel CSS
 * Description: Ön yüz için tasarım katmanı (tipografi, okuma kolonu, fact-check kartları,
 *              sınıflandırma rozetleri, arşiv). Tema bağımsız çalışır.
 */
if (!defined('ABSPATH')) exit;

add_action('wp_head', function () {
    ?>
<style id="haberler-tema">
:root{
  --hb-ink:#15202b; --hb-text:#2b2f36; --hb-muted:#5b6570; --hb-line:#e6e8eb;
  --hb-bg:#ffffff; --hb-soft:#f7f8fa; --hb-accent:#15457a;
  --c-dogru:#1a7f37; --c-kismen:#9a6700; --c-yanlis:#cf222e; --c-dogrulanamaz:#57606a; --c-gorus:#7c3aed;
}
body{ color:var(--hb-text); background:var(--hb-bg);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  line-height:1.65; -webkit-font-smoothing:antialiased; }
a{ color:var(--hb-accent); text-decoration:none; } a:hover{ text-decoration:underline; }

/* Okuma kolonu + başlıklar */
.hb-wrap, .entry-content, .wp-block-post-content, main .wp-block-group{ }
.entry-content, .wp-block-post-content{ max-width:760px; margin-inline:auto; font-size:1.06rem; }
.entry-title, .wp-block-post-title{ font-weight:800; letter-spacing:-.02em; line-height:1.2;
  color:var(--hb-ink); max-width:860px; margin-inline:auto; }
h2{ color:var(--hb-ink); font-weight:750; letter-spacing:-.01em; margin-top:1.8rem; }

/* ---- Dosya (tekil) ---- */
.hb-dosya{ margin-top:2rem; border-top:1px solid var(--hb-line); padding-top:1.5rem; }
.hb-disclaimer{ font-size:.92rem; border-radius:10px; padding:12px 16px; margin:10px 0 18px; }
.hb-disclaimer--top{ background:#fff8e6; border:1px solid #f3d27a; color:#6b5200; }
.hb-disclaimer--bottom{ background:var(--hb-soft); border:1px solid var(--hb-line); color:var(--hb-muted); font-size:.86rem; }
.hb-gd{ background:#eef3f8; border-left:4px solid var(--hb-accent); border-radius:0 10px 10px 0;
  padding:14px 18px; line-height:1.7; }

/* Lejant */
.hb-legend{ font-size:.85rem; background:var(--hb-soft); border:1px solid var(--hb-line);
  border-radius:10px; padding:10px 14px; margin:10px 0 16px; }
.hb-legend-row{ margin:4px 0; color:var(--hb-muted); }

/* İddia kartları */
.hb-iddia{ border:1px solid var(--hb-line); border-left-width:5px; border-radius:10px;
  padding:14px 16px; margin:14px 0; background:#fff; box-shadow:0 1px 2px rgba(16,24,40,.04); }
.hb-iddia__metin{ font-weight:650; color:var(--hb-ink); margin:.55rem 0 .35rem; font-size:1.05rem; }
.hb-iddia__satir{ margin:.35rem 0; color:var(--hb-text); }
.hb-iddia__satir b{ color:var(--hb-muted); font-weight:600; }
.hb-iddia__dayanak{ font-size:.86rem; }

/* Sınıflandırma renkleri (kart kenarı + rozet) */
.hb-iddia--dogru{ border-left-color:var(--c-dogru); }
.hb-iddia--kismen_dogru{ border-left-color:var(--c-kismen); }
.hb-iddia--yanlis{ border-left-color:var(--c-yanlis); }
.hb-iddia--dogrulanamaz{ border-left-color:var(--c-dogrulanamaz); }
.hb-iddia--gorus{ border-left-color:var(--c-gorus); }

.hb-chip{ display:inline-block; color:#fff; font-size:.72rem; font-weight:700;
  text-transform:uppercase; letter-spacing:.02em; padding:3px 9px; border-radius:999px; margin:0 4px 2px 0; }
.hb-chip--dogru{ background:var(--c-dogru); } .hb-chip--kismen_dogru{ background:var(--c-kismen); }
.hb-chip--yanlis{ background:var(--c-yanlis); } .hb-chip--dogrulanamaz{ background:var(--c-dogrulanamaz); }
.hb-chip--gorus{ background:var(--c-gorus); }

/* Kaynaklar */
.hb-kaynaklar{ list-style:none; padding:0; margin:.5rem 0; }
.hb-kaynaklar li{ padding:8px 0; border-bottom:1px dashed var(--hb-line); }
.hb-kaynaklar li:last-child{ border-bottom:0; }

/* ---- Listeleme / akış kartı ---- */
.hb-ozet-kart{ margin:.4rem 0 .2rem; }
.hb-ozet-kart .hb-kaynak-sayi{ font-size:.82rem; color:var(--hb-muted); }

/* ---- Arşiv ---- */
.hb-filtre{ display:flex; gap:12px; flex-wrap:wrap; align-items:end; margin:1rem 0;
  padding:14px 16px; background:var(--hb-soft); border:1px solid var(--hb-line); border-radius:12px; }
.hb-filtre label{ font-size:.85rem; color:var(--hb-muted); }
.hb-filtre select, .hb-filtre input{ padding:7px 9px; border:1px solid #cdd2d8; border-radius:8px; background:#fff; }
.hb-btn{ padding:8px 18px; background:var(--hb-ink); color:#fff; border:0; border-radius:8px; cursor:pointer; font-weight:600; }
.hb-btn:hover{ background:#0c1620; }
.hb-kart{ border:1px solid var(--hb-line); border-radius:12px; padding:16px 18px; margin:14px 0;
  background:#fff; box-shadow:0 1px 2px rgba(16,24,40,.04); transition:box-shadow .15s; }
.hb-kart:hover{ box-shadow:0 4px 14px rgba(16,24,40,.08); }
.hb-kart__baslik{ font-size:1.12rem; font-weight:750; color:var(--hb-ink); }
.hb-kart__meta{ font-size:.82rem; color:var(--hb-muted); margin:5px 0 8px; }

@media (max-width:640px){ .entry-content,.wp-block-post-content{ font-size:1rem; padding-inline:4px; } }
</style>
    <?php
}, 99);
