<?php
/**
 * Plugin Name: Haberler — Dosya Görünümü (ön yüz)
 * Description: Dosya meta'sını (özet, iddialar+sınıflandırma, kaynaklar, feragatname)
 *              yazı içeriğinin altında ön yüzde render eder.
 */
if (!defined('ABSPATH')) exit;

const HABERLER_SINIF_RENK = [
    'dogru'        => ['Doğru', '#1a7f37'],
    'kismen_dogru' => ['Kısmen doğru', '#9a6700'],
    'yanlis'       => ['Yanlış', '#cf222e'],
    'dogrulanamaz' => ['Doğrulanamaz', '#57606a'],
    'gorus'        => ['Görüş', '#8250df'],
];

function haberler_dosya_render($content) {
    if (!is_singular('post') || !in_the_loop() || !is_main_query()) return $content;

    $id    = get_the_ID();
    $ozet  = get_post_meta($id, 'haberler_ozet', true);
    $kay   = json_decode((string) get_post_meta($id, 'haberler_kaynaklar', true), true);
    $idd   = json_decode((string) get_post_meta($id, 'haberler_iddialar', true), true);
    $isim  = get_post_meta($id, 'haberler_isim_verilen_suclama', true);
    if (!$ozet && !$kay && !$idd) return $content; // dosya değil → dokunma

    $h  = '<div class="haberler-dosya" style="margin-top:2rem;border-top:2px solid #e5e7eb;padding-top:1.5rem">';

    // Üst feragatname
    $h .= '<p style="background:#fff8e1;border-left:4px solid #f59e0b;padding:10px 14px;font-size:.9rem;color:#5a4a00">'
        . '<strong>Not:</strong> Bu bir doğruluk denetimi dosyasıdır; iddialar kaynağına atfedilmiştir. '
        . 'Hukuki/cezai nitelemeler mahkemelerin işidir, kesin hüküm değildir.</p>';

    if ($ozet) {
        $h .= '<h2>Özet</h2><p>' . esc_html($ozet) . '</p>';
    }

    if (is_array($idd) && $idd) {
        $h .= '<h2>İddialar ve Değerlendirme</h2>';
        foreach ($idd as $x) {
            $s = $x['siniflandirma'] ?? 'dogrulanamaz';
            [$etiket, $renk] = HABERLER_SINIF_RENK[$s] ?? ['Doğrulanamaz', '#57606a'];
            $h .= '<div style="border-left:4px solid ' . esc_attr($renk) . ';padding:8px 14px;margin:12px 0;background:#f6f8fa">';
            $h .= '<span style="display:inline-block;background:' . esc_attr($renk) . ';color:#fff;font-size:.7rem;'
                . 'font-weight:700;text-transform:uppercase;padding:2px 8px;border-radius:4px">' . esc_html($etiket) . '</span>';
            $h .= '<p style="margin:8px 0 4px;font-weight:600">' . esc_html($x['iddia_metni'] ?? '') . '</p>';
            if (!empty($x['gerekce'])) $h .= '<p style="margin:4px 0;color:#444"><em>Gerekçe:</em> ' . esc_html($x['gerekce']) . '</p>';
            if (!empty($x['dayanak_kaynak_url'])) {
                $h .= '<p style="margin:4px 0;font-size:.85rem"><em>Dayanak:</em> <a href="' . esc_url($x['dayanak_kaynak_url'])
                    . '" target="_blank" rel="noopener">' . esc_html($x['dayanak_kaynak_url']) . '</a></p>';
            }
            $h .= '</div>';
        }
    }

    if (is_array($kay) && $kay) {
        $h .= '<h2>Kaynaklar</h2><ul>';
        foreach ($kay as $k) {
            $url = $k['orijinal_url'] ?? '';
            $ad  = $k['kaynak_adi'] ?? $url;
            $tar = !empty($k['yayin_tarihi']) ? ' — ' . esc_html($k['yayin_tarihi']) : '';
            $h  .= '<li><strong>' . esc_html($ad) . '</strong>' . $tar;
            if ($url) $h .= ' · <a href="' . esc_url($url) . '" target="_blank" rel="noopener">orijinal</a>';
            if (!empty($k['arsiv_url'])) $h .= ' · <a href="' . esc_url($k['arsiv_url']) . '" target="_blank" rel="noopener">arşiv</a>';
            $h .= '</li>';
        }
        $h .= '</ul>';
    }

    // Alt feragatname
    $h .= '<p style="margin-top:1.5rem;font-size:.85rem;color:#666;border-top:1px solid #eee;padding-top:10px">'
        . 'Bu içerik bağımsız bir medya izleme/doğruluk denetimi çalışmasıdır ve insan editör onayından geçmiştir. '
        . 'Düzeltme talepleri için İletişim sayfasını kullanın.</p>';

    $h .= '</div>';
    return $content . $h;
}
add_filter('the_content', 'haberler_dosya_render', 20);
