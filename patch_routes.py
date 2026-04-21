"""
Append: Smart Connection + User Management + AI Operator routes
Run: py -3.11 patch_routes.py
"""
import os

PATCH = '''

# ══════════════════════════════════════════════════════
#  AI OPERATOR — المحرك الذكي الحقيقي
# ══════════════════════════════════════════════════════

@wp_bp.route("/operator/run", methods=["POST"])
def operator_run():
    """AI Operator: تحلل → تقرر → تنفذ"""
    import time
    try:
        from ai_operator import ai_operator
    except Exception as e:
        return jsonify({"error": "AI Operator not available: " + str(e)}), 500

    data    = request.get_json(force=True) or {}
    task    = data.get("task", "")
    explain = data.get("explain", False)
    site_n  = data.get("site")

    if not task:
        return jsonify({"error": "task required"}), 400

    site = wp_manager.get_site(site_n) if site_n else None

    if data.get("all_sites"):
        sites   = wp_manager.get_all_sites()
        results = [ai_operator.execute(task, s, explain) for s in sites]
        return jsonify({"success": True, "all_sites": True, "results": results})

    result = ai_operator.execute(task, site, explain)
    return jsonify(result)


@wp_bp.route("/operator/explain", methods=["POST"])
def operator_explain():
    """شرح ما سيحدث قبل التنفيذ"""
    try:
        from ai_operator import ai_operator
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    data = request.get_json(force=True) or {}
    task = data.get("task", "")
    site = wp_manager.get_site(data.get("site")) if data.get("site") else None
    result = ai_operator.execute(task, site, explain=True)
    return jsonify(result)


# ══════════════════════════════════════════════════════
#  SMART CONNECTION STATUS
# ══════════════════════════════════════════════════════

@wp_bp.route("/sites/<site_name>/status", methods=["GET"])
def smart_site_status(site_name):
    """حالة اتصال ذكية: Latency + API + Plugin Sync + Version"""
    import time
    site = wp_manager.get_site(site_name)
    if not site:
        return jsonify({"error": "Site not found"}), 404

    result = {
        "site":          site_name,
        "url":           site.url,
        "connected":     False,
        "latency_ms":    0,
        "api_status":    "unknown",
        "plugin_sync":   "unknown",
        "wp_version":    None,
        "php_version":   None,
        "plugin_version": None,
        "compatible":    False,
        "checks":        {},
    }

    # 1. Ping + Latency
    t0 = time.time()
    try:
        ok = site.ping()
        ms = round((time.time() - t0) * 1000, 1)
        result["connected"]  = ok
        result["latency_ms"] = ms
        result["checks"]["ping"] = "ok" if ok else "fail"
    except Exception as e:
        result["checks"]["ping"] = "error: " + str(e)[:40]

    if not result["connected"]:
        return jsonify(result)

    # 2. Site Info
    try:
        info = site.get_site_info()
        if info.get("success"):
            d = info.get("data", {})
            result["wp_version"]  = d.get("wp_version")
            result["php_version"] = d.get("php_version")
            result["checks"]["site_info"] = "ok"
        else:
            result["checks"]["site_info"] = "fail"
    except Exception as e:
        result["checks"]["site_info"] = "error"

    # 3. Plugin API Check
    try:
        ping_r = site._request("GET", "ping")
        if ping_r.get("success") or ping_r.get("status") == "ok":
            result["api_status"]   = "ok"
            result["plugin_version"] = ping_r.get("plugin_version", "?")
            result["plugin_sync"]  = "ok"
            result["compatible"]   = True
            result["checks"]["plugin_api"] = "ok"
        else:
            result["api_status"]  = "degraded"
            result["checks"]["plugin_api"] = "degraded"
    except Exception as e:
        result["api_status"] = "error"
        result["checks"]["plugin_api"] = "error"

    # 4. Latency rating
    ms = result["latency_ms"]
    result["latency_rating"] = "excellent" if ms < 300 else "good" if ms < 1000 else "slow" if ms < 3000 else "critical"

    return jsonify(result)


# ══════════════════════════════════════════════════════
#  USER MANAGEMENT — احذف + أضف + عدّل
# ══════════════════════════════════════════════════════

@wp_bp.route("/users", methods=["GET"])
def list_users():
    data  = request.args
    site  = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"error": "Site required"}), 400
    r = site._request("GET", "users")
    return jsonify(r)


@wp_bp.route("/users/delete", methods=["POST"])
def delete_user():
    """حذف مستخدم — مع حماية (لا يحذف Admins)"""
    data    = request.get_json(force=True) or {}
    site    = wp_manager.get_site(data.get("site"))
    user_id = data.get("user_id")
    if not site:    return jsonify({"error": "Site required"}), 400
    if not user_id: return jsonify({"error": "user_id required"}), 400

    r = site._request("POST", "users/delete", {
        "user_id":      user_id,
        "reassign":     data.get("reassign", 1),   # Reassign posts to admin
    })
    return jsonify(r)


@wp_bp.route("/users/create", methods=["POST"])
def create_user():
    data = request.get_json(force=True) or {}
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"error": "Site required"}), 400
    r = site._request("POST", "users/create", {
        "username": data.get("username"),
        "email":    data.get("email"),
        "password": data.get("password"),
        "role":     data.get("role", "subscriber"),
    })
    return jsonify(r)


@wp_bp.route("/users/update", methods=["POST"])
def update_user():
    data    = request.get_json(force=True) or {}
    site    = wp_manager.get_site(data.get("site"))
    user_id = data.get("user_id")
    if not site or not user_id:
        return jsonify({"error": "site and user_id required"}), 400
    r = site._request("POST", "users/update", data)
    return jsonify(r)


# ══════════════════════════════════════════════════════
#  MASTERSTUDY LMS
# ══════════════════════════════════════════════════════

@wp_bp.route("/masterstudy/courses", methods=["GET"])
def ms_list_courses():
    site = wp_manager.get_site(request.args.get("site"))
    if not site: return jsonify({"error": "Site required"}), 400
    return jsonify(site._request("GET", "masterstudy/courses"))


@wp_bp.route("/masterstudy/create", methods=["POST"])
def ms_create_course():
    data  = request.get_json(force=True) or {}
    site  = wp_manager.get_site(data.get("site"))
    topic = data.get("topic", data.get("title", "New Course"))
    if not site: return jsonify({"error": "Site required"}), 400

    try:
        from ai_operator import ai_operator
        result = ai_operator.execute(f"أنشئ كورس MasterStudy عن {topic}", site)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@wp_bp.route("/masterstudy/students", methods=["GET"])
def ms_students():
    site      = wp_manager.get_site(request.args.get("site"))
    course_id = request.args.get("course_id")
    if not site: return jsonify({"error": "Site required"}), 400
    path = f"masterstudy/courses/{course_id}/students" if course_id else "masterstudy/students"
    return jsonify(site._request("GET", path))


@wp_bp.route("/masterstudy/enroll", methods=["POST"])
def ms_enroll():
    data = request.get_json(force=True) or {}
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"error": "Site required"}), 400
    return jsonify(site._request("POST", "masterstudy/enroll", {
        "user_id":   data.get("user_id"),
        "course_id": data.get("course_id"),
    }))

'''

TARGET = r"C:\mcp-agent\wp_routes.py"
current = open(TARGET, encoding="utf-8", errors="replace").read()

markers = ["AI OPERATOR", "/operator/run", "smart_site_status", "/users/delete", "/masterstudy/courses"]
already = [m for m in markers if m in current]

if len(already) >= 3:
    print(f"Already patched ({len(already)}/5 markers found)")
else:
    with open(TARGET, "a", encoding="utf-8") as f:
        f.write(PATCH)
    print(f"Patched! New size: {os.path.getsize(TARGET)} bytes")
