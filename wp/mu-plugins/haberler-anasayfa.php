<?php
/**
 * Plugin Name: Haberler — Ana Sayfa & Footer
 * Description: [haberler_son_dosyalar] kısa kodu (kart ızgarası) + site geneli footer.
 */
if (!defined('ABSPATH')) exit;

add_shortcode('haberler_son_dosyalar', function ($atts) {
    $a = shortcode_atts(['limit' => 9, 'baslik' => ''], $atts);
    $q = new WP_Query([
        'post_type' => 'post', 'post_status' => 'publish', 'posts_per_page' => (int) $a['limit'],
        'meta_query' => [['key' => 'haberler_ozet', 'compare' => 'EXISTS']],
    ]);
    $bas = $a['baslik'] ? '<h2 class="hb-section__title">' . esc_html($a['baslik']) . '</h2>' : '';
    if (!$q->have_posts()) { wp_reset_postdata(); return '<section class="hb-section">' . $bas . '<p>Henüz yayımlanmış dosya yok.</p></section>'; }

    $etk = function ($s) { return function_exists('haberler_etiket') ? haberler_etiket($s) : $s; };
    $out = '<section class="hb-section">' . $bas . '<div class="hb-grid">';
    foreach ($q->posts as $p) {
        $idd  = json_decode((string) get_post_meta($p->ID, 'haberler_iddialar', true), true) ?: [];
        $kay  = json_decode((string) get_post_meta($p->ID, 'haberler_kaynaklar', true), true) ?: [];
        $ozet = get_post_meta($p->ID, 'haberler_ozet', true);
        $say = [];
        foreach ($idd as $x) { $s = $x['siniflandirma'] ?? 'dogrulanamaz'; $say[$s] = ($say[$s] ?? 0) + 1; }
        $chips = '';
        foreach ($say as $s => $n) {
            $chips .= '<span class="hb-chip hb-chip--' . esc_attr($s) . '">' . esc_html($n . ' ' . $etk($s)) . '</span>';
        }
        $kn = array_values(array_unique(array_filter(array_column($kay, 'kaynak_adi'))));
        $out .= '<article class="hb-kart">';
        $out .= '<a class="hb-kart__baslik" href="' . esc_url(get_permalink($p)) . '">' . esc_html(get_the_title($p)) . '</a>';
        $out .= '<div class="hb-kart__meta">' . esc_html(get_the_date('d.m.Y', $p)) . ($kn ? ' · ' . esc_html(implode(', ', $kn)) : '') . '</div>';
        if ($ozet) $out .= '<p class="hb-kart__ozet">' . esc_html(mb_substr($ozet, 0, 150) . (mb_strlen($ozet) > 150 ? '…' : '')) . '</p>';
        $out .= '<div class="hb-kart__chips">' . $chips . '</div></article>';
    }
    $out .= '</div></section>';
    wp_reset_postdata();
    return $out;
});

// Site geneli footer (ön yüz)
add_action('wp_footer', function () {
    if (is_admin()) return;
    echo '<footer class="hb-footer"><div class="hb-footer__in">';
    echo '<p class="hb-footer__brand">Bağımsız Medya İzleme</p>';
    echo '<p class="hb-footer__desc">Bağımsız doğruluk denetimi ve medya izleme girişimi. Her dosya insan '
       . 'editör onayından geçer; iddialar kaynağına atfedilir ve kesin hüküm değildir.</p>';
    echo '<nav class="hb-footer__nav">'
       . '<a href="' . esc_url(home_url('/metodoloji/')) . '">Metodoloji</a>'
       . '<a href="' . esc_url(home_url('/kunye/')) . '">Künye</a>'
       . '<a href="' . esc_url(home_url('/arsiv/')) . '">Arşiv</a>'
       . '<a href="' . esc_url(home_url('/iletisim-duzeltme-talebi/')) . '">İletişim / Düzeltme Talebi</a>'
       . '</nav>';
    echo '<p class="hb-footer__legal">© ' . esc_html(date('Y')) . ' · Bu bir haber kaynağı veya hukuki danışmanlık hizmeti değildir.</p>';
    echo '</div></footer>';
});
