<?php
/**
 * Plugin Name: Haberler — Arşiv (filtrelenebilir)
 * Description: [haberler_arsiv] kısa kodu: yayınlanan dosyaları kaynak/sınıflandırma/tarih ile filtreler.
 */
if (!defined('ABSPATH')) exit;

function haberler_arsiv_renk() {
    return [
        'dogru'=>['Doğru','#1a7f37'],'kismen_dogru'=>['Kısmen doğru','#9a6700'],
        'yanlis'=>['Yanlış','#cf222e'],'dogrulanamaz'=>['Doğrulanamaz','#57606a'],
        'gorus'=>['Görüş','#8250df'],
    ];
}

add_shortcode('haberler_arsiv', function () {
    $f_sinif  = isset($_GET['f_sinif'])  ? sanitize_text_field(wp_unslash($_GET['f_sinif']))  : '';
    $f_kaynak = isset($_GET['f_kaynak']) ? sanitize_text_field(wp_unslash($_GET['f_kaynak'])) : '';
    $f_tarih  = isset($_GET['f_tarih'])  ? sanitize_text_field(wp_unslash($_GET['f_tarih']))  : '';
    $renk = haberler_arsiv_renk();

    $q = new WP_Query([
        'post_type' => 'post', 'post_status' => 'publish', 'posts_per_page' => 100,
        'orderby' => 'date', 'order' => 'DESC',
        'meta_query' => [['key' => 'haberler_ozet', 'compare' => 'EXISTS']],
    ]);

    // Kaynak dropdown'u için tüm kaynak adlarını topla
    $kaynaklar = [];
    foreach ($q->posts as $p) {
        $k = json_decode((string) get_post_meta($p->ID, 'haberler_kaynaklar', true), true);
        if (is_array($k)) foreach ($k as $r) if (!empty($r['kaynak_adi'])) $kaynaklar[$r['kaynak_adi']] = 1;
    }
    ksort($kaynaklar);

    // ---- Filtre formu ----
    $h = '<form method="get" class="haberler-filtre" style="display:flex;gap:10px;flex-wrap:wrap;align-items:end;margin:1rem 0;padding:12px;background:#f6f8fa;border-radius:8px">';
    // Sınıflandırma
    $h .= '<label style="font-size:.85rem">Sınıflandırma<br><select name="f_sinif" style="padding:6px">';
    $h .= '<option value="">— hepsi —</option>';
    foreach ($renk as $val => $r) {
        $h .= '<option value="' . esc_attr($val) . '" ' . selected($f_sinif, $val, false) . '>' . esc_html($r[0]) . '</option>';
    }
    $h .= '</select></label>';
    // Kaynak
    $h .= '<label style="font-size:.85rem">Kaynak<br><select name="f_kaynak" style="padding:6px">';
    $h .= '<option value="">— hepsi —</option>';
    foreach (array_keys($kaynaklar) as $kn) {
        $h .= '<option value="' . esc_attr($kn) . '" ' . selected($f_kaynak, $kn, false) . '>' . esc_html($kn) . '</option>';
    }
    $h .= '</select></label>';
    // Tarih (yıl-ay)
    $h .= '<label style="font-size:.85rem">Tarih (YYYY-AA)<br><input type="text" name="f_tarih" value="' . esc_attr($f_tarih) . '" placeholder="2026-06" style="padding:6px"></label>';
    $h .= '<button type="submit" style="padding:7px 16px;background:#1f2937;color:#fff;border:0;border-radius:6px;cursor:pointer">Filtrele</button>';
    if ($f_sinif || $f_kaynak || $f_tarih) $h .= '<a href="' . esc_url(get_permalink()) . '" style="font-size:.85rem;align-self:center">temizle</a>';
    $h .= '</form>';

    // ---- Liste ----
    $kart = '';
    $sayi = 0;
    foreach ($q->posts as $p) {
        $idd = json_decode((string) get_post_meta($p->ID, 'haberler_iddialar', true), true) ?: [];
        $kay = json_decode((string) get_post_meta($p->ID, 'haberler_kaynaklar', true), true) ?: [];
        $siniflar = array_column($idd, 'siniflandirma');
        $knames   = array_column($kay, 'kaynak_adi');

        if ($f_sinif  && !in_array($f_sinif, $siniflar, true)) continue;
        if ($f_kaynak && !in_array($f_kaynak, $knames, true)) continue;
        if ($f_tarih  && strpos(get_the_date('Y-m', $p), $f_tarih) !== 0) continue;
        $sayi++;

        $chips = '';
        $say = [];
        foreach ($siniflar as $s) $say[$s] = ($say[$s] ?? 0) + 1;
        foreach ($say as $s => $n) {
            [$et, $rk] = $renk[$s] ?? ['Doğrulanamaz', '#57606a'];
            $chips .= '<span style="display:inline-block;background:' . esc_attr($rk) . ';color:#fff;font-size:.7rem;font-weight:700;padding:1px 7px;border-radius:4px;margin:2px 4px 0 0">' . esc_html($n . ' ' . $et) . '</span>';
        }
        $kart .= '<article style="border:1px solid #e5e7eb;border-radius:8px;padding:14px;margin:12px 0">';
        $kart .= '<a href="' . esc_url(get_permalink($p)) . '" style="font-size:1.1rem;font-weight:700;text-decoration:none">' . esc_html(get_the_title($p)) . '</a>';
        $kart .= '<div style="font-size:.8rem;color:#666;margin:4px 0">' . esc_html(get_the_date('d.m.Y', $p));
        if ($knames) $kart .= ' · ' . esc_html(implode(', ', array_unique($knames)));
        $kart .= '</div><div>' . $chips . '</div></article>';
    }
    wp_reset_postdata();

    $bilgi = '<p style="font-size:.85rem;color:#666">' . esc_html($sayi) . ' dosya listeleniyor.</p>';
    return $h . $bilgi . ($kart ?: '<p>Filtreye uyan dosya bulunamadı.</p>');
});
