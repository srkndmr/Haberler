<?php
/**
 * Plugin Name: Haberler — Veri Alanları (ücretsiz)
 * Description: Dosya alanlarını post meta olarak kaydeder ve REST'e açar.
 *              ACF PRO (repeater) GEREKTİRMEZ. kaynaklar/iddialar JSON string tutulur.
 */
if (!defined('ABSPATH')) exit;

const HABERLER_META = [
    'haberler_ozet',
    'haberler_genel_degerlendirme',    // hukuki-gazetecilik dilinde genel değerlendirme
    'haberler_baslik_en',              // İngilizce başlık
    'haberler_ozet_en',                // İngilizce özet
    'haberler_genel_degerlendirme_en', // İngilizce genel değerlendirme
    'haberler_medya_kategori',         // tek anahtar: kara_propaganda|dezenformasyon|manipulatif|dogrulanmamis|kabul_edilebilir
    'haberler_kategori_gerekce',       // kategori için 1-2 cümle gerekçe
    'haberler_halk_tabiri',            // amiyane/halk ağzı ağır tabir — "en hafif tabirle ..."
    'haberler_araclastirma',           // 'FETÖ' yaftasının siyaseten araçsallaştırılması notu (boşsa gösterilmez)
    'haberler_haber_sorunu',           // JSON dizi: yalan_haber|iftira|toptan_suclama|carpitma|sorun_yok
    'haberler_ihlal_haklar',           // JSON dizi: ihlal edilen/risk altındaki temel haklar
    'haberler_kanun_maddeleri',        // JSON: [{kanun,madde,gerekce}] — yerel hukuk (Anayasa/TCK/Basın K.)
    'haberler_isim_verilen_suclama',   // 'evet' | 'hayir'
    'haberler_isim_suclama_gerekce',
    'haberler_kaynaklar',              // JSON: [{kaynak_adi,orijinal_url,yayin_tarihi,arsiv_url,ekran_goruntusu}]
    'haberler_iddialar',               // JSON: [{iddia_metni,siniflandirma,gerekce,dayanak_kaynak_url}]
];

const HABERLER_SORUN_ETIKET = [
    'yalan_haber'   => 'Yalan haber',
    'iftira'        => 'İftira',
    'toptan_suclama'=> 'Toptan suçlama',
    'carpitma'      => 'Çarpıtma / bağlam saptırma',
    'sorun_yok'     => 'Belirgin sorun yok',
];

// Uluslararası habercilik/dezenformasyon literatüründe karşılığı — ağırdan hafife (en üstte gösterilir)
const HABERLER_KATEGORI = [
    'kara_propaganda' => [
        'tr'   => 'Kara Propaganda · Hedef Gösterme',
        'en'   => 'Black Propaganda / Character Assassination',
        'desc' => 'Habercilik standardının tümüyle dışında. Kurgulanmış, sistematik iftira ve hedef gösterme; yaşayan kişileri delilsiz suçlu ilan eden, nefrete tahrik eden metin. Uluslararası ölçütlerde “haber” sayılmaz; medya eliyle yargısız infaz (trial by media) örneğidir.',
        'sev'  => 5,
    ],
    'dezenformasyon' => [
        'tr'   => 'Dezenformasyon · İftira Haberi',
        'en'   => 'Disinformation / Defamatory Smear',
        'desc' => 'Kasıtlı yanlış bilgi ve iftira ağırlıklı. Gerçek dışı isnatlar olgu gibi sunulmuş, zarar verme niyeti belirgin.',
        'sev'  => 4,
    ],
    'manipulatif' => [
        'tr'   => 'Manipülatif Habercilik · Çarpıtma',
        'en'   => 'Yellow Journalism / Misleading Spin',
        'desc' => 'Bağlam saptırma, sansasyon ve tek taraflılık. Olgular seçici biçimde sunulmuş, okuyucu yönlendirilmiştir.',
        'sev'  => 3,
    ],
    'dogrulanmamis' => [
        'tr'   => 'Doğrulanmamış Habercilik',
        'en'   => 'Misinformation / Unverified Reporting',
        'desc' => 'Kaynaksız veya doğrulanmamış iddialar içeriyor; kötü niyet açık değil ancak doğruluk standardı karşılanmamış.',
        'sev'  => 2,
    ],
    'kabul_edilebilir' => [
        'tr'   => 'Kabul Edilebilir Habercilik',
        'en'   => 'Acceptable Reporting',
        'desc' => 'Belirgin bir habercilik etiği ihlali tespit edilmedi.',
        'sev'  => 1,
    ],
];

