<?php
/**
 * Plugin Name: AI WordPress Agent
 * Plugin URI:  https://github.com/mostafa-ai-agent
 * Description: اتصال كامل بين WordPress والـ AI Agent — REST API, Heartbeat, WP-CLI, Elementor, LearnDash, MasterStudy
 * Version:     2.1.1
 * Author:      EN MOSTAFA AI AGENT
 * Text Domain: ai-wp-agent
 * Requires WP: 5.8
 * Requires PHP: 7.4
 */

if ( ! defined( 'ABSPATH' ) ) exit;

define( 'AIWA_VERSION',   '2.1.1' );
define( 'AIWA_DIR',       plugin_dir_path( __FILE__ ) );
define( 'AIWA_URL',       plugin_dir_url( __FILE__ ) );
define( 'AIWA_API_BASE',  'ai-agent/v1' );

// تحميل الملفات
require_once AIWA_DIR . 'includes/class-aiwa-api.php';
require_once AIWA_DIR . 'includes/class-aiwa-heartbeat.php';
require_once AIWA_DIR . 'includes/class-aiwa-elementor.php';
require_once AIWA_DIR . 'includes/class-aiwa-selfheal.php';
require_once AIWA_DIR . 'admin/class-aiwa-dashboard.php';

class AI_WordPress_Agent {

    private static $instance = null;

    public static function get_instance() {
        if ( null === self::$instance ) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        add_action( 'init',               [ $this, 'init' ] );
        add_action( 'rest_api_init',      [ $this, 'register_api' ] );
        add_action( 'admin_menu',         [ $this, 'admin_menu' ] );
        add_action( 'wp_dashboard_setup', [ $this, 'dashboard_widget' ] );

        register_activation_hook( __FILE__,   [ $this, 'activate' ] );
        register_deactivation_hook( __FILE__, [ $this, 'deactivate' ] );
    }

    public function init() {
        if ( class_exists( 'AIWA_Heartbeat' ) ) {
            AIWA_Heartbeat::get_instance()->init();
        }

        if ( class_exists( 'AIWA_SelfHeal' ) ) {
            AIWA_SelfHeal::get_instance()->init();
        }
    }

    public function register_api() {
        if ( class_exists( 'AIWA_API' ) ) {
            AIWA_API::get_instance()->register_routes();
        }
    }

    public function admin_menu() {
        if ( class_exists( 'AIWA_Dashboard' ) ) {
            AIWA_Dashboard::get_instance()->register_menu();
        }
    }

    // ── Dashboard Widget ──────────────────
    public function dashboard_widget() {
        wp_add_dashboard_widget(
            'aiwa_status_widget',
            '🤖 AI Agent Status',
            [ $this, 'render_widget' ]
        );
    }

    public function render_widget() {
        $status     = get_option( 'aiwa_connection_status', 'disconnected' );
        $device     = get_option( 'aiwa_device_name', 'Unknown' );
        $last       = get_option( 'aiwa_last_ping', 'Never' );
        $agent_url  = esc_url( get_option( 'aiwa_agent_url', '' ) );
        $color      = $status === 'connected' ? '#10b981' : '#ef4444';
        ?>
        <div style="font-family:monospace;padding:8px;">
            <p>● <strong style="color:<?php echo esc_attr($color); ?>">
                <?php echo esc_html( ucfirst($status) ); ?>
            </strong></p>

            <p>🖥️ Device: <strong><?php echo esc_html($device); ?></strong></p>
            <p>🕐 Last Ping: <?php echo esc_html($last); ?></p>

            <?php if ( $agent_url ) : ?>
                <p>🌐 Agent: <code style="font-size:10px;"><?php echo esc_html($agent_url); ?></code></p>
            <?php endif; ?>

            <p style="margin-top:10px;">
                <a href="<?php echo esc_url( admin_url('admin.php?page=ai-wp-agent') ); ?>" class="button button-primary">
                    Open Control Panel
                </a>

                <?php if ( $agent_url ) : ?>
                    <a href="<?php echo esc_url($agent_url . '/wp-dashboard'); ?>" target="_blank" class="button" style="margin-right:6px;">
                        AI Dashboard ↗
                    </a>
                <?php endif; ?>
            </p>
        </div>
        <?php
    }

    // ── Lifecycle ─────────────────────────
    public function activate() {
        update_option( 'aiwa_version', AIWA_VERSION );
        
        if ( ! get_option( 'aiwa_api_key' ) ) {
            update_option( 'aiwa_api_key', wp_generate_password( 32, false ) );
        }

        update_option( 'aiwa_active', 1 );

        // إنشاء الجداول اللازمة لإصلاح الـ Fatal Error
        $this->create_tables();

        // تشغيل Cron
        if ( ! wp_next_scheduled( 'aiwa_heartbeat_cron' ) ) {
            wp_schedule_event( time(), 'minutely', 'aiwa_heartbeat_cron' );
        }

        // تسجيل الموقع مع الـ Agent
        $this->register_with_agent();
    }

    public function deactivate() {
        wp_clear_scheduled_hook( 'aiwa_heartbeat_cron' );
        update_option( 'aiwa_active', 0 );
        update_option( 'aiwa_connection_status', 'disconnected' );
    }

    /**
     * إنشاء الجداول الأساسية للنظام
     */
    private function create_tables() {
        global $wpdb;
        $charset_collate = $wpdb->get_charset_collate();

        // جدول سجلات الأحداث (Event Logger)
        $table_name = $wpdb->prefix . 'aiwa_events';
        $sql = "CREATE TABLE $table_name (
            id bigint(20) NOT NULL AUTO_INCREMENT,
            event_type varchar(50) NOT NULL,
            event_data text NOT NULL,
            created_at datetime DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY  (id)
        ) $charset_collate;";

        require_once ABSPATH . 'wp-admin/includes/upgrade.php';
        dbDelta( $sql );
    }

    /**
     * تسجيل الموقع مع الـ Agent
     */
    public function register_with_agent() {
        $agent_url = esc_url_raw( get_option( 'aiwa_agent_url', '' ) );

        if ( ! $agent_url || ! filter_var( $agent_url, FILTER_VALIDATE_URL ) ) {
            return;
        }

        $payload = [
            'site_name' => get_bloginfo( 'name' ),
            'site_url'  => get_site_url(),
            'api_key'   => get_option( 'aiwa_api_key' ),
        ];

        $response = wp_remote_post(
            trailingslashit( $agent_url ) . 'wp/register-site',
            [
                'timeout' => 15,
                'headers' => [ 'Content-Type' => 'application/json' ],
                'body'    => wp_json_encode( $payload ),
            ]
        );

        if ( is_wp_error( $response ) ) {
            error_log( 'AIWA Error: ' . $response->get_error_message() );
            return;
        }

        $body = json_decode( wp_remote_retrieve_body( $response ), true );

        if ( is_array( $body ) ) {
            $status = ! empty( $body['connected'] ) ? 'connected' : 'registered';
            update_option( 'aiwa_connection_status', $status );
            update_option( 'aiwa_last_ping', current_time( 'mysql' ) );
        }
    }
}

// ── Cron كل دقيقة
add_filter( 'cron_schedules', function ( $s ) {
    $s['minutely'] = [
        'interval' => 60,
        'display'  => 'Every Minute'
    ];
    return $s;
} );

// ── إعادة التسجيل عند تغيير Agent URL
add_action( 'update_option_aiwa_agent_url', function () {
    AI_WordPress_Agent::get_instance()->register_with_agent();
});

// تشغيل الإضافة
AI_WordPress_Agent::get_instance();
