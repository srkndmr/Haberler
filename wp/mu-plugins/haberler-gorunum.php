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

/** İnce çizgi (line) SVG ikon — currentColor ile çizilir, harici istek yok. */
function haberler_ic($ad) {
    $p = [
        'doc'   => '<path d="M14 3v5h5"/><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="14" y2="17"/>',
        'scale' => '<path d="M12 3v18"/><path d="M8 21h8"/><path d="M3 7h18"/><path d="M7 7l-3 6a3 3 0 0 0 6 0z"/><path d="M17 7l-3 6a3 3 0 0 0 6 0z"/>',
        'check' => '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M8 11l2.5 2.5L16 8"/>',
        'link'  => '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    ];
    if (!isset($p[$ad])) return '';
    return '<svg class="hb-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
         . 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' . $p[$ad] . '</svg>';
}

/** Sınıflandırmaya özgü küçük rozet ikonu. */
function haberler_chip_ic($s) {
    $p = [
        'dogru'        => '<path d="M5 13l4 4L19 7"/>',
        'kismen_dogru' => '<circle cx="12" cy="12" r="9"/><path d="M8 12h8"/>',
        'yanlis'       => '<path d="M6 6l12 12M18 6 6 18"/>',
        'dogrulanamaz' => '<circle cx="12" cy="12" r="9"/><path d="M9.6 9a2.4 2.4 0 1 1 3.3 2.3c-.7.4-.9.8-.9 1.6"/><path d="M12 16.5v.01"/>',
        'mesnetsiz'    => '<path d="M12 3 2 20h20z"/><path d="M12 10v4"/><path d="M12 17v.01"/>',
        'gorus'        => '<path d="M21 11.5a8.4 8.4 0 0 1-8.5 8.5 8.5 8.5 0 0 1-3.8-.9L3 21l1.9-5.7A8.4 8.4 0 0 1 4 11.5 8.5 8.5 0 0 1 12.5 3 8.4 8.4 0 0 1 21 11.5z"/>',
    ];
    if (!isset($p[$s])) return '';
    return '<svg class="hb-chip-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
         . 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' . $p[$s] . '</svg>';
}

/** Tam rozet (ikon + etiket). $text verilmezse etiketi kullanır (ör. sayı için "2 Görüş"). */
function haberler_chip($s, $text = null) {
    $t = $text ?? haberler_etiket($s);
    return '<span class="hb-chip hb-chip--' . esc_attr($s) . '">' . haberler_chip_ic($s) . esc_html($t) . '</span>';
}

function haberler_dosya_render($content) {
    if (!in_the_loop() || !is_main_query()) return $content;
    $id = get_the_ID();
    if (get_post_type($id) !== 'post') return $content;

    $ozet = get_post_meta($id, 'haberler_ozet', true);
    $kay  = json_decode((string) get_post_meta($id, 'haberler_kaynaklar', true), true);
    $idd  = json_decode((string) get_post_meta($id, 'haberler_iddialar', true), true);
    $gd   = get_post_meta($id, 'haberler_genel_degerlendirme', true);
    $sorun = json_decode((string) get_post_meta($id, 'haberler_haber_sorunu', true), true);
    $ozet_en = get_post_meta($id, 'haberler_ozet_en', true);
    $gd_en = get_post_meta($id, 'haberler_genel_degerlendirme_en', true);
    $baslik_en = get_post_meta($id, 'haberler_baslik_en', true);
    if (!$ozet && !$kay && !$idd) return $content;

    // ---- Listeleme (akış/arşiv) ----
    if (!is_singular('post')) {
        $chips = '';
        if (is_array($idd)) {
            $say = [];
            foreach ($idd as $x) { $s = $x['siniflandirma'] ?? 'dogrulanamaz'; $say[$s] = ($say[$s] ?? 0) + 1; }
            foreach ($say as $s => $n) {
                $chips .= haberler_chip($s, $n . ' ' . haberler_etiket($s));
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

    // Tespit edilen haber sorunu (varsa) — en üstte belirgin banner
    if (is_array($sorun)) {
        $etiketler = [];
        foreach ($sorun as $s) {
            if ($s && $s !== 'sorun_yok' && isset(HABERLER_SORUN_ETIKET[$s])) $etiketler[] = HABERLER_SORUN_ETIKET[$s];
        }
        if ($etiketler) {
            $h .= '<div class="hb-sorun"><span class="hb-sorun__ic">⚠</span> Bu haberde tespit edilen sorun: '
                . '<strong>' . esc_html(implode(' · ', $etiketler)) . '</strong></div>';
        }
    }

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
            $vchips .= haberler_chip($s, $n . ' ' . haberler_etiket($s));
        }
        $ks = is_array($kay) ? count($kay) : 0;
        $h .= '<div class="hb-verdict"><div class="hb-verdict__kicker">' . haberler_ic('scale') . 'DOSYA DEĞERLENDİRMESİ</div>'
            . '<div class="hb-verdict__chips">' . $vchips . '</div>'
            . '<div class="hb-verdict__note">' . esc_html(count($idd)) . ' iddia incelendi'
            . ($ks ? ' · ' . esc_html($ks) . ' kaynak' : '') . '</div></div>';
    }

    if ($ozet) $h .= '<h2>' . haberler_ic('doc') . 'Özet</h2><p>' . nl2br(esc_html($ozet)) . '</p>';
    if ($gd)   $h .= '<h2>' . haberler_ic('scale') . 'Genel Değerlendirme</h2><div class="hb-gd">' . nl2br(esc_html($gd)) . '</div>';

    if (is_array($idd) && $idd) {
        $h .= '<h2>' . haberler_ic('check') . 'İddialar ve Değerlendirme</h2>';
        $kullanilan = array_unique(array_map(function ($x) { return $x['siniflandirma'] ?? 'dogrulanamaz'; }, $idd));
        $h .= '<div class="hb-legend">';
        foreach ($kullanilan as $s) {
            $h .= '<div class="hb-legend-row">' . haberler_chip($s) . ' ' . esc_html(HABERLER_SINIF_ACIKLAMA[$s] ?? '') . '</div>';
        }
        $h .= '</div>';

        foreach ($idd as $x) {
            $s = $x['siniflandirma'] ?? 'dogrulanamaz';
            $h .= '<div class="hb-iddia hb-iddia--' . esc_attr($s) . '">';
            $h .= haberler_chip($s);
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
        $h .= '<h2>' . haberler_ic('link') . 'Kaynaklar' . (count($kay) > 1 ? ' (' . count($kay) . ' mecra)' : '') . '</h2>';
        if (count($kay) > 2) {
            $h .= '<p class="hb-coklu-kaynak">Bu içerik <strong>' . count($kay) . ' ayrı mecrada</strong> yer aldı.</p>';
        }
        $h .= '<ul class="hb-kaynaklar">';
        foreach ($kay as $k) {
            $url = $k['orijinal_url'] ?? ''; $ad = $k['kaynak_adi'] ?? $url;
            $tar = !empty($k['yayin_tarihi']) ? ' — ' . esc_html($k['yayin_tarihi']) : '';
            $h  .= '<li><strong>' . esc_html($ad) . '</strong>' . $tar;
            if ($url) $h .= ' · <a href="' . esc_url($url) . '" target="_blank" rel="noopener">' . haberler_ic('link') . 'orijinal</a>';
            if (!empty($k['arsiv_url'])) $h .= ' · <a href="' . esc_url($k['arsiv_url']) . '" target="_blank" rel="noopener">arşiv</a>';
            $h .= '</li>';
        }
        $h .= '</ul>';
    }

    if ($ozet_en || $gd_en) {
        $h .= '<details class="hb-en"><summary>🌐 In English</summary>';
        if ($baslik_en) $h .= '<h3>' . esc_html($baslik_en) . '</h3>';
        if ($ozet_en) $h .= '<p>' . nl2br(esc_html($ozet_en)) . '</p>';
        if ($gd_en)   $h .= '<p>' . nl2br(esc_html($gd_en)) . '</p>';
        $h .= '<p class="hb-en__note">Automated fact-check draft, reviewed by a human editor. '
            . 'Claims are attributed to their sources; this is not a final legal determination.</p>';
        $h .= '</details>';
    }

    $h .= '<p class="hb-disclaimer hb-disclaimer--bottom">Bu çalışma bağımsız bir medya izleme ve '
        . 'doğruluk denetimi faaliyetidir; bir editör incelemesinden geçmiştir ve hukuki görüş niteliği '
        . 'taşımaz. Bir hata olduğunu düşünüyorsanız İletişim / Düzeltme Talebi sayfasından bildirebilirsiniz; '
        . 'her başvuru insan eliyle değerlendirilir.</p>';
    $h .= '</div>';
    return $content . $h;
}
add_filter('the_content', 'haberler_dosya_render', 20);
