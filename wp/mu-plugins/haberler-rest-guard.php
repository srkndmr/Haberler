<?php
/**
 * Plugin Name: Haberler — REST Durum Koruması
 * Description: REST ile bir yazı güncellenirken istek gövdesinde 'status' AÇIKÇA yoksa,
 *              mevcut durumu KORUR. Böylece meta-yalnızca güncellemeler (ör. AI yeniden analiz)
 *              özel durumları (otomatik-taslak vb.) yanlışlıkla 'publish'e çeviremez.
 *              "İnsan onayı olmadan yayın yok" ilkesinin teknik güvencesi.
 */
if (!defined('ABSPATH')) exit;

add_filter('rest_pre_insert_post', function ($prepared, $request) {
    $id = (int) ($request['id'] ?? 0);
    if ($id && !isset($request['status'])) {
        $current = get_post_status($id);
        if ($current) {
            $prepared->post_status = $current; // durumu olduğu gibi bırak
        }
    }
    return $prepared;
}, 10, 2);
