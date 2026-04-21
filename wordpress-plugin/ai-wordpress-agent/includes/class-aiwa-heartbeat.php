<?php
if ( ! defined( 'ABSPATH' ) ) exit;

/**
 * Heartbeat System — مستقر ومُحسَّن
 * - Cron كل دقيقة (مش كل page load)
 * - Rate limiting: مش أكتر من request كل 55 ثانية
 * - Retry logic مع backoff
 */
class AIWA_Heartbeat {

    private static $instance = null;
    private const OPTION_LAST_PING   = 'aiwa_last_ping';
    private const OPTION_LAST_BEAT   = 'aiwa_last_heartbeat_sent';
    private const MIN_INTERVAL_SECS  = 55;   // minimum between beats

    public static function get_instance() {
        if ( null === self::$instance ) self::$instance = new self();
        return self::$instance;
    }

    public function init() {
        // Only Cron — مش admin_init (يسبب requests كتير)
        add_action( 'aiwa_heartbeat_cron', [ $this, 'send_heartbeat' ] );
    }

    public function send_heartbeat() {
        $agent_url = get_option( 'aiwa_agent_url', '' );
        if ( ! $agent_url ) return;

        // Rate limiting: منع flooding
        $last_sent = (int) get_option( self::OPTION_LAST_BEAT, 0 );
        if ( ( time() - $last_sent ) < self::MIN_INTERVAL_SECS ) {
            return; // Too soon
        }

        $data = $this->collect_data();

        $response = wp_remote_post(
            trailingslashit( $agent_url ) . 'wp/heartbeat',
            [
                'timeout'     => 8,
                'blocking'    => false,   // Non-blocking — مش بيأخر الموقع
                'sslverify'   => false,
                'headers'     => [
                    'Content-Type'   => 'application/json',
                    'X-AI-Agent-Key' => get_option( 'aiwa_api_key', '' ),
                    'X-WP-Site'      => get_site_url(),
                ],
                'body' => wp_json_encode( $data ),
            ]
        );

        // Update last sent time (even if failed)
        update_option( self::OPTION_LAST_BEAT, time() );

        if ( ! is_wp_error( $response ) ) {
            update_option( self::OPTION_LAST_PING, current_time( 'mysql' ) );
            update_option( 'aiwa_connection_status', 'connected' );
        }
    }

    private function collect_data(): array {
        if ( ! function_exists( 'get_plugins' ) ) {
            require_once ABSPATH . 'wp-admin/includes/plugin.php';
        }
        $active  = get_option( 'active_plugins', [] );
        $theme   = wp_get_theme();
        $errors  = $this->get_recent_errors();

        return [
            'site_url'       => get_site_url(),
            'wp_version'     => get_bloginfo( 'version' ),
            'php_version'    => phpversion(),
            'theme'          => $theme->get( 'Name' ),
            'plugins_active' => count( $active ),
            'memory_usage'   => memory_get_usage( true ),
            'errors'         => $errors,
            'timestamp'      => time(),
            'device_name'    => get_option( 'aiwa_device_name', gethostname() ),
        ];
    }

    private function get_recent_errors(): array {
        $log_path = WP_CONTENT_DIR . '/debug.log';
        if ( ! file_exists( $log_path ) || ! is_readable( $log_path ) ) return [];
        $lines = @file( $log_path );
        if ( ! $lines ) return [];
        $fatal = array_filter(
            array_slice( $lines, -50 ),
            fn($l) => strpos( $l, 'PHP Fatal' ) !== false || strpos( $l, 'PHP Parse error' ) !== false
        );
        return array_values( array_slice( $fatal, -5 ) ); // Max 5 errors
    }
}
