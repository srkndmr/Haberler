<?php
/**
 * Plugin Name: Haberler — Hukuk Onayı & Yayınla Aksiyonu
 * Description: Yazılar listesinde tek tıkla "Hukuk onayı & Yayınla". Blok editördeki
 *              kayıt-sırası sorununu aşar (onay meta'sı yayından ÖNCE set edilir).
 *              Sadece yayın yetkisi olan rol (Yönetici/Editör) görebilir/kullanabilir.
 */
if (!defined('ABSPATH')) exit;

// Dosya mı? (özet veya iddia meta'sı var mı)
function haberler_dosya_mu($id) {
    return get_post_meta($id, 'haberler_ozet', true) || get_post_meta($id, 'haberler_iddialar', true);
}

// Yazılar listesine satır aksiyonu
add_filter('post_row_actions', function ($actions, $post) {
    if ($post->post_type !== 'post') return $actions;
    if (!current_user_can('publish_posts')) return $actions;
    if (!haberler_dosya_mu($post->ID)) return $actions;

    if ($post->post_status === 'publish') {
        // Yayındaki dosya: geri al (yayından kaldır -> taslak)
        $url = wp_nonce_url(
            admin_url('admin-post.php?action=haberler_geri_al&post=' . $post->ID),
            'haberler_geri_' . $post->ID
        );
        $actions['haberler_geri'] = '<a href="' . esc_url($url) . '" style="color:#b32d2e;font-weight:600" '
            . 'onclick="return confirm(\'Bu dosya yayından kaldırılıp taslağa alınacak. Emin misiniz?\')">'
            . '↩ Yayından kaldır</a>';
    } else {
        // Taslak/inceleme: hukuk onayı & yayınla
        $url = wp_nonce_url(
            admin_url('admin-post.php?action=haberler_onayla_yayinla&post=' . $post->ID),
            'haberler_onayla_' . $post->ID
        );
        $actions['haberler_onayla'] = '<a href="' . esc_url($url) . '" style="color:#1a7f37;font-weight:600">'
            . '✓ Hukuk onayı &amp; Yayınla</a>';
    }
    return $actions;
}, 10, 2);

// Geri alma işleyici (yayından kaldır -> otomatik-taslak, onay meta'sı silinir)
add_action('admin_post_haberler_geri_al', function () {
    $id = (int) ($_GET['post'] ?? 0);
    $nonce = sanitize_text_field(wp_unslash($_GET['_wpnonce'] ?? ''));
    if (!$id || !current_user_can('publish_posts') || !wp_verify_nonce($nonce, 'haberler_geri_' . $id)) {
        wp_die('Yetkisiz veya geçersiz istek.');
    }
    delete_post_meta($id, '_hukuk_onayi');
    wp_update_post(['ID' => $id, 'post_status' => 'otomatik-taslak']);
    wp_safe_redirect(admin_url('edit.php?haberler_geri_alindi=' . $id));
    exit;
});

// Aksiyon işleyici
add_action('admin_post_haberler_onayla_yayinla', function () {
    $id = (int) ($_GET['post'] ?? 0);
    $nonce = sanitize_text_field(wp_unslash($_GET['_wpnonce'] ?? ''));
    if (!$id || !current_user_can('publish_posts') || !wp_verify_nonce($nonce, 'haberler_onayla_' . $id)) {
        wp_die('Yetkisiz veya geçersiz istek.');
    }
    update_post_meta($id, '_hukuk_onayi', '1');           // onay ÖNCE
    wp_update_post(['ID' => $id, 'post_status' => 'publish']); // sonra yayınla (kapı onayı görür)
    wp_safe_redirect(admin_url('edit.php?haberler_yayinlandi=' . $id));
    exit;
});

add_action('admin_notices', function () {
    if (!empty($_GET['haberler_yayinlandi'])) {
        $id = (int) $_GET['haberler_yayinlandi'];
        $durum = get_post_status($id);
        if ($durum === 'publish') {
            echo '<div class="notice notice-success is-dismissible"><p><strong>Yayımlandı:</strong> '
               . 'Dosya hukuk onayı verilerek yayına alındı.</p></div>';
        } else {
            echo '<div class="notice notice-warning is-dismissible"><p>İşlem tamamlanamadı; durum: '
               . esc_html($durum) . '.</p></div>';
        }
    }
    if (!empty($_GET['haberler_geri_alindi'])) {
        echo '<div class="notice notice-success is-dismissible"><p><strong>Yayından kaldırıldı:</strong> '
           . 'Dosya taslağa (otomatik-taslak) alındı; herkese açık listelerde artık görünmez.</p></div>';
    }
});
