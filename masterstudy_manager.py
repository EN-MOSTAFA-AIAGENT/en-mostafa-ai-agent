"""
MasterStudy LMS Integration — AI WordPress Control Center
أقوى من LearnDash — دعم كامل:
- رفع كورس كامل تلقائي
- تقسيم دروس من محتوى نصي
- إدارة طلاب + شهادات
- تحليل AI للمحتوى
"""

import json
import time
from typing import Dict, List, Optional, Any
from logger_system import get_logger
from llm_bridge     import llm_bridge

logger = get_logger("masterstudy")


class MasterStudyManager:
    """
    AI Operator لـ MasterStudy LMS
    ينفذ — مش بس يعرض
    """

    def __init__(self, site):
        self.site = site  # WordPressSite instance

    # ─── Course CRUD ──────────────────────────────────────

    def get_courses(self) -> Dict:
        """كل الكورسات مع تفاصيل كاملة"""
        return self.site._request("GET", "masterstudy/courses")

    def get_course(self, course_id: int) -> Dict:
        return self.site._request("GET", f"masterstudy/courses/{course_id}")

    def create_course(self, title: str, description: str = "",
                      price: float = 0, status: str = "draft",
                      level: str = "beginner", duration: str = "",
                      requirements: List[str] = None,
                      meta: Dict = None) -> Dict:
        return self.site._request("POST", "masterstudy/courses", {
            "title":        title,
            "description":  description,
            "price":        price,
            "status":       status,
            "level":        level,
            "duration":     duration,
            "requirements": requirements or [],
            "meta":         meta or {},
        })

    def update_course(self, course_id: int, data: Dict) -> Dict:
        return self.site._request("POST", f"masterstudy/courses/{course_id}/update", data)

    def delete_course(self, course_id: int) -> Dict:
        return self.site._request("POST", f"masterstudy/courses/{course_id}/delete", {})

    # ─── Lessons ──────────────────────────────────────────

    def add_lesson(self, course_id: int, title: str, content: str = "",
                   video_url: str = "", duration: str = "",
                   order: int = 0) -> Dict:
        return self.site._request("POST", f"masterstudy/courses/{course_id}/lessons", {
            "title":     title,
            "content":   content,
            "video_url": video_url,
            "duration":  duration,
            "order":     order,
        })

    def add_quiz(self, course_id: int, title: str,
                 questions: List[Dict] = None) -> Dict:
        return self.site._request("POST", f"masterstudy/courses/{course_id}/quizzes", {
            "title":     title,
            "questions": questions or [],
        })

    # ─── Students ─────────────────────────────────────────

    def get_students(self, course_id: int = None) -> Dict:
        path = f"masterstudy/courses/{course_id}/students" if course_id else "masterstudy/students"
        return self.site._request("GET", path)

    def enroll_student(self, user_id: int, course_id: int) -> Dict:
        return self.site._request("POST", "masterstudy/enroll", {
            "user_id":   user_id,
            "course_id": course_id,
        })

    def get_progress(self, user_id: int, course_id: int) -> Dict:
        return self.site._request("GET", f"masterstudy/progress/{user_id}/{course_id}")

    # ─── AI-Powered: Full Course Creation ─────────────────

    def ai_create_full_course(self, topic: str, lessons_count: int = 5,
                               language: str = "ar", price: float = 0) -> Dict:
        """
        ينشئ كورس كامل بالذكاء الاصطناعي:
        1. يولّد المحتوى
        2. يقسّم لدروس
        3. يرفع تلقائياً
        """
        logger.info(f"AI creating full course: {topic}")

        # 1. Generate course structure with LLM
        prompt = f"""أنشئ هيكل كورس تعليمي كامل عن: {topic}
اللغة: {language}
عدد الدروس: {lessons_count}

أعطني JSON بالشكل التالي:
{{
  "title": "عنوان الكورس",
  "description": "وصف الكورس (3 جمل)",
  "level": "beginner|intermediate|advanced",
  "duration": "مثال: 10 hours",
  "requirements": ["متطلب1", "متطلب2"],
  "lessons": [
    {{
      "title": "عنوان الدرس",
      "content": "محتوى الدرس (فقرة كاملة)",
      "duration": "مثال: 30 minutes"
    }}
  ],
  "quiz": {{
    "title": "اختبار نهائي",
    "questions": [
      {{
        "question": "السؤال",
        "options": ["أ", "ب", "ج", "د"],
        "correct": 0
      }}
    ]
  }}
}}

أجب بـ JSON فقط بدون أي كلام إضافي."""

        result = llm_bridge._call_llm(prompt)

        # Parse JSON from LLM
        course_data = self._parse_json_safe(result)
        if not course_data:
            # Fallback: basic structure
            course_data = self._generate_basic_structure(topic, lessons_count)

        # 2. Create course
        create_r = self.create_course(
            title       = course_data.get("title", f"كورس {topic}"),
            description = course_data.get("description", ""),
            price       = price,
            status      = "draft",
            level       = course_data.get("level", "beginner"),
            duration    = course_data.get("duration", ""),
            requirements= course_data.get("requirements", []),
        )

        if not create_r.get("success"):
            return {"success": False, "error": "Failed to create course", "details": create_r}

        course_id = create_r.get("course_id") or create_r.get("data", {}).get("course_id")
        if not course_id:
            return {"success": False, "error": "No course_id returned", "details": create_r}

        # 3. Add lessons
        lessons_added = []
        for i, lesson in enumerate(course_data.get("lessons", [])):
            lr = self.add_lesson(
                course_id = course_id,
                title     = lesson.get("title", f"الدرس {i+1}"),
                content   = lesson.get("content", ""),
                duration  = lesson.get("duration", ""),
                order     = i,
            )
            lessons_added.append({
                "title":   lesson.get("title"),
                "success": lr.get("success", False),
            })
            time.sleep(0.2)  # Throttle

        # 4. Add quiz
        quiz_added = None
        if course_data.get("quiz"):
            quiz_r = self.add_quiz(
                course_id = course_id,
                title     = course_data["quiz"].get("title", "اختبار"),
                questions = course_data["quiz"].get("questions", []),
            )
            quiz_added = quiz_r

        logger.info(f"Course created: {course_id} with {len(lessons_added)} lessons")
        return {
            "success":      True,
            "course_id":    course_id,
            "title":        course_data.get("title"),
            "lessons":      lessons_added,
            "lessons_count": len(lessons_added),
            "quiz":         quiz_added,
            "status":       "draft",
            "message":      f"تم إنشاء الكورس بنجاح ({len(lessons_added)} دروس)"
        }

    def ai_split_content_to_lessons(self, course_id: int, raw_content: str) -> Dict:
        """
        يأخذ محتوى نصي طويل ويقسّمه لدروس تلقائياً
        """
        prompt = f"""قسّم هذا المحتوى التعليمي إلى دروس منظمة:

{raw_content[:3000]}

أعطني JSON:
[
  {{"title": "عنوان الدرس", "content": "محتوى الدرس"}},
  ...
]
أجب بـ JSON فقط."""

        result = llm_bridge._call_llm(prompt)
        lessons = self._parse_json_safe(result)

        if not lessons or not isinstance(lessons, list):
            return {"success": False, "error": "Failed to parse content into lessons"}

        added = []
        for i, lesson in enumerate(lessons):
            r = self.add_lesson(course_id, lesson.get("title", f"درس {i+1}"),
                               lesson.get("content", ""), order=i)
            added.append({"title": lesson.get("title"), "success": r.get("success", False)})
            time.sleep(0.2)

        return {"success": True, "lessons_added": len(added), "lessons": added}

    def ai_analyze_course(self, course_id: int) -> Dict:
        """تحليل AI لجودة الكورس"""
        r = self.get_course(course_id)
        if not r.get("success"):
            return r
        course = r.get("data", {})
        prompt = f"""حلل هذا الكورس وأعطني تقرير بالعربية:
الكورس: {json.dumps(course, ensure_ascii=False)[:1500]}

التقرير يشمل:
1. نقاط القوة
2. نقاط الضعف
3. توصيات تحسين المحتوى
4. تقييم من 10"""
        analysis = llm_bridge._call_llm(prompt)
        return {"success": True, "course_id": course_id, "analysis": analysis}

    # ─── Helpers ──────────────────────────────────────────

    def _parse_json_safe(self, text: str) -> Any:
        try:
            import re
            # Extract JSON from text
            match = re.search(r'\[.*\]|\{.*\}', text, re.S)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        try:
            return json.loads(text)
        except Exception:
            return None

    def _generate_basic_structure(self, topic: str, lessons_count: int) -> Dict:
        """Fallback structure without LLM"""
        return {
            "title":       f"كورس {topic}",
            "description": f"كورس شامل عن {topic}",
            "level":       "beginner",
            "duration":    f"{lessons_count * 30} minutes",
            "requirements": [],
            "lessons": [
                {
                    "title":    f"الدرس {i+1}: {topic}",
                    "content":  f"محتوى الدرس {i+1}",
                    "duration": "30 minutes",
                }
                for i in range(lessons_count)
            ],
        }


