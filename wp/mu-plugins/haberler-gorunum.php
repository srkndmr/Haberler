<?php
/**
 * Plugin Name: Haberler — Dosya Görünümü (ön yüz)
 * Description: Dosya meta'sını tasarlanmış kart/panel olarak render eder (stil: haberler-tema.php).
 */
if (!defined('ABSPATH')) exit;

const HABERLER_SINIF_RENK = [
    'dogru'        => ['Doğru', '#1a7f37'],
    'kismen_dogru' => ['Kısmen Doğru', '#9a6700'],
    'yanlis'       => ['Yanlış', '#cf222e'],
    'dogrulanamaz' => ['Doğrulanamadı', '#57606a'],
    'mesnetsiz'    => ['Mesnetsiz', '#c2410c'],
    'gorus'        => ['Görüş', '#7c3aed'],
];
const HABERLER_SINIF_ACIKLAMA = [
    'dogru'        => 'Güvenilir kanıtla doğrulandı.',
    'kismen_dogru' => 'Bir kısmı doğru; bir kısmı eksik, yanlış veya bağlamından kopuk.',
    'yanlis'       => 'Güvenilir kanıtla çürütüldü.',
    'dogrulanamaz' => 'İddia ne doğrulanabildi ne çürütüldü — bağımsız kanıt sunulmadığı için açık bırakıldı (suçlama anlamına gelmez).',
    'mesnetsiz'    => 'Kaynak, iddiayı somut bir delil/dayanak göstermeden ileri sürmüş — doğru ya da yanlış olduğu ayrıca değerlendirilir.',
    'gorus'        => 'Olgu değil; yorum, değerlendirme veya değer yargısı.',
];

function haberler_etiket($s) { return HABERLER_SINIF_RENK[$s][0] ?? 'Doğrulanamadı'; }

