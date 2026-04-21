<?php
if ( ! defined( 'ABSPATH' ) ) exit;

/**
 * Self-Healing Firewall
 * عند حدوث خطأ: قراءة error_log → تعطيل plugin → إصلاح → تقرير
 */
class AIWA_SelfHeal {

    private static $instance = null;

    public static function get_instance() {
        if ( null === self::$instance ) self::$instance = new self();
        return self::$instance;
    }

    public function init() {
        add_action( 'aiwa_heartbeat_cron', [ $this, 'check_and_heal' ] );
        // Catch fatal errors via shutdown
        register_shutdown_function( [ $this, 'handle_shutdown' ] );
    }

    public function handle_shutdown() {
        $error = error_get_last();
        if ( $error && in_array($error['type'], [E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR]) ) {
            $this->heal( $error['message'], $error['file'] );
        }
    }

    public function check_and_heal() {
        $log   = $this->read_recent_errors();
        $fatal = array_filter($log, fn($l) => strpos($l, 'Fatal') !== false || strpos($l, 'Parse error') !== false);
        foreach ( array_slice($fatal, 0, 3) as $error_line ) {
            $this->heal($error_line, '');
        }
    }

    public function heal( string $error_message, string $error_file ): array {
        $report = [
            'error'       => $error_message,
            'file'        => $error_file,
            'timestamp'   => current_time('mysql'),
            'actions'     => [],
        ];

        // 1. تحديد Plugin المسبب
        $plugin = $this->detect_plugin($error_file ?: $error_message);
        if ( $plugin ) {
            $this->disable_plugin($plugin);
            $report['actions'][] = "Disabled plugin: {$plugin}";
        }

        // 2. تنظيف الـ cache
        if ( function_exists('wp_cache_flush') ) {
            wp_cache_flush();
            $report['actions'][] = 'Cache flushed';
        }

        // 3. حفظ التقرير
        $reports   = get_option('aiwa_heal_reports', []);
        $reports[] = $report;
        update_option('aiwa_heal_reports', array_slice($reports, -20));  // keep last 20

        // 4. إرسال تقرير للـ Agent
        $this->send_report($report);

        return $report;
    }

    private function detect_plugin( string $error_text ): ?string {
        if ( ! function_exists('get_plugins') ) require_once ABSPATH . 'wp-admin/includes/plugin.php';
        $active = get_option('active_plugins', []);
        foreach ( $active as $plugin_file ) {
            $plugin_slug = explode('/', $plugin_file)[0];
            if ( stripos($error_text, $plugin_slug) !== false ) {
                return $plugin_file;
            }
        }
        // Check if error is in plugins directory
        if ( strpos($error_text, '/plugins/') !== false ) {
            preg_match('/plugins\/([^\/]+)/', $error_text, $m);
            if ( isset($m[1]) ) {
                foreach ( $active as $plugin_file ) {
                    if ( strpos($plugin_file, $m[1]) !== false ) return $plugin_file;
                }
            }
        }
        return null;
    }

    private function disable_plugin( string $plugin_file ) {
        if ( ! function_exists('deactivate_plugins') ) require_once ABSPATH . 'wp-admin/includes/plugin.php';
        deactivate_plugins($plugin_file);
        $disabled   = get_option('aiwa_disabled_plugins', []);
        $disabled[] = ['plugin' => $plugin_file, 'time' => current_time('mysql')];
        update_option('aiwa_disabled_plugins', $disabled);
    }

    private function send_report( array $report ) {
        $agent_url = get_option('aiwa_agent_url', '');
        if ( ! $agent_url ) return;
        wp_remote_post( trailingslashit($agent_url) . 'wp/error-report', [
            'timeout'  => 5,
            'blocking' => false,
            'headers'  => ['Content-Type' => 'application/json', 'X-AI-Agent-Key' => get_option('aiwa_api_key')],
            'body'     => json_encode($report),
        ]);
    }

    private function read_recent_errors(): array {
        $log_path = WP_CONTENT_DIR . '/debug.log';
        if ( ! file_exists($log_path) ) return [];
        return array_slice(file($log_path), -50);
    }
}
