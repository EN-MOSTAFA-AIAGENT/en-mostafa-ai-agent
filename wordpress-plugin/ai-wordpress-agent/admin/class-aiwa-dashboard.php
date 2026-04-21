<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class AIWA_Dashboard {

    private static $instance = null;

    public static function get_instance() {
        if ( null === self::$instance ) self::$instance = new self();
        return self::$instance;
    }

    public function register_menu() {
        add_menu_page(
            'AI WordPress Agent',
            '🤖 AI Agent',
            'manage_options',
            'ai-wp-agent',
            [$this, 'render_main'],
            'dashicons-superhero',
            2
        );
        add_submenu_page('ai-wp-agent', 'Overview',    'Overview',    'manage_options', 'ai-wp-agent',              [$this, 'render_main']);
        add_submenu_page('ai-wp-agent', 'Sites',       'Multi-Sites', 'manage_options', 'ai-wp-agent-sites',        [$this, 'render_sites']);
        add_submenu_page('ai-wp-agent', 'LearnDash',   'LearnDash',   'manage_options', 'ai-wp-agent-learndash',    [$this, 'render_learndash']);
        add_submenu_page('ai-wp-agent', 'MasterStudy', 'MasterStudy', 'manage_options', 'ai-wp-agent-masterstudy',  [$this, 'render_masterstudy']);
        add_submenu_page('ai-wp-agent', 'Knowledge',   'Knowledge',   'manage_options', 'ai-wp-agent-knowledge',    [$this, 'render_knowledge']);
        add_submenu_page('ai-wp-agent', 'Settings',    'Settings',    'manage_options', 'ai-wp-agent-settings',     [$this, 'render_settings']);
        add_submenu_page('ai-wp-agent', 'Heal Reports','Heal Reports','manage_options', 'ai-wp-agent-heal',         [$this, 'render_heal']);
    }

    // ─── Save Settings ──────────────────
    private function save_settings() {
        if ( ! current_user_can('manage_options') ) return;
        check_admin_referer('aiwa_settings_save');
        update_option('aiwa_agent_url',  esc_url_raw($_POST['agent_url'] ?? ''));
        update_option('aiwa_device_name', sanitize_text_field($_POST['device_name'] ?? ''));
        echo '<div class="notice notice-success"><p>✅ Settings saved.</p></div>';
    }

    // ─── Pages ──────────────────────────
    public function render_main() {
        $status     = get_option('aiwa_connection_status', 'disconnected');
        $last_ping  = get_option('aiwa_last_ping', 'Never');
        $api_key    = get_option('aiwa_api_key', '');
        $heal_rep   = get_option('aiwa_heal_reports', []);
        $theme      = wp_get_theme();
        $active_p   = count(get_option('active_plugins', []));
        $page_count = wp_count_posts('page')->publish;
        ?>
        <div class="wrap aiwa-wrap">
        <h1>🤖 AI WordPress Agent — Control Center</h1>
        <div class="aiwa-grid">

          <!-- Status Card -->
          <div class="aiwa-card <?php echo $status==='connected'?'card-green':'card-red'; ?>">
            <h3>⚡ Connection</h3>
            <p class="aiwa-big"><?php echo $status==='connected'?'🟢 Connected':'🔴 Disconnected'; ?></p>
            <p>Last ping: <strong><?php echo esc_html($last_ping); ?></strong></p>
          </div>

          <!-- Site Stats -->
          <div class="aiwa-card">
            <h3>📊 Site Overview</h3>
            <p>🎨 Theme: <strong><?php echo esc_html($theme->get('Name')); ?></strong></p>
            <p>🔌 Active Plugins: <strong><?php echo $active_p; ?></strong></p>
            <p>📄 Pages: <strong><?php echo $page_count; ?></strong></p>
            <p>🐘 PHP: <strong><?php echo phpversion(); ?></strong></p>
          </div>

          <!-- API Key -->
          <div class="aiwa-card">
            <h3>🔑 API Key</h3>
            <code style="word-break:break-all;font-size:11px;"><?php echo esc_html($api_key); ?></code>
            <br><br>
            <strong>Endpoint:</strong><br>
            <code><?php echo esc_html(get_rest_url(null, AIWA_API_BASE . '/ping')); ?></code>
          </div>

          <!-- Self-Heal -->
          <div class="aiwa-card">
            <h3>🛡️ Self-Heal Reports</h3>
            <p>Total events: <strong><?php echo count($heal_rep); ?></strong></p>
            <?php if($heal_rep): $last = end($heal_rep); ?>
            <p>Last: <?php echo esc_html($last['timestamp']??''); ?></p>
            <p>Actions: <?php echo implode(', ', array_map('esc_html', $last['actions']??[])); ?></p>
            <?php endif; ?>
            <a href="<?php echo admin_url('admin.php?page=ai-wp-agent-heal'); ?>" class="button">View All</a>
          </div>

        </div>
        <?php $this->render_styles(); ?>
        </div>
        <?php
    }

    public function render_settings() {
        if ( isset($_POST['aiwa_save']) ) $this->save_settings();
        $agent_url   = get_option('aiwa_agent_url', '');
        $device_name = get_option('aiwa_device_name', gethostname());
        ?>
        <div class="wrap aiwa-wrap">
        <h1>⚙️ Settings</h1>
        <form method="post">
        <?php wp_nonce_field('aiwa_settings_save'); ?>
        <table class="form-table">
          <tr>
            <th>Agent URL</th>
            <td><input type="url" name="agent_url" value="<?php echo esc_attr($agent_url); ?>" class="regular-text" placeholder="http://localhost:5000"></td>
          </tr>
          <tr>
            <th>Device Name</th>
            <td><input type="text" name="device_name" value="<?php echo esc_attr($device_name); ?>" class="regular-text"></td>
          </tr>
          <tr>
            <th>API Key</th>
            <td>
              <code><?php echo esc_html(get_option('aiwa_api_key','')); ?></code>
              <p class="description">Use this key in X-AI-Agent-Key header</p>
            </td>
          </tr>
        </table>
        <input type="hidden" name="aiwa_save" value="1">
        <?php submit_button('Save Settings'); ?>
        </form>
        <?php $this->render_styles(); ?>
        </div>
        <?php
    }

    public function render_sites() {
        echo '<div class="wrap aiwa-wrap"><h1>🌐 Multi-Site Management</h1>';
        echo '<p class="description">Manage multiple WordPress sites from one place via the AI Agent REST API.</p>';
        echo '<div class="aiwa-card"><h3>Add Site</h3><p>Configure site connections in <a href="' . admin_url('admin.php?page=ai-wp-agent-settings') . '">Settings</a> → Agent URL.</p></div>';
        $this->render_styles();
        echo '</div>';
    }

    public function render_learndash() {
        echo '<div class="wrap aiwa-wrap"><h1>🎓 LearnDash Management</h1>';
        if ( ! post_type_exists('sfwd-courses') ) {
            echo '<div class="notice notice-warning"><p>LearnDash is not active on this site.</p></div>';
        } else {
            $courses = get_posts(['post_type'=>'sfwd-courses','posts_per_page'=>-1,'post_status'=>'any']);
            echo '<table class="wp-list-table widefat fixed striped"><thead><tr><th>ID</th><th>Title</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
            foreach($courses as $c) {
                echo "<tr><td>{$c->ID}</td><td>" . esc_html($c->post_title) . "</td><td>{$c->post_status}</td><td><a href='" . get_edit_post_link($c->ID) . "'>Edit</a></td></tr>";
            }
            echo '</tbody></table>';
        }
        $this->render_styles();
        echo '</div>';
    }

    public function render_masterstudy() {
        echo '<div class="wrap aiwa-wrap"><h1>📚 MasterStudy LMS Management</h1>';
        if ( ! post_type_exists('stm-courses') ) {
            echo '<div class="notice notice-warning"><p>MasterStudy LMS is not detected or active on this site.</p></div>';
        } else {
            $courses = get_posts(['post_type' => 'stm-courses', 'posts_per_page' => -1, 'post_status' => 'any']);
            echo '<table class="wp-list-table widefat fixed striped"><thead><tr><th>ID</th><th>Course Title</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
            foreach($courses as $c) {
                echo "<tr><td>{$c->ID}</td><td><strong>" . esc_html($c->post_title) . "</strong></td><td>{$c->post_status}</td><td><a href='" . get_edit_post_link($c->ID) . "'>Edit</a></td></tr>";
            }
            echo '</tbody></table>';
        }
        $this->render_styles();
        echo '</div>';
    }

    public function render_knowledge() {
        echo '<div class="wrap aiwa-wrap"><h1>📚 Knowledge Base</h1>';
        echo '<p>Upload documents to train the AI Agent from your WordPress admin.</p>';
        echo '<div class="aiwa-card"><h3>📤 Upload Document</h3>';
        echo '<form method="post" enctype="multipart/form-data"><input type="file" name="knowledge_file" accept=".pdf,.txt,.md"><br><br><button class="button button-primary">Upload & Learn</button></form>';
        echo '</div>';
        $this->render_styles();
        echo '</div>';
    }

    public function render_heal() {
        $reports = array_reverse(get_option('aiwa_heal_reports', []));
        echo '<div class="wrap aiwa-wrap"><h1>🛡️ Self-Heal Reports</h1>';
        if(empty($reports)){ echo '<p>No heal events recorded.</p>'; }
        else {
            echo '<table class="wp-list-table widefat fixed striped"><thead><tr><th>Time</th><th>Error</th><th>Actions Taken</th></tr></thead><tbody>';
            foreach($reports as $r) {
                echo '<tr><td>' . esc_html($r['timestamp']??'') . '</td><td style="max-width:400px;overflow:hidden;font-size:11px;">' . esc_html(substr($r['error']??'',0,200)) . '</td><td>' . esc_html(implode(', ',$r['actions']??[])) . '</td></tr>';
            }
            echo '</tbody></table>';
        }
        $this->render_styles();
        echo '</div>';
    }

    private function render_styles() { ?>
        <style>
        .aiwa-wrap { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
        .aiwa-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; margin-top: 20px; }
        .aiwa-card { background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,.06); }
        .aiwa-card h3 { margin-top: 0; font-size: 15px; border-bottom: 1px solid #f0f0f0; padding-bottom: 8px; }
        .aiwa-big { font-size: 22px; font-weight: bold; margin: 10px 0; }
        .card-green { border-left: 4px solid #10b981; }
        .card-red   { border-left: 4px solid #ef4444; }
        </style>
    <?php }
}