// Haberde ihlal edilen / risk altındaki temel hak ve özgürlükler — yerel (Anayasa) + uluslararası (AİHS)
const HABERLER_HAK_ETIKET = [
    'ozel_hayat'      => 'Özel hayatın gizliliği (Anayasa m.20 · AİHS m.8)',
    'din_vicdan'      => 'Din ve vicdan özgürlüğü (Anayasa m.24 · AİHS m.9)',
    'orgutlenme'      => 'Dernek/vakıf ve örgütlenme özgürlüğü (Anayasa m.33-34 · AİHS m.11)',
    'masumiyet'       => 'Masumiyet karinesi (Anayasa m.38/4 · AİHS m.6/2)',
    'adil_yargilanma' => 'Adil yargılanma hakkı (Anayasa m.36 · AİHS m.6)',
    'kanunsuz_ceza'   => 'Suç ve cezaların kanuniliği (Anayasa m.38 · AİHS m.7)',
    'ifade'           => 'İfade özgürlüğü (Anayasa m.26 · AİHS m.10)',
    'ayrimcilik'      => 'Ayrımcılık yasağı (Anayasa m.10 · AİHS m.14)',
    'kisi_hurriyeti'  => 'Kişi hürriyeti ve güvenliği (Anayasa m.19 · AİHS m.5)',
    'seref_itibar'    => 'Şeref ve itibarın korunması (Anayasa m.17 · AİHS m.8)',
];

add_action('init', function () {
    $auth = function () { return current_user_can('edit_posts'); };
    foreach (HABERLER_META as $key) {
        register_post_meta('post', $key, [
            'type'          => 'string',
            'single'        => true,
            'show_in_rest'  => true,
            'auth_callback' => $auth,
        ]);
    }
    // Hukuk onayı bayrağı — REST'e KAPALI (sadece WP içinden, yetkili rol set eder)
    register_post_meta('post', '_hukuk_onayi', [
        'type'          => 'string',
        'single'        => true,
        'show_in_rest'  => false,
        'auth_callback' => function () { return current_user_can('edit_others_posts'); },
    ]);
});

/* ---------- Admin meta kutusu ---------- */

add_action('add_meta_boxes', function () {
    add_meta_box('haberler_dosya', 'Dosya (Doğruluk Denetimi)', 'haberler_dosya_box', 'post', 'normal', 'high');
});

