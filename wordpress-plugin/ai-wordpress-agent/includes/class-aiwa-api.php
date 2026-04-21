<?php
if ( ! defined( 'ABSPATH' ) ) exit;

/**
 * AI WordPress Agent — REST API v2.1
 * User Management + MasterStudy + Smart Ping
 */
class AIWA_API {

    private static $instance = null;

    public static function get_instance() {
        if ( null === self::$instance ) self::$instance = new self();
        return self::$instance;
    }

    public function init() {
        add_action( 'rest_api_init', [ $this, 'register_routes' ] );
    }

    private function ns(): string { return 'ai-agent/v1'; }

    private function verify_key( WP_REST_Request $req ): bool {
        $key = $req->get_header('X-AI-Agent-Key') ?: $req->get_param('api_key');
        return $key === get_option( 'aiwa_api_key', '' );
    }

    public function check_auth( WP_REST_Request $req ): bool {
        return $this->verify_key( $req );
    }

    private function auth_error(): array {
        return [ 'success' => false, 'error' => 'Unauthorized' ];
    }

    public function register_routes() {
        $ns = $this->ns();

        // ── Core ──────────────────────────────────────
        register_rest_route( $ns, '/ping', [
            'methods'             => 'GET',
            'callback'            => [ $this, 'ping' ],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route( $ns, '/site-info', [
            'methods'             => 'GET',
            'callback'            => [ $this, 'site_info' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);
        register_rest_route( $ns, '/error-log', [
            'methods'             => 'GET',
            'callback'            => [ $this, 'get_error_log' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);
        register_rest_route( $ns, '/run-cli', [
            'methods'             => 'POST',
            'callback'            => [ $this, 'run_cli' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);

        // ── Plugins ────────────────────────────────────
        register_rest_route( $ns, '/plugins', [
            'methods'             => 'GET',
            'callback'            => [ $this, 'get_plugins' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);
        register_rest_route( $ns, '/update-plugins', [
            'methods'             => 'POST',
            'callback'            => [ $this, 'update_plugins' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);
        register_rest_route( $ns, '/toggle-plugin', [
            'methods'             => 'POST',
            'callback'            => [ $this, 'toggle_plugin' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);

        // ── Users ──────────────────────────────────────
        register_rest_route( $ns, '/users', [
            'methods'             => 'GET',
            'callback'            => [ $this, 'list_users' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);
        register_rest_route( $ns, '/users/delete', [
            'methods'             => 'POST',
            'callback'            => [ $this, 'delete_user' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);
        register_rest_route( $ns, '/users/create', [
            'methods'             => 'POST',
            'callback'            => [ $this, 'create_user' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);
        register_rest_route( $ns, '/users/update', [
            'methods'             => 'POST',
            'callback'            => [ $this, 'update_user_role' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);

        // ── Elementor ──────────────────────────────────
        register_rest_route( $ns, '/elementor-data', [
            ['methods' => 'GET',  'callback' => [ $this, 'get_elementor' ], 'permission_callback' => [ $this, 'check_auth' ]],
            ['methods' => 'POST', 'callback' => [ $this, 'set_elementor' ], 'permission_callback' => [ $this, 'check_auth' ]],
        ]);

        // ── MasterStudy ────────────────────────────────
        register_rest_route( $ns, '/masterstudy/courses', [
            ['methods' => 'GET',  'callback' => [ $this, 'ms_get_courses' ],  'permission_callback' => [ $this, 'check_auth' ]],
            ['methods' => 'POST', 'callback' => [ $this, 'ms_create_course' ],'permission_callback' => [ $this, 'check_auth' ]],
        ]);
        register_rest_route( $ns, '/masterstudy/courses/(?P<id>\d+)', [
            'methods'             => 'GET',
            'callback'            => [ $this, 'ms_get_course' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);
        register_rest_route( $ns, '/masterstudy/courses/(?P<id>\d+)/lessons', [
            'methods'             => 'POST',
            'callback'            => [ $this, 'ms_add_lesson' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);
        register_rest_route( $ns, '/masterstudy/courses/(?P<id>\d+)/quizzes', [
            'methods'             => 'POST',
            'callback'            => [ $this, 'ms_add_quiz' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);
        register_rest_route( $ns, '/masterstudy/courses/(?P<id>\d+)/students', [
            'methods'             => 'GET',
            'callback'            => [ $this, 'ms_get_students' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);
        register_rest_route( $ns, '/masterstudy/enroll', [
            'methods'             => 'POST',
            'callback'            => [ $this, 'ms_enroll' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);
        register_rest_route( $ns, '/masterstudy/progress/(?P<user>\d+)/(?P<course>\d+)', [
            'methods'             => 'GET',
            'callback'            => [ $this, 'ms_progress' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);
        register_rest_route( $ns, '/masterstudy/students', [
            'methods'             => 'GET',
            'callback'            => [ $this, 'ms_all_students' ],
            'permission_callback' => [ $this, 'check_auth' ],
        ]);
    }

    // ════════════════════════════════════════
    //  CORE
    // ════════════════════════════════════════

    public function ping(): WP_REST_Response {
        return new WP_REST_Response([
            'success'        => true,
            'status'         => 'ok',
            'site_url'       => get_site_url(),
            'wp_version'     => get_bloginfo('version'),
            'plugin_version' => AIWA_VERSION,
            'timestamp'      => time(),
        ]);
    }

    public function site_info(): WP_REST_Response {
        global $wpdb;
        if ( ! function_exists( 'get_plugins' ) ) require_once ABSPATH . 'wp-admin/includes/plugin.php';
        $theme   = wp_get_theme();
        $active  = get_option( 'active_plugins', [] );
        $plugins = get_plugins();
        $plugin_list = [];
        foreach ( $plugins as $slug => $data ) {
            $plugin_list[] = [
                'slug'             => $slug,
                'name'             => $data['Name'],
                'version'          => $data['Version'],
                'active'           => in_array( $slug, $active ),
                'update_available' => false, // Updated via update check
            ];
        }
        return new WP_REST_Response([
            'success'        => true,
            'data'           => [
                'wp_version'     => get_bloginfo('version'),
                'php_version'    => phpversion(),
                'mysql_version'  => $wpdb->db_version(),
                'theme'          => [ 'name' => $theme->get('Name'), 'version' => $theme->get('Version') ],
                'theme_version'  => $theme->get('Version'),
                'plugins_active' => count( $active ),
                'plugins_total'  => count( $plugins ),
                'pages_count'    => (int) wp_count_posts('page')->publish,
                'admin_email'    => get_option('admin_email'),
                'memory_limit'   => WP_MEMORY_LIMIT,
                'memory_usage'   => size_format( memory_get_usage(true) ),
                'upload_max'     => ini_get('upload_max_filesize'),
                'debug_mode'     => defined('WP_DEBUG') && WP_DEBUG,
                'plugins'        => $plugin_list,
            ]
        ]);
    }

    public function get_error_log(): WP_REST_Response {
        $log_path = WP_CONTENT_DIR . '/debug.log';
        if ( ! file_exists($log_path) ) return new WP_REST_Response(['success' => true, 'data' => ['log' => '', 'message' => 'No debug.log']]);
        $size = filesize($log_path);
        $log  = file_get_contents( $log_path, false, null, max(0, $size - 10000), 10000 );
        return new WP_REST_Response([
            'success' => true,
            'data'    => [
                'log'      => $log,
                'size'     => $size,
                'has_fatal'=> strpos($log, 'PHP Fatal') !== false || strpos($log, 'PHP Parse error') !== false,
            ]
        ]);
    }

    public function run_cli( WP_REST_Request $req ): WP_REST_Response {
        if ( ! $this->verify_key($req) ) return new WP_REST_Response( $this->auth_error(), 401 );
        $cmd = sanitize_text_field( $req->get_param('command') ?? '' );
        if ( ! $cmd ) return new WP_REST_Response(['error' => 'command required'], 400);
        // Execute via WP-CLI if available
        $wpcli = realpath(ABSPATH . '../wp-cli.phar') ?: 'wp';
        $safe  = escapeshellarg( $cmd ); // Proper shell escaping
        exec( $wpcli . ' ' . $safe . ' --allow-root 2>&1', $output, $code );
        return new WP_REST_Response([
            'success' => $code === 0,
            'command' => $cmd,
            'output'  => implode("\n", $output),
            'code'    => $code,
        ]);
    }

    // ════════════════════════════════════════
    //  PLUGINS
    // ════════════════════════════════════════

    public function get_plugins(): WP_REST_Response {
        if ( ! function_exists('get_plugins') ) require_once ABSPATH . 'wp-admin/includes/plugin.php';
        $plugins = get_plugins();
        $active  = get_option('active_plugins', []);
        // Check for updates
        $update_data = get_site_transient('update_plugins');
        $list = [];
        foreach ( $plugins as $slug => $data ) {
            $list[] = [
                'slug'             => $slug,
                'name'             => $data['Name'],
                'version'          => $data['Version'],
                'description'      => $data['Description'],
                'active'           => in_array($slug, $active),
                'update_available' => isset($update_data->response[$slug]),
                'new_version'      => $update_data->response[$slug]->new_version ?? null,
            ];
        }
        return new WP_REST_Response(['success' => true, 'data' => ['plugins' => $list]]);
    }

    public function update_plugins( WP_REST_Request $req ): WP_REST_Response {
        require_once ABSPATH . 'wp-admin/includes/plugin.php';
        require_once ABSPATH . 'wp-admin/includes/class-wp-upgrader.php';
        require_once ABSPATH . 'wp-admin/includes/class-plugin-upgrader.php';
        $specific = $req->get_param('plugins') ?? null;
        $upgrader = new Plugin_Upgrader( new Automatic_Upgrader_Skin() );
        if ( $specific ) {
            $result = $upgrader->upgrade( $specific );
        } else {
            $update  = get_site_transient('update_plugins');
            $to_update = array_keys( $update->response ?? [] );
            $result  = $upgrader->bulk_upgrade( $to_update );
        }
        return new WP_REST_Response(['success' => !is_wp_error($result), 'message' => 'Plugins updated']);
    }

    public function toggle_plugin( WP_REST_Request $req ): WP_REST_Response {
        $slug   = $req->get_param('plugin') ?? '';
        $action = $req->get_param('action') ?? 'activate';
        if ( $action === 'activate' ) {
            $r = activate_plugin( $slug );
        } else {
            deactivate_plugins( $slug );
            $r = null;
        }
        return new WP_REST_Response(['success' => !is_wp_error($r), 'plugin' => $slug, 'action' => $action]);
    }

    // ════════════════════════════════════════
    //  USERS — مع حذف حقيقي
    // ════════════════════════════════════════

    public function list_users( WP_REST_Request $req ): WP_REST_Response {
        $role  = $req->get_param('role') ?? '';
        $args  = ['number' => 100, 'orderby' => 'registered', 'order' => 'DESC'];
        if ( $role ) $args['role'] = $role;
        $users = get_users( $args );
        $list  = array_map( function($u) {
            return [
                'id'         => $u->ID,
                'username'   => $u->user_login,
                'email'      => $u->user_email,
                'name'       => $u->display_name,
                'role'       => implode(', ', $u->roles),
                'registered' => $u->user_registered,
            ];
        }, $users);
        return new WP_REST_Response(['success' => true, 'users' => $list, 'count' => count($list)]);
    }

    public function delete_user( WP_REST_Request $req ): WP_REST_Response {
        if ( ! $this->verify_key($req) ) return new WP_REST_Response( $this->auth_error(), 401 );
        $user_id  = (int)($req->get_param('user_id') ?? 0);
        $reassign = (int)($req->get_param('reassign') ?? 1);
        if ( ! $user_id ) return new WP_REST_Response(['error' => 'user_id required'], 400);

        // Safety: don't delete current user
        if ( $user_id === get_current_user_id() ) {
            return new WP_REST_Response(['error' => 'Cannot delete current user'], 400);
        }
        // Don't delete super admins
        $user = get_userdata($user_id);
        if ( ! $user ) return new WP_REST_Response(['error' => 'User not found'], 404);
        if ( in_array('administrator', $user->roles) ) {
            return new WP_REST_Response(['error' => 'Cannot delete administrator for safety'], 403);
        }

        require_once ABSPATH . 'wp-admin/includes/user.php';
        $result = wp_delete_user( $user_id, $reassign );
        return new WP_REST_Response(['success' => $result, 'deleted_id' => $user_id]);
    }

    public function create_user( WP_REST_Request $req ): WP_REST_Response {
        if ( ! $this->verify_key($req) ) return new WP_REST_Response( $this->auth_error(), 401 );
        $params = $req->get_json_params();
        $id = wp_create_user(
            sanitize_user($params['username'] ?? ''),
            $params['password'] ?? wp_generate_password(),
            sanitize_email($params['email'] ?? '')
        );
        if ( is_wp_error($id) ) return new WP_REST_Response(['success' => false, 'error' => $id->get_error_message()], 400);
        $user = get_userdata($id);
        $user->set_role($params['role'] ?? 'subscriber');
        return new WP_REST_Response(['success' => true, 'user_id' => $id, 'username' => $params['username']]);
    }

    public function update_user_role( WP_REST_Request $req ): WP_REST_Response {
        if ( ! $this->verify_key($req) ) return new WP_REST_Response( $this->auth_error(), 401 );
        $params  = $req->get_json_params();
        $user_id = (int)($params['user_id'] ?? 0);
        $role    = $params['role'] ?? '';
        if ( ! $user_id || ! $role ) return new WP_REST_Response(['error' => 'user_id and role required'], 400);
        $user = get_userdata($user_id);
        if ( ! $user ) return new WP_REST_Response(['error' => 'User not found'], 404);
        $user->set_role($role);
        return new WP_REST_Response(['success' => true, 'user_id' => $user_id, 'new_role' => $role]);
    }

    // ════════════════════════════════════════
    //  ELEMENTOR
    // ════════════════════════════════════════

    public function get_elementor( WP_REST_Request $req ): WP_REST_Response {
        $page_id = (int)($req->get_param('page_id') ?? 0);
        if ( ! $page_id ) {
            $pages = get_posts(['post_type' => 'page', 'posts_per_page' => 5, 'post_status' => 'publish']);
            return new WP_REST_Response(['success' => true, 'pages' => array_map(fn($p) => ['id' => $p->ID, 'title' => $p->post_title], $pages)]);
        }
        $data = get_post_meta($page_id, '_elementor_data', true);
        return new WP_REST_Response(['success' => true, 'page_id' => $page_id, 'data' => $data ? json_decode($data, true) : []]);
    }

    public function set_elementor( WP_REST_Request $req ): WP_REST_Response {
        if ( ! $this->verify_key($req) ) return new WP_REST_Response( $this->auth_error(), 401 );
        $params  = $req->get_json_params();
        $page_id = (int)($params['page_id'] ?? 0);
        $data    = $params['data'] ?? [];
        if ( ! $page_id ) return new WP_REST_Response(['error' => 'page_id required'], 400);
        update_post_meta($page_id, '_elementor_data', wp_json_encode($data));
        return new WP_REST_Response(['success' => true, 'page_id' => $page_id]);
    }

    // ════════════════════════════════════════
    //  MASTERSTUDY LMS
    // ════════════════════════════════════════

    public function ms_get_courses(): WP_REST_Response {
        $courses = get_posts(['post_type' => 'stm-courses', 'posts_per_page' => -1, 'post_status' => 'any']);
        $list = array_map(function($c) {
            $lessons = get_posts(['post_type' => 'stm-lessons', 'post_parent' => $c->ID, 'posts_per_page' => -1]);
            return [
                'id'       => $c->ID,
                'title'    => $c->post_title,
                'status'   => $c->post_status,
                'price'    => get_post_meta($c->ID, 'price', true) ?: 0,
                'level'    => get_post_meta($c->ID, 'level', true) ?: 'beginner',
                'duration' => get_post_meta($c->ID, 'duration', true) ?: '',
                'lessons'  => count($lessons),
                'students' => (int)get_post_meta($c->ID, 'stm_students_count', true),
            ];
        }, $courses);
        return new WP_REST_Response(['success' => true, 'courses' => $list, 'count' => count($list)]);
    }

    public function ms_get_course( WP_REST_Request $req ): WP_REST_Response {
        $id = (int)$req->get_param('id');
        $c  = get_post($id);
        if ( ! $c || $c->post_type !== 'stm-courses' ) return new WP_REST_Response(['error' => 'Not found'], 404);
        $lessons = get_posts(['post_type' => 'stm-lessons', 'post_parent' => $id, 'posts_per_page' => -1, 'orderby' => 'menu_order', 'order' => 'ASC']);
        $quizzes = get_posts(['post_type' => 'stm-quizzes', 'post_parent' => $id, 'posts_per_page' => -1]);
        return new WP_REST_Response(['success' => true, 'data' => [
            'id'          => $id,
            'title'       => $c->post_title,
            'description' => $c->post_content,
            'status'      => $c->post_status,
            'price'       => get_post_meta($id, 'price', true),
            'level'       => get_post_meta($id, 'level', true),
            'duration'    => get_post_meta($id, 'duration', true),
            'lessons'     => array_map(fn($l) => ['id' => $l->ID, 'title' => $l->post_title, 'content' => $l->post_content], $lessons),
            'quizzes'     => array_map(fn($q) => ['id' => $q->ID, 'title' => $q->post_title], $quizzes),
        ]]);
    }

    public function ms_create_course( WP_REST_Request $req ): WP_REST_Response {
        if ( ! $this->verify_key($req) ) return new WP_REST_Response( $this->auth_error(), 401 );
        $p  = $req->get_json_params();
        $id = wp_insert_post([
            'post_title'   => sanitize_text_field($p['title'] ?? 'New Course'),
            'post_content' => wp_kses_post($p['description'] ?? ''),
            'post_status'  => $p['status'] ?? 'draft',
            'post_type'    => 'stm-courses',
        ]);
        if ( is_wp_error($id) ) return new WP_REST_Response(['success' => false, 'error' => $id->get_error_message()], 400);
        update_post_meta($id, 'price',    floatval($p['price']    ?? 0));
        update_post_meta($id, 'level',    sanitize_text_field($p['level']    ?? 'beginner'));
        update_post_meta($id, 'duration', sanitize_text_field($p['duration'] ?? ''));
        if (!empty($p['requirements'])) update_post_meta($id, 'requirements', array_map('sanitize_text_field', $p['requirements']));
        return new WP_REST_Response(['success' => true, 'course_id' => $id, 'title' => get_the_title($id)]);
    }

    public function ms_add_lesson( WP_REST_Request $req ): WP_REST_Response {
        if ( ! $this->verify_key($req) ) return new WP_REST_Response( $this->auth_error(), 401 );
        $course_id = (int)$req->get_param('id');
        $p = $req->get_json_params();
        $id = wp_insert_post([
            'post_title'   => sanitize_text_field($p['title'] ?? 'Lesson'),
            'post_content' => wp_kses_post($p['content'] ?? ''),
            'post_status'  => 'publish',
            'post_type'    => 'stm-lessons',
            'post_parent'  => $course_id,
            'menu_order'   => (int)($p['order'] ?? 0),
        ]);
        if ( is_wp_error($id) ) return new WP_REST_Response(['success' => false, 'error' => $id->get_error_message()], 400);
        if ( !empty($p['video_url']) ) update_post_meta($id, 'video_url', esc_url($p['video_url']));
        if ( !empty($p['duration'])  ) update_post_meta($id, 'duration',  sanitize_text_field($p['duration']));
        return new WP_REST_Response(['success' => true, 'lesson_id' => $id]);
    }

    public function ms_add_quiz( WP_REST_Request $req ): WP_REST_Response {
        if ( ! $this->verify_key($req) ) return new WP_REST_Response( $this->auth_error(), 401 );
        $course_id = (int)$req->get_param('id');
        $p = $req->get_json_params();
        $id = wp_insert_post([
            'post_title'  => sanitize_text_field($p['title'] ?? 'Quiz'),
            'post_status' => 'publish',
            'post_type'   => 'stm-quizzes',
            'post_parent' => $course_id,
        ]);
        if ( is_wp_error($id) ) return new WP_REST_Response(['success' => false, 'error' => $id->get_error_message()], 400);
        if ( !empty($p['questions']) ) update_post_meta($id, 'questions', $p['questions']);
        return new WP_REST_Response(['success' => true, 'quiz_id' => $id]);
    }

    public function ms_get_students( WP_REST_Request $req ): WP_REST_Response {
        global $wpdb;
        $course_id = (int)$req->get_param('id');
        $key = "stm_lms_course_{$course_id}_progress";
        $results = $wpdb->get_results($wpdb->prepare(
            "SELECT u.ID, u.user_login, u.user_email, u.display_name, um.meta_value as progress
             FROM {$wpdb->users} u
             JOIN {$wpdb->usermeta} um ON u.ID = um.user_id
             WHERE um.meta_key = %s", $key
        ));
        return new WP_REST_Response(['success' => true, 'students' => $results, 'count' => count($results)]);
    }

    public function ms_all_students(): WP_REST_Response {
        global $wpdb;
        $results = $wpdb->get_results(
            "SELECT u.ID, u.user_login, u.user_email, COUNT(um.meta_key) as enrolled_courses
             FROM {$wpdb->users} u
             JOIN {$wpdb->usermeta} um ON u.ID = um.user_id
             WHERE um.meta_key LIKE 'stm_lms_course_%_progress'
             GROUP BY u.ID ORDER BY enrolled_courses DESC LIMIT 50"
        );
        return new WP_REST_Response(['success' => true, 'students' => $results, 'count' => count($results)]);
    }

    public function ms_enroll( WP_REST_Request $req ): WP_REST_Response {
        if ( ! $this->verify_key($req) ) return new WP_REST_Response( $this->auth_error(), 401 );
        $p         = $req->get_json_params();
        $user_id   = (int)($p['user_id']   ?? 0);
        $course_id = (int)($p['course_id'] ?? 0);
        if (!$user_id || !$course_id) return new WP_REST_Response(['error' => 'Missing params'], 400);
        update_user_meta($user_id, "stm_lms_course_{$course_id}_progress", 0);
        update_user_meta($user_id, "stm_lms_course_{$course_id}_enrolled",  time());
        return new WP_REST_Response(['success' => true, 'user_id' => $user_id, 'course_id' => $course_id]);
    }

    public function ms_progress( WP_REST_Request $req ): WP_REST_Response {
        $user_id   = (int)$req->get_param('user');
        $course_id = (int)$req->get_param('course');
        $progress  = get_user_meta($user_id, "stm_lms_course_{$course_id}_progress", true);
        $enrolled  = get_user_meta($user_id, "stm_lms_course_{$course_id}_enrolled",  true);
        return new WP_REST_Response([
            'user_id'   => $user_id,
            'course_id' => $course_id,
            'progress'  => (int)$progress,
            'enrolled'  => $enrolled ? date('Y-m-d H:i', $enrolled) : null,
        ]);
    }
}
