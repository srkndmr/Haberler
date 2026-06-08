<?php
/**
 * Plugin Name: Haberler — İş Akışı Durumları
 * Description: Özel yazı durumları: Otomatik Taslak, Doğrulama, Hukuk İncelemesi, Yayına Hazır.
 *              (PublishPress kurulmasa da çalışır.)
 */
if (!defined('ABSPATH')) exit;

function haberler_durumlar_list() {
    return [
        'otomatik-taslak'  => 'Otomatik Taslak',
        'dogrulama'        => 'Doğrulama',
        'hukuk-incelemesi' => 'Hukuk İncelemesi',
        'yayina-hazir'     => 'Yayına Hazır',
    ];
}

add_action('init', function () {
    foreach (haberler_durumlar_list() as $slug => $label) {
        register_post_status($slug, [
            'label'                     => $label,
            'public'                    => false,
            'internal'                  => false,
            'protected'                 => true,
            'exclude_from_search'       => true,
            'show_in_admin_all_list'    => true,
            'show_in_admin_status_list' => true,
            /* translators: %s: count */
            'label_count'               => _n_noop(
                $label . ' <span class="count">(%s)</span>',
                $label . ' <span class="count">(%s)</span>'
            ),
        ]);
    }
});

/**
 * Klasik editör durum açılır menüsüne özel durumları ekle.
 * (Blok editör için PublishPress'in durum arayüzü önerilir; iş akışı ayrıca
 *  WP-CLI/REST ile de sürülebilir.)
 */
function haberler_durum_dropdown() {
    global $post;
    if (!$post || $post->post_type !== 'post') return;
    $durumlar = haberler_durumlar_list();
    $current  = $post->post_status;
    echo '<script>jQuery(function($){';
    foreach ($durumlar as $slug => $label) {
        printf("\$('select#post_status').append('<option value=\"%s\">%s</option>');", esc_js($slug), esc_js($label));
    }
    if (isset($durumlar[$current])) {
        printf(
            "\$('select#post_status').val('%s');\$('#post-status-display').text('%s');",
            esc_js($current), esc_js($durumlar[$current])
        );
    }
    echo '});</script>';
}
add_action('admin_footer-post.php', 'haberler_durum_dropdown');
add_action('admin_footer-post-new.php', 'haberler_durum_dropdown');
