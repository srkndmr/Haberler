<?php
/**
 * Linkten Haber İncele — on-demand analiz modülü.
 * Akış: admin formu → iş kuyruğa (option) yazılır → host'taki Python izleyici
 * (incele_watch.py) REST ile çeker, hibrit-pipeline ile analiz eder, taslak dosya
 * oluşturur ve işi 'hazir' işaretler. Admin sayfasında durum görünür.
 */

const HABERLER_KUYRUK_OPT = 'haberler_incele_kuyruk';

/* ---------- Admin menü + sayfa ---------- */
add_action('admin_menu', function () {
    add_menu_page(
        'Linkten Haber İncele', 'Haber İncele', 'edit_posts',
        'haberler-incele', 'haberler_incele_sayfa', 'dashicons-search', 27
    );
});

function haberler_incele_kuyruk_getir() {
    $q = get_option(HABERLER_KUYRUK_OPT, []);
    return is_array($q) ? $q : [];
}

function haberler_incele_sayfa() {
    if (!current_user_can('edit_posts')) return;
    $kuyruk = haberler_incele_kuyruk_getir();
    ?>
    <div class="wrap">
      <h1>🔎 Linkten Haber İncele</h1>
      <p>Bir haber <strong>linki</strong> yapıştır (ve/veya metnini yapıştır). Sistem, arka planda
         AI ile analiz edip <strong>otomatik-taslak</strong> bir dosya oluşturur. Site otomatik metin
         çekmeyi engellerse, <em>haber metnini</em> yapıştırman en güvenilir yoldur.</p>

      <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>" style="max-width:760px">
        <?php wp_nonce_field('haberler_incele_ekle'); ?>
        <input type="hidden" name="action" value="haberler_incele_ekle">
        <table class="form-table">
          <tr><th><label for="hi_url">Haber linki</label></th>
              <td><input type="url" id="hi_url" name="hi_url" class="regular-text" placeholder="https://..." style="width:100%"></td></tr>
          <tr><th><label for="hi_baslik">Başlık (opsiyonel)</label></th>
              <td><input type="text" id="hi_baslik" name="hi_baslik" class="regular-text" style="width:100%" placeholder="Boşsa linkten/metinden türetilir"></td></tr>
          <tr><th><label for="hi_metin">Haber metni (opsiyonel ama önerilir)</label></th>
              <td><textarea id="hi_metin" name="hi_metin" rows="10" style="width:100%" placeholder="Haberin tam metnini buraya yapıştır..."></textarea></td></tr>
        </table>
        <?php submit_button('Analiz Et'); ?>
      </form>

      <h2 style="margin-top:30px">Son işler</h2>
      <table class="widefat striped">
        <thead><tr><th>Zaman</th><th>Başlık / Link</th><th>Durum</th><th>Dosya</th></tr></thead>
        <tbody>
        <?php if (!$kuyruk): ?>
          <tr><td colspan="4">Henüz iş yok.</td></tr>
        <?php else: foreach (array_reverse($kuyruk) as $j):
          $durum = $j['durum'] ?? 'bekliyor';
          $renk = ['bekliyor'=>'#8a6b1f','isleniyor'=>'#1f4a85','hazir'=>'#1f7a44','hata'=>'#b3261e','atlandi'=>'#5a6b7e'][$durum] ?? '#333';
          ?>
          <tr>
            <td><?php echo esc_html(date('d.m H:i', (int)($j['ts'] ?? 0))); ?></td>
            <td><?php echo esc_html($j['baslik'] ?: ($j['url'] ?: '—')); ?>
                <?php if (!empty($j['url'])): ?><br><a href="<?php echo esc_url($j['url']); ?>" target="_blank" rel="noopener" style="font-size:11px"><?php echo esc_html(mb_substr($j['url'],0,70)); ?></a><?php endif; ?></td>
            <td><strong style="color:<?php echo $renk; ?>"><?php echo esc_html(strtoupper($durum)); ?></strong>
                <?php if (!empty($j['not'])): ?><br><span style="font-size:11px;color:#777"><?php echo esc_html($j['not']); ?></span><?php endif; ?></td>
            <td><?php if (!empty($j['post_id'])): ?>
                  <a href="<?php echo esc_url(admin_url('post.php?post='.(int)$j['post_id'].'&action=edit')); ?>">#<?php echo (int)$j['post_id']; ?> aç</a>
                <?php else: ?>—<?php endif; ?></td>
          </tr>
        <?php endforeach; endif; ?>
        </tbody>
      </table>
      <p style="color:#777;font-size:12px">Not: Analiz host'taki Python izleyici (incele_watch.py) tarafından yapılır; birkaç dakika sürebilir. Sayfayı yenileyerek durumu görebilirsin.</p>
    </div>
    <?php
}

