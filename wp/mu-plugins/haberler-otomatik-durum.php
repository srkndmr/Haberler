<?php
/**
 * Plugin Name: Haberler — Bot Taslak Durumu
 * Description: pipeline-bot'un REST ile oluşturduğu taslakları "Otomatik Taslak" durumuna çeker.
 *              Otomasyon ASLA yayınlayamaz; en fazla otomatik taslak üretir.
 */
if (!defined('ABSPATH')) exit;

add_action('rest_after_insert_post', function ($post, $request, $creating) {
    if (!$creating) return;
    $bot = get_user_by('login', 'pipeline-bot');
    if ($bot && (int) $post->post_author === (int) $bot->ID && $post->post_status === 'draft') {
        wp_update_post(['ID' => $post->ID, 'post_status' => 'otomatik-taslak']);
    }
}, 10, 3);