function haberler_dosya_box($post) {
    wp_nonce_field('haberler_dosya_save', 'haberler_dosya_nonce');
    $ozet = get_post_meta($post->ID, 'haberler_ozet', true);
    $isim = get_post_meta($post->ID, 'haberler_isim_verilen_suclama', true) ?: 'hayir';
    $ger  = get_post_meta($post->ID, 'haberler_isim_suclama_gerekce', true);
    $kay  = get_post_meta($post->ID, 'haberler_kaynaklar', true);
    $idd  = get_post_meta($post->ID, 'haberler_iddialar', true);
    $gd = get_post_meta($post->ID, 'haberler_genel_degerlendirme', true);
    ?>
    <p><strong>Özet</strong></p>
    <textarea name="haberler_ozet" rows="4" style="width:100%"><?php echo esc_textarea($ozet); ?></textarea>

    <p style="margin-top:14px"><strong>Genel Değerlendirme</strong> (hukuki-gazetecilik dili)</p>
    <textarea name="haberler_genel_degerlendirme" rows="5" style="width:100%"><?php echo esc_textarea($gd); ?></textarea>

    <p style="margin-top:14px"><strong>Medya kategorisi</strong> (uluslararası habercilik değerlendirmesi — en üstte gösterilir)</p>
    <?php $mk = get_post_meta($post->ID, 'haberler_medya_kategori', true); ?>
    <select name="haberler_medya_kategori">
        <option value="">— seçilmedi —</option>
        <?php foreach (HABERLER_KATEGORI as $k => $v): ?>
            <option value="<?php echo esc_attr($k); ?>" <?php selected($mk, $k); ?>><?php echo esc_html($v['tr'] . ' (' . $v['en'] . ')'); ?></option>
        <?php endforeach; ?>
    </select>
    <p style="margin-top:8px"><strong>Kategori gerekçesi</strong></p>
    <textarea name="haberler_kategori_gerekce" rows="2" style="width:100%"><?php echo esc_textarea(get_post_meta($post->ID, 'haberler_kategori_gerekce', true)); ?></textarea>
    <p style="margin-top:8px"><strong>Halk ağzı / amiyane tabir</strong> ("en hafif tabirle ...") —
       <span style="color:#888">örn. çamur atma, kara çalma, fişleme gazeteciliği</span></p>
    <input type="text" name="haberler_halk_tabiri" style="width:100%" value="<?php echo esc_attr(get_post_meta($post->ID, 'haberler_halk_tabiri', true)); ?>">

    <p style="margin-top:14px"><strong>Suçlamanın araçsallaştırılması</strong> notu
       <span style="color:#888">('FETÖ' yaftasının siyaseten silah olarak kullanımı; yoksa boş bırak)</span></p>
    <textarea name="haberler_araclastirma" rows="3" style="width:100%"><?php echo esc_textarea(get_post_meta($post->ID, 'haberler_araclastirma', true)); ?></textarea>

    <p style="margin-top:14px"><strong>Haber sorunu</strong> (JSON dizi) —
       <code>["yalan_haber","iftira","toptan_suclama","carpitma"]</code> veya <code>["sorun_yok"]</code></p>
    <textarea name="haberler_haber_sorunu" rows="2" style="width:100%;font-family:monospace"><?php echo esc_textarea(get_post_meta($post->ID, 'haberler_haber_sorunu', true)); ?></textarea>

    <p style="margin-top:14px"><strong>İhlal edilen / risk altındaki haklar</strong> (JSON dizi) —
       <code>["ozel_hayat","din_vicdan","orgutlenme","masumiyet","adil_yargilanma","kanunsuz_ceza","ifade","ayrimcilik"]</code></p>
    <textarea name="haberler_ihlal_haklar" rows="2" style="width:100%;font-family:monospace"><?php echo esc_textarea(get_post_meta($post->ID, 'haberler_ihlal_haklar', true)); ?></textarea>

    <p style="margin-top:14px"><strong>İlgili kanun maddeleri</strong> (yerel hukuk, JSON) —
       <code>[{"kanun":"TCK","madde":"267","gerekce":"..."}]</code></p>
    <textarea name="haberler_kanun_maddeleri" rows="4" style="width:100%;font-family:monospace"><?php echo esc_textarea(get_post_meta($post->ID, 'haberler_kanun_maddeleri', true)); ?></textarea>

    <p style="margin-top:14px"><strong>İsim verilen suçlama var mı?</strong>
       <span style="color:#a00">(evet ise hukuk kapısı tetiklenir)</span></p>
    <select name="haberler_isim_verilen_suclama">
        <option value="hayir" <?php selected($isim, 'hayir'); ?>>Hayır</option>
        <option value="evet"  <?php selected($isim, 'evet'); ?>>Evet</option>
    </select>

    <p style="margin-top:14px"><strong>İsim verilen suçlama — gerekçe</strong></p>
    <textarea name="haberler_isim_suclama_gerekce" rows="2" style="width:100%"><?php echo esc_textarea($ger); ?></textarea>

    <p style="margin-top:14px"><strong>Kaynaklar (JSON)</strong>
       — <code>[{"kaynak_adi","orijinal_url","yayin_tarihi","arsiv_url","ekran_goruntusu"}]</code></p>
    <textarea name="haberler_kaynaklar" rows="6" style="width:100%;font-family:monospace"><?php echo esc_textarea($kay); ?></textarea>
    <?php haberler_kaynak_onizleme($kay); ?>

    <p style="margin-top:14px"><strong>İddialar (JSON)</strong>
       — <code>[{"iddia_metni","siniflandirma","gerekce","dayanak_kaynak_url"}]</code></p>
    <textarea name="haberler_iddialar" rows="8" style="width:100%;font-family:monospace"><?php echo esc_textarea($idd); ?></textarea>
    <?php haberler_iddia_onizleme($idd); ?>
    <?php
}