/* ---------- Form gönderimi: işi kuyruğa ekle ---------- */
add_action('admin_post_haberler_incele_ekle', function () {
    if (!current_user_can('edit_posts')) wp_die('Yetki yok');
    check_admin_referer('haberler_incele_ekle');
    $url    = esc_url_raw(trim(wp_unslash($_POST['hi_url'] ?? '')));
    $baslik = sanitize_text_field(wp_unslash($_POST['hi_baslik'] ?? ''));
    $metin  = sanitize_textarea_field(wp_unslash($_POST['hi_metin'] ?? ''));
    if (!$url && !$metin) {
        wp_safe_redirect(add_query_arg('hi', 'bos', admin_url('admin.php?page=haberler-incele'))); exit;
    }
    $kuyruk = haberler_incele_kuyruk_getir();
    $kuyruk[] = [
        'job_id' => uniqid('hi_', true),
        'url'    => $url, 'baslik' => $baslik, 'metin' => $metin,
        'durum'  => 'bekliyor', 'ts' => time(), 'post_id' => 0, 'not' => '',
    ];
    // Son 100 işi tut
    if (count($kuyruk) > 100) $kuyruk = array_slice($kuyruk, -100);
    update_option(HABERLER_KUYRUK_OPT, $kuyruk, false);
    wp_safe_redirect(admin_url('admin.php?page=haberler-incele')); exit;
});

/* ---------- REST: izleyici için kuyruk API'si ---------- */
add_action('rest_api_init', function () {
    $izin = function () { return current_user_can('edit_posts'); };

    // Bekleyen işleri getir
    register_rest_route('haberler/v1', '/kuyruk', [
        'methods'  => 'GET',
        'permission_callback' => $izin,
        'callback' => function () {
            $bekleyen = array_values(array_filter(haberler_incele_kuyruk_getir(),
                function ($j) { return ($j['durum'] ?? '') === 'bekliyor'; }));
            return rest_ensure_response($bekleyen);
        },
    ]);

    // Bir işin durumunu güncelle
    register_rest_route('haberler/v1', '/kuyruk/durum', [
        'methods'  => 'POST',
        'permission_callback' => $izin,
        'callback' => function ($req) {
            $job_id  = sanitize_text_field((string) $req->get_param('job_id'));
            $durum   = sanitize_text_field((string) $req->get_param('durum'));
            $post_id = (int) $req->get_param('post_id');
            $not     = sanitize_text_field((string) $req->get_param('not'));
            $izinli  = ['bekliyor','isleniyor','hazir','hata','atlandi'];
            if (!$job_id || !in_array($durum, $izinli, true)) {
                return new WP_Error('gecersiz', 'job_id ve geçerli durum gerekli', ['status' => 400]);
            }
            $kuyruk = haberler_incele_kuyruk_getir(); $bulundu = false;
            foreach ($kuyruk as &$j) {
                if (($j['job_id'] ?? '') === $job_id) {
                    $j['durum'] = $durum;
                    if ($post_id) $j['post_id'] = $post_id;
                    if ($not !== '') $j['not'] = $not;
                    $bulundu = true; break;
                }
            }
            unset($j);
            if (!$bulundu) return new WP_Error('yok', 'iş bulunamadı', ['status' => 404]);
            update_option(HABERLER_KUYRUK_OPT, $kuyruk, false);
            return rest_ensure_response(['ok' => true]);
        },
    ]);
});
