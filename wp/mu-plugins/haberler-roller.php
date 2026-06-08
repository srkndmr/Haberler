<?php
/**
 * Plugin Name: Haberler — Roller
 * Description: "Hukuk Danışmanı" özel rolünü ekler. Tek başına YAYINLAYAMAZ.
 */
if (!defined('ABSPATH')) exit;

add_action('init', function () {
    if (!get_role('hukuk_danismani')) {
        add_role('hukuk_danismani', 'Hukuk Danışmanı', [
            'read'                 => true,
            'edit_posts'           => true,
            'edit_others_posts'    => true,
            'edit_published_posts' => true,
            'moderate_comments'    => true,
            'upload_files'         => true,
            'publish_posts'        => false, // tek başına yayınlayamaz
            'delete_posts'         => false,
        ]);
    }
});