function haberler_kaynak_onizleme($json) {
    $rows = json_decode((string) $json, true);
    if (!is_array($rows) || !$rows) return;
    echo '<table class="widefat striped" style="margin-top:8px"><thead><tr><th>Kaynak</th><th>URL</th><th>Tarih</th></tr></thead><tbody>';
    foreach ($rows as $r) {
        printf(
            '<tr><td>%s</td><td><a href="%s" target="_blank" rel="noopener">%s</a></td><td>%s</td></tr>',
            esc_html($r['kaynak_adi'] ?? ''),
            esc_url($r['orijinal_url'] ?? ''),
            esc_html($r['orijinal_url'] ?? ''),
            esc_html($r['yayin_tarihi'] ?? '')
        );
    }
    echo '</tbody></table>';
}

function haberler_iddia_onizleme($json) {
    $rows = json_decode((string) $json, true);
    if (!is_array($rows) || !$rows) return;
    $renk = [
        'dogru' => '#1a7f37', 'kismen_dogru' => '#9a6700', 'yanlis' => '#cf222e',
        'dogrulanamaz' => '#57606a', 'gorus' => '#8250df',
    ];
    echo '<div style="margin-top:8px">';
    foreach ($rows as $r) {
        $s = $r['siniflandirma'] ?? 'dogrulanamaz';
        printf(
            '<div style="border-left:4px solid %s;padding:4px 10px;margin:6px 0;background:#f6f8fa">
               <span style="color:%s;font-weight:600;text-transform:uppercase;font-size:11px">%s</span><br>%s</div>',
            esc_attr($renk[$s] ?? '#57606a'),
            esc_attr($renk[$s] ?? '#57606a'),
            esc_html($s),
            esc_html($r['iddia_metni'] ?? '')
        );
    }
    echo '</div>';
}

add_action('save_post_post', function ($post_id) {
    if (!isset($_POST['haberler_dosya_nonce']) ||
        !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['haberler_dosya_nonce'])), 'haberler_dosya_save')) return;
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) return;
    if (!current_user_can('edit_post', $post_id)) return;

    foreach (HABERLER_META as $key) {
        if (!isset($_POST[$key])) continue;
        // JSON alanlarını ham bırak (sadece slash temizle); diğerlerini metin temizle
        if (in_array($key, ['haberler_kaynaklar', 'haberler_iddialar', 'haberler_haber_sorunu', 'haberler_ihlal_haklar', 'haberler_kanun_maddeleri'], true)) {
            update_post_meta($post_id, $key, wp_unslash($_POST[$key]));
        } elseif (in_array($key, ['haberler_ozet', 'haberler_genel_degerlendirme', 'haberler_ozet_en', 'haberler_genel_degerlendirme_en', 'haberler_kategori_gerekce', 'haberler_araclastirma'], true)) {
            update_post_meta($post_id, $key, sanitize_textarea_field(wp_unslash($_POST[$key])));
        } else {
            update_post_meta($post_id, $key, sanitize_text_field(wp_unslash($_POST[$key])));
        }
    }
});