function haberler_dosya_render($content) {
    if (!in_the_loop() || !is_main_query()) return $content;
    $id = get_the_ID();
    if (get_post_type($id) !== 'post') return $content;

    $ozet = get_post_meta($id, 'haberler_ozet', true);
    $kay  = json_decode((string) get_post_meta($id, 'haberler_kaynaklar', true), true);
    $idd  = json_decode((string) get_post_meta($id, 'haberler_iddialar', true), true);
    $gd   = get_post_meta($id, 'haberler_genel_degerlendirme', true);
    if (!$ozet && !$kay && !$idd) return $content;

    // ---- Listeleme (akış/arşiv) ----
    if (!is_singular('post')) {
        $chips = '';
        if (is_array($idd)) {
            $say = [];
            foreach ($idd as $x) { $s = $x['siniflandirma'] ?? 'dogrulanamaz'; $say[$s] = ($say[$s] ?? 0) + 1; }
            foreach ($say as $s => $n) {
                $chips .= '<span class="hb-chip hb-chip--' . esc_attr($s) . '">' . esc_html($n . ' ' . haberler_etiket($s)) . '</span>';
            }
        }
        $ksay  = is_array($kay) ? count($kay) : 0;
        $ozetk = $ozet ? mb_substr($ozet, 0, 220) . (mb_strlen($ozet) > 220 ? '…' : '') : '';
        $o = '<div class="hb-ozet-kart">';
        if ($ozetk) $o .= '<p>' . esc_html($ozetk) . '</p>';
        if ($chips) $o .= '<p>' . $chips . '</p>';
        if ($ksay)  $o .= '<p class="hb-kaynak-sayi">' . esc_html($ksay) . ' kaynak</p>';
        $o .= '</div>';
        return $o;
    }

    // ---- Tekil dosya ----
    $h  = '<div class="hb-dosya">';
    $h .= '<p class="hb-disclaimer hb-disclaimer--top"><strong>Not:</strong> Bu dosya, kamuya açık '
        . 'haberlerde öne sürülen iddiaların bağımsız bir değerlendirmesidir. Aktarılan iddialar ilgili '
        . 'kaynaklara aittir; bir kişinin suçlu olup olmadığına ilişkin nihai takdir yalnızca yargı '
        . 'mercilerine aittir. Değerlendirmelerimiz kesin hüküm niteliği taşımaz.</p>';

    // Değerlendirme kutusu (görsel anchor)
    if (is_array($idd) && $idd) {
        $say = [];
        foreach ($idd as $x) { $s = $x['siniflandirma'] ?? 'dogrulanamaz'; $say[$s] = ($say[$s] ?? 0) + 1; }
        $vchips = '';
        foreach ($say as $s => $n) {
            $vchips .= '<span class="hb-chip hb-chip--' . esc_attr($s) . '">' . esc_html($n . ' ' . haberler_etiket($s)) . '</span>';
        }
        $ks = is_array($kay) ? count($kay) : 0;
        $h .= '<div class="hb-verdict"><div class="hb-verdict__kicker">Dosya Değerlendirmesi</div>'
            . '<div class="hb-verdict__chips">' . $vchips . '</div>'
            . '<div class="hb-verdict__note">' . esc_html(count($idd)) . ' iddia incelendi'
            . ($ks ? ' · ' . esc_html($ks) . ' kaynak' : '') . '</div></div>';
    }

    if ($ozet) $h .= '<h2>Özet</h2><p>' . nl2br(esc_html($ozet)) . '</p>';
    if ($gd)   $h .= '<h2>Genel Değerlendirme</h2><div class="hb-gd">' . nl2br(esc_html($gd)) . '</div>';

    if (is_array($idd) && $idd) {
        $h .= '<h2>İddialar ve Değerlendirme</h2>';
        $kullanilan = array_unique(array_map(function ($x) { return $x['siniflandirma'] ?? 'dogrulanamaz'; }, $idd));
        $h .= '<div class="hb-legend">';
        foreach ($kullanilan as $s) {
            $h .= '<div class="hb-legend-row"><span class="hb-chip hb-chip--' . esc_attr($s) . '">'
                . esc_html(haberler_etiket($s)) . '</span> ' . esc_html(HABERLER_SINIF_ACIKLAMA[$s] ?? '') . '</div>';
        }
        $h .= '</div>';

        foreach ($idd as $x) {
            $s = $x['siniflandirma'] ?? 'dogrulanamaz';
            $h .= '<div class="hb-iddia hb-iddia--' . esc_attr($s) . '">';
            $h .= '<span class="hb-chip hb-chip--' . esc_attr($s) . '">' . esc_html(haberler_etiket($s)) . '</span>';
            $h .= '<p class="hb-iddia__metin">' . esc_html($x['iddia_metni'] ?? '') . '</p>';
            if (!empty($x['gerekce']))
                $h .= '<p class="hb-iddia__satir"><b>Gerekçe:</b> ' . esc_html($x['gerekce']) . '</p>';
            if (!empty($x['dayanak_kaynak_url']))
                $h .= '<p class="hb-iddia__satir hb-iddia__dayanak"><b>Dayanak:</b> <a href="'
                    . esc_url($x['dayanak_kaynak_url']) . '" target="_blank" rel="noopener">'
                    . esc_html($x['dayanak_kaynak_url']) . '</a></p>';
            $h .= '</div>';
        }
    }

    if (is_array($kay) && $kay) {
        $h .= '<h2>Kaynaklar</h2><ul class="hb-kaynaklar">';
        foreach ($kay as $k) {
            $url = $k['orijinal_url'] ?? ''; $ad = $k['kaynak_adi'] ?? $url;
            $tar = !empty($k['yayin_tarihi']) ? ' — ' . esc_html($k['yayin_tarihi']) : '';
            $h  .= '<li><strong>' . esc_html($ad) . '</strong>' . $tar;
            if ($url) $h .= ' · <a href="' . esc_url($url) . '" target="_blank" rel="noopener">orijinal</a>';
            if (!empty($k['arsiv_url'])) $h .= ' · <a href="' . esc_url($k['arsiv_url']) . '" target="_blank" rel="noopener">arşiv</a>';
            $h .= '</li>';
        }
        $h .= '</ul>';
    }

    $h .= '<p class="hb-disclaimer hb-disclaimer--bottom">Bu çalışma bağımsız bir medya izleme ve '
        . 'doğruluk denetimi faaliyetidir; bir editör incelemesinden geçmiştir ve hukuki görüş niteliği '
        . 'taşımaz. Bir hata olduğunu düşünüyorsanız İletişim / Düzeltme Talebi sayfasından bildirebilirsiniz; '
        . 'her başvuru insan eliyle değerlendirilir.</p>';
    $h .= '</div>';
    return $content . $h;
}
add_filter('the_content', 'haberler_dosya_render', 20);
