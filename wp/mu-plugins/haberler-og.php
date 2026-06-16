<?php
/**
 * Plugin Name: Haberler — Sosyal Paylaşım Kartı (OG image)
 * Description: Her dosya için Open Graph + Twitter Card meta etiketleri ve dinamik 1200×630 PNG kart
 *              (başlık + tespit edilen sorun/karar + marka). Paylaşımlarda zengin önizleme.
 */
if (!defined('ABSPATH')) exit;

define('HABERLER_OG_FONT', ABSPATH . 'wp-content/themes/twentytwentythree/assets/fonts/inter/Inter-VariableFont_slnt,wght.ttf');

/* ---- <head> OG + Twitter meta (tekil dosya) ---- */
add_action('wp_head', function () {
    if (!is_singular('post')) return;
    $id = get_the_ID();
    $ozet = get_post_meta($id, 'haberler_ozet', true);
    if (!$ozet && !get_post_meta($id, 'haberler_iddialar', true)) return; // dosya değilse dokunma
    $title = get_the_title($id);
    $desc  = $ozet ? mb_substr(wp_strip_all_tags($ozet), 0, 180) : '';
    $img   = esc_url(add_query_arg('haberler_og', $id, home_url('/')));
    echo "\n";
    echo '<meta property="og:type" content="article">' . "\n";
    echo '<meta property="og:title" content="' . esc_attr($title) . '">' . "\n";
    echo '<meta property="og:description" content="' . esc_attr($desc) . '">' . "\n";
    echo '<meta property="og:image" content="' . $img . '">' . "\n";
    echo '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">' . "\n";
    echo '<meta name="twitter:card" content="summary_large_image">' . "\n";
    echo '<meta name="twitter:title" content="' . esc_attr($title) . '">' . "\n";
    echo '<meta name="twitter:description" content="' . esc_attr($desc) . '">' . "\n";
    echo '<meta name="twitter:image" content="' . $img . '">' . "\n";
}, 6);

/* ---- PNG kart üretici: /?haberler_og=ID ---- */
add_action('init', function () {
    if (!isset($_GET['haberler_og'])) return;
    $id = (int) $_GET['haberler_og'];
    if (!$id || get_post_type($id) !== 'post' || !function_exists('imagettftext')) { status_header(404); exit; }

    $title = get_the_title($id);
    $sorun = json_decode((string) get_post_meta($id, 'haberler_haber_sorunu', true), true) ?: [];
    $idd   = json_decode((string) get_post_meta($id, 'haberler_iddialar', true), true) ?: [];
    $F = HABERLER_OG_FONT;

    $W = 1200; $H = 630; $im = imagecreatetruecolor($W, $H);
    $bg = imagecolorallocate($im, 255, 255, 255);
    $ink = imagecolorallocate($im, 17, 24, 28);
    $muted = imagecolorallocate($im, 90, 100, 110);
    $accent = imagecolorallocate($im, 15, 76, 92);
    $red = imagecolorallocate($im, 194, 65, 12);
    imagefilledrectangle($im, 0, 0, $W, $H, $bg);
    imagefilledrectangle($im, 0, 0, $W, 14, $accent);
    imagefilledrectangle($im, 0, $H - 6, $W, $H, $accent);

    imagettftext($im, 19, 0, 70, 92, $accent, $F, 'BAĞIMSIZ MEDYA İZLEME — DOĞRULUK DENETİMİ');

    // Başlık (satır kaydır, en çok 4 satır)
    $size = 44; $maxw = $W - 140; $y = 180;
    $words = preg_split('/\s+/u', $title); $line = ''; $lines = [];
    foreach ($words as $w) {
        $try = ($line === '') ? $w : $line . ' ' . $w;
        $bb = imagettfbbox($size, 0, $F, $try);
        if (($bb[2] - $bb[0]) > $maxw && $line !== '') { $lines[] = $line; $line = $w; }
        else { $line = $try; }
    }
    if ($line !== '') $lines[] = $line;
    foreach (array_slice($lines, 0, 4) as $ln) { imagettftext($im, $size, 0, 70, $y, $ink, $F, $ln); $y += 62; }

    // Tespit edilen sorun / değerlendirme
    $map = ['yalan_haber' => 'YALAN HABER', 'iftira' => 'İFTİRA', 'toptan_suclama' => 'TOPTAN SUÇLAMA', 'carpitma' => 'ÇARPITMA'];
    $etk = [];
    foreach ($sorun as $s) { if (isset($map[$s])) $etk[] = $map[$s]; }
    if ($etk) {
        imagettftext($im, 28, 0, 70, $H - 95, $red, $F, 'TESPİT: ' . implode('  ·  ', $etk));
    } else {
        imagettftext($im, 24, 0, 70, $H - 95, $muted, $F, count($idd) . ' iddia kanıta karşı değerlendirildi');
    }
    imagettftext($im, 17, 0, 70, $H - 45, $muted, $F, 'Taslak — kaynağa atıflıdır, hukuki görüş değildir.');

    header('Content-Type: image/png');
    header('Cache-Control: public, max-age=3600');
    imagepng($im); imagedestroy($im); exit;
}, 1);
