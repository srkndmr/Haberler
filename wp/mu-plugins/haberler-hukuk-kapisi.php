<?php
/**
 * Plugin Name: Haberler — Hukuk Kapısı
 * Description: isim_verilen_suclama=evet olan dosya, "Hukuk onayı alındı" işaretlenmeden
 *              Yayına Hazır / Yayında durumuna GEÇEMEZ. Geçmeye çalışırsa Hukuk İncelemesi'ne döner.
 */
if (!defined('ABSPATH')) exit;

function haberler_hukuk_kapisi($new_status, $old_status, $post) {
    if ($post->post_type !== 'post') return;
    if (!in_array($new_status, ['publish', 'yayina-hazir'], true)) return;

    $isim = get_post_meta($post->ID, 'haberler_isim_verilen_suclama', true);
    $onay = get_post_meta($post->ID, '_hukuk_onayi', true);

    if ($isim === 'evet' && $onay !== '1') {
        // Sonsuz döngüyü önle: kendini geçici çıkar, durumu geri al, tekrar bağla.
        remove_action('transition_post_status', 'haberler_hukuk_kapisi', 10);
        wp_update_post(['ID' => $post->ID, 'post_status' => 'hukuk-incelemesi']);
        add_action('transition_post_status', 'haberler_hukuk_kapisi', 10, 3);
        set_transient('haberler_kapi_' . $post->ID, 1, 60);
    }
}
add_action('transition_post_status', 'haberler_hukuk_kapisi', 10, 3);

// Yöneticiye/hukukçuya neden engellendiğini bildir.
add_action('admin_notices', function () {
    global $post;
    if ($post && get_transient('haberler_kapi_' . $post->ID)) {
        delete_transient('haberler_kapi_' . $post->ID);
        echo '<div class="notice notice-error"><p><strong>Hukuk kapısı:</strong> '
           . 'Bu dosyada isim verilen suçlama var ve hukuk onayı alınmamış. '
           . 'Durum otomatik olarak <em>Hukuk İncelemesi</em>ne alındı.</p></div>';
    }
});

/* ---------- Hukuk onayı kutusu (sadece yetkili rol) ---------- */

add_action('add_meta_boxes', function () {
    // publish yetkisi olan (Yönetici/Editör) veya başkasının yazısını düzenleyebilen (Hukuk Danışmanı)
    if (current_user_can('publish_posts') || current_user_can('edit_others_posts')) {
        add_meta_box('haberler_hukuk_onay', 'Hukuk Onayı', 'haberler_hukuk_onay_box', 'post', 'side', 'high');
    }
});

function haberler_hukuk_onay_box($post) {
    wp_nonce_field('haberler_onay_save', 'haberler_onay_nonce');
    $onay = get_post_meta($post->ID, '_hukuk_onayi', true);
    echo '<label><input type="checkbox" name="haberler_hukuk_onayi" value="1" ' . checked($onay, '1', false) . '> '
       . '<strong>Hukuk onayı alındı</strong></label>';
    echo '<p style="color:#666;font-size:11px;margin-top:8px">İsim verilen suçlama içeren dosyalar bu kutu '
       . 'işaretlenmeden <em>Yayına Hazır</em> / <em>Yayında</em> olamaz.</p>';
}

add_action('save_post_post', function ($post_id) {
    if (!isset($_POST['haberler_onay_nonce']) ||
        !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['haberler_onay_nonce'])), 'haberler_onay_save')) return;
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) return;
    if (!(current_user_can('publish_posts') || current_user_can('edit_others_posts'))) return;
    update_post_meta($post_id, '_hukuk_onayi', isset($_POST['haberler_hukuk_onayi']) ? '1' : '0');
});
