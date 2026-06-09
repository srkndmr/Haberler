<?php
/**
 * Plugin Name: Haberler — Düzeltme Talebi Formu
 * Description: [haberler_iletisim] kısa kodu. Talepleri 'duzeltme_talebi' olarak saklar.
 *              Sadece talep toplar; otomatik yayın/aksiyon YOKTUR.
 */
if (!defined('ABSPATH')) exit;

// Talepleri tutacak özel tip (gizli, sadece yönetimde görünür)
add_action('init', function () {
    register_post_type('duzeltme_talebi', [
        'labels' => ['name' => 'Düzeltme Talepleri', 'singular_name' => 'Düzeltme Talebi'],
        'public' => false, 'show_ui' => true, 'menu_icon' => 'dashicons-email-alt',
        'supports' => ['title', 'editor'], 'capability_type' => 'post',
    ]);
});

add_shortcode('haberler_iletisim', function () {
    $sent = false; $err = '';

    if (($_SERVER['REQUEST_METHOD'] ?? '') === 'POST' && isset($_POST['haberler_il_nonce'])) {
        if (!wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['haberler_il_nonce'])), 'haberler_il')) {
            $err = 'Oturum süresi doldu, lütfen tekrar deneyin.';
        } elseif (!empty($_POST['website'])) {     // honeypot (botlar doldurur)
            $err = 'Geçersiz gönderim.';
        } else {
            $ad    = sanitize_text_field(wp_unslash($_POST['il_ad'] ?? ''));
            $email = sanitize_email(wp_unslash($_POST['il_eposta'] ?? ''));
            $dosya = esc_url_raw(wp_unslash($_POST['il_dosya'] ?? ''));
            $mesaj = sanitize_textarea_field(wp_unslash($_POST['il_mesaj'] ?? ''));
            if (!$ad || !$email || !$mesaj) {
                $err = 'Ad, e-posta ve mesaj zorunludur.';
            } else {
                $pid = wp_insert_post([
                    'post_type'   => 'duzeltme_talebi',
                    'post_status' => 'private',
                    'post_title'  => 'Düzeltme: ' . $ad . ' — ' . current_time('Y-m-d H:i'),
                    'post_content'=> $mesaj,
                    'meta_input'  => ['il_eposta' => $email, 'il_dosya' => $dosya, 'il_ad' => $ad],
                ]);
                if ($pid && !is_wp_error($pid)) {
                    $sent = true;
                    // Bilgilendirme e-postası (SMTP varsa gider; yoksa kayıt yine durur)
                    @wp_mail(get_option('admin_email'), 'Yeni düzeltme talebi',
                        "Ad: $ad\nE-posta: $email\nDosya: $dosya\n\nMesaj:\n$mesaj");
                } else {
                    $err = 'Kaydedilemedi, lütfen tekrar deneyin.';
                }
            }
        }
    }

    if ($sent) {
        return '<div style="background:#e7f7ed;border-left:4px solid #1a7f37;padding:14px 18px;border-radius:6px">'
             . '<strong>Talebiniz alındı.</strong> Her talep insan eliyle değerlendirilir; '
             . 'haklı bulunan düzeltmeler görünür biçimde yapılır. İlginiz için teşekkürler.</div>';
    }

    $h = '';
    if ($err) $h .= '<p style="color:#cf222e"><strong>' . esc_html($err) . '</strong></p>';
    $h .= '<form method="post" style="max-width:560px;display:grid;gap:12px">';
    $h .= wp_nonce_field('haberler_il', 'haberler_il_nonce', true, false);
    $h .= '<input type="text" name="website" style="display:none" tabindex="-1" autocomplete="off">'; // honeypot
    $h .= '<label>Ad Soyad *<br><input type="text" name="il_ad" required style="width:100%;padding:8px"></label>';
    $h .= '<label>E-posta *<br><input type="email" name="il_eposta" required style="width:100%;padding:8px"></label>';
    $h .= '<label>İlgili dosya linki<br><input type="url" name="il_dosya" placeholder="https://..." style="width:100%;padding:8px"></label>';
    $h .= '<label>Mesajınız *<br><textarea name="il_mesaj" rows="5" required style="width:100%;padding:8px"></textarea></label>';
    $h .= '<button type="submit" style="padding:10px 20px;background:#1f2937;color:#fff;border:0;border-radius:6px;cursor:pointer;justify-self:start">Gönder</button>';
    $h .= '<p style="font-size:.8rem;color:#666">Bu form yalnızca düzeltme talebi toplar; otomatik yayın veya aksiyon yapılmaz. '
        . 'Gönderdiğiniz bilgiler yalnızca talebinizi değerlendirmek için kullanılır (KVKK).</p>';
    $h .= '</form>';
    return $h;
});