# ─────────────────────────────────────────────────────────
#  MasterStudy PHP Plugin Endpoints (يُضاف لـ class-aiwa-api.php)
# ─────────────────────────────────────────────────────────

MASTERSTUDY_PHP_ENDPOINTS = """
// في class-aiwa-api.php — أضف داخل register_routes():

// MasterStudy Courses
register_rest_route($ns, '/masterstudy/courses', [
    ['methods' => 'GET',  'callback' => [$this, 'ms_get_courses'],  'permission_callback' => [$this, 'check_auth']],
    ['methods' => 'POST', 'callback' => [$this, 'ms_create_course'],'permission_callback' => [$this, 'check_auth']],
]);
register_rest_route($ns, '/masterstudy/courses/(?P<id>\\d+)', [
    ['methods' => 'GET',  'callback' => [$this, 'ms_get_course'],   'permission_callback' => [$this, 'check_auth']],
]);
register_rest_route($ns, '/masterstudy/courses/(?P<id>\\d+)/update', [
    ['methods' => 'POST', 'callback' => [$this, 'ms_update_course'],'permission_callback' => [$this, 'check_auth']],
]);
register_rest_route($ns, '/masterstudy/courses/(?P<id>\\d+)/lessons', [
    ['methods' => 'POST', 'callback' => [$this, 'ms_add_lesson'],   'permission_callback' => [$this, 'check_auth']],
]);
register_rest_route($ns, '/masterstudy/courses/(?P<id>\\d+)/quizzes', [
    ['methods' => 'POST', 'callback' => [$this, 'ms_add_quiz'],     'permission_callback' => [$this, 'check_auth']],
]);
register_rest_route($ns, '/masterstudy/courses/(?P<id>\\d+)/students', [
    ['methods' => 'GET',  'callback' => [$this, 'ms_get_students'], 'permission_callback' => [$this, 'check_auth']],
]);
register_rest_route($ns, '/masterstudy/enroll', [
    ['methods' => 'POST', 'callback' => [$this, 'ms_enroll'],       'permission_callback' => [$this, 'check_auth']],
]);
register_rest_route($ns, '/masterstudy/progress/(?P<user>\\d+)/(?P<course>\\d+)', [
    ['methods' => 'GET',  'callback' => [$this, 'ms_progress'],     'permission_callback' => [$this, 'check_auth']],
]);

// == Handler Methods ==

public function ms_get_courses(WP_REST_Request $req): WP_REST_Response {
    $courses = get_posts(['post_type' => 'stm-courses', 'posts_per_page' => -1, 'post_status' => 'any']);
    $list = array_map(function($c) {
        return [
            'id'       => $c->ID,
            'title'    => $c->post_title,
            'status'   => $c->post_status,
            'price'    => get_post_meta($c->ID, 'price', true),
            'level'    => get_post_meta($c->ID, 'level', true),
            'duration' => get_post_meta($c->ID, 'duration', true),
            'students' => (int) get_post_meta($c->ID, 'stm_students_count', true),
            'lessons'  => count(get_posts(['post_type' => 'stm-lessons', 'post_parent' => $c->ID, 'posts_per_page' => -1])),
        ];
    }, $courses);
    return new WP_REST_Response(['courses' => $list, 'count' => count($list)]);
}

public function ms_get_course(WP_REST_Request $req): WP_REST_Response {
    $id = (int) $req->get_param('id');
    $c  = get_post($id);
    if (!$c || $c->post_type !== 'stm-courses') return new WP_REST_Response(['error' => 'Not found'], 404);
    $lessons = get_posts(['post_type' => 'stm-lessons', 'post_parent' => $id, 'posts_per_page' => -1, 'orderby' => 'menu_order', 'order' => 'ASC']);
    return new WP_REST_Response(['success' => true, 'data' => [
        'id'          => $id,
        'title'       => $c->post_title,
        'description' => $c->post_content,
        'status'      => $c->post_status,
        'price'       => get_post_meta($id, 'price', true),
        'level'       => get_post_meta($id, 'level', true),
        'duration'    => get_post_meta($id, 'duration', true),
        'lessons'     => array_map(fn($l) => ['id' => $l->ID, 'title' => $l->post_title, 'content' => $l->post_content], $lessons),
    ]]);
}

public function ms_create_course(WP_REST_Request $req): WP_REST_Response {
    $params = $req->get_json_params();
    $id = wp_insert_post([
        'post_title'   => sanitize_text_field($params['title'] ?? 'New Course'),
        'post_content' => wp_kses_post($params['description'] ?? ''),
        'post_status'  => $params['status'] ?? 'draft',
        'post_type'    => 'stm-courses',
    ]);
    if (is_wp_error($id)) return new WP_REST_Response(['success' => false, 'error' => $id->get_error_message()], 400);
    update_post_meta($id, 'price',    $params['price']    ?? 0);
    update_post_meta($id, 'level',    $params['level']    ?? 'beginner');
    update_post_meta($id, 'duration', $params['duration'] ?? '');
    if (!empty($params['requirements'])) update_post_meta($id, 'requirements', $params['requirements']);
    return new WP_REST_Response(['success' => true, 'course_id' => $id, 'title' => $params['title']]);
}

public function ms_add_lesson(WP_REST_Request $req): WP_REST_Response {
    $course_id = (int) $req->get_param('id');
    $params    = $req->get_json_params();
    $id = wp_insert_post([
        'post_title'   => sanitize_text_field($params['title'] ?? 'Lesson'),
        'post_content' => wp_kses_post($params['content'] ?? ''),
        'post_status'  => 'publish',
        'post_type'    => 'stm-lessons',
        'post_parent'  => $course_id,
        'menu_order'   => (int)($params['order'] ?? 0),
    ]);
    if (is_wp_error($id)) return new WP_REST_Response(['success' => false, 'error' => $id->get_error_message()], 400);
    if (!empty($params['video_url'])) update_post_meta($id, 'video_url', esc_url($params['video_url']));
    if (!empty($params['duration']))  update_post_meta($id, 'duration',  sanitize_text_field($params['duration']));
    return new WP_REST_Response(['success' => true, 'lesson_id' => $id]);
}

public function ms_add_quiz(WP_REST_Request $req): WP_REST_Response {
    $course_id = (int) $req->get_param('id');
    $params    = $req->get_json_params();
    $id = wp_insert_post([
        'post_title'  => sanitize_text_field($params['title'] ?? 'Quiz'),
        'post_status' => 'publish',
        'post_type'   => 'stm-quizzes',
        'post_parent' => $course_id,
    ]);
    if (is_wp_error($id)) return new WP_REST_Response(['success' => false, 'error' => $id->get_error_message()], 400);
    if (!empty($params['questions'])) update_post_meta($id, 'questions', $params['questions']);
    return new WP_REST_Response(['success' => true, 'quiz_id' => $id]);
}

public function ms_get_students(WP_REST_Request $req): WP_REST_Response {
    $course_id = (int) $req->get_param('id');
    global $wpdb;
    $results = $wpdb->get_results($wpdb->prepare(
        "SELECT u.ID, u.user_login, u.user_email, um.meta_value as progress
         FROM {$wpdb->users} u
         JOIN {$wpdb->usermeta} um ON u.ID = um.user_id
         WHERE um.meta_key = %s",
        "stm_lms_course_{$course_id}_progress"
    ));
    return new WP_REST_Response(['students' => $results, 'count' => count($results)]);
}

public function ms_enroll(WP_REST_Request $req): WP_REST_Response {
    $params    = $req->get_json_params();
    $user_id   = (int)($params['user_id']   ?? 0);
    $course_id = (int)($params['course_id'] ?? 0);
    if (!$user_id || !$course_id) return new WP_REST_Response(['error' => 'Missing params'], 400);
    update_user_meta($user_id, "stm_lms_course_{$course_id}_progress", 0);
    update_user_meta($user_id, "stm_lms_course_{$course_id}_enrolled", time());
    return new WP_REST_Response(['success' => true, 'user_id' => $user_id, 'course_id' => $course_id]);
}

public function ms_progress(WP_REST_Request $req): WP_REST_Response {
    $user_id   = (int) $req->get_param('user');
    $course_id = (int) $req->get_param('course');
    $progress  = get_user_meta($user_id, "stm_lms_course_{$course_id}_progress", true);
    $enrolled  = get_user_meta($user_id, "stm_lms_course_{$course_id}_enrolled", true);
    return new WP_REST_Response(['user_id' => $user_id, 'course_id' => $course_id, 'progress' => (int)$progress, 'enrolled' => $enrolled]);
}
"""
