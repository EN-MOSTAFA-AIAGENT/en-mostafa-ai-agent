import os
from flask import Blueprint, request, jsonify
from wp_manager import wp_manager
from logger_system import get_logger

# استيراد المحركات الذكية
try:
    from agent_brain import agent_brain
    from memory_engine import memory_engine
    from pattern_engine import pattern_engine
    from strategy_engine import strategy_engine
    from decision_engine import decision_engine
    SMART_SYSTEM_READY = True
except ImportError:
    SMART_SYSTEM_READY = False

logger = get_logger("wp_routes")
wp_bp = Blueprint("wp", __name__, url_prefix="/wp")

@wp_bp.route("/sites", methods=["GET"])
@wp_bp.route("/sites-status", methods=["GET"])
def get_sites_status():
    sites = wp_manager.get_all_sites()
    return jsonify({
        "success": True,
        "sites": [
            {
                "name": s.name,
                "url": s.url,
                "connected": s.connected,
                "last_ping": s.last_ping
            } for s in sites
        ]
    })

@wp_bp.route("/add-site", methods=["POST"])
def add_site():
    data = request.json
    name = data.get("name")
    url = data.get("url")
    key = data.get("api_key")
    if not name or not url or not key:
        return jsonify({"success": False, "error": "Missing parameters"}), 400
    
    # استخدام StrategyEngine للتأكد من صحة الموقع قبل الإضافة (إذا كان متاحاً)
    if SMART_SYSTEM_READY:
        strategy = strategy_engine.get_connection_strategy(url)
        logger.info(f"Using strategy: {strategy} for site {name}")

    site = wp_manager.add_site(name, url, key)
    connected = site.ping()

    # Persist to DB so site survives restart
    from sites_store import sites_store
    sites_store.save(name, url, key)

    if SMART_SYSTEM_READY:
        memory_engine.store_event("site_added", {"name": name, "connected": connected})

    return jsonify({"success": True, "name": name, "connected": connected})

@wp_bp.route("/site-info", methods=["POST"])
def site_info():
    data = request.json
    site_name = data.get("site")
    site = wp_manager.get_site(site_name)
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404

    r = site.get_site_info()
    if not r.get("success"):
        return jsonify({"success": False, "error": r.get("error", "Connection failed"), "connected": False})

    # Unwrap double-wrapping: _request wraps WP response in data{}
    # WP returns {success, data:{wp_version, plugins_active, ...}}
    # _request returns {success, data:{success, data:{wp_version,...}}, status}
    raw = r.get("data", {})
    if isinstance(raw, dict) and "data" in raw and isinstance(raw["data"], dict):
        d = raw["data"]
    else:
        d = raw
    d["connected"] = site.connected

    # pages_count & admin_email — use WP REST API directly if plugin doesn't provide them
    if not d.get("pages_count") or not d.get("admin_email"):
        try:
            import requests as _req, urllib3 as _u3
            _u3.disable_warnings(_u3.exceptions.InsecureRequestWarning)
            _h = {"X-AI-Agent-Key": site.api_key}
            _base = site.url.rstrip("/")
            if not d.get("pages_count"):
                _pr = _req.get(f"{_base}/wp-json/wp/v2/pages", params={"per_page": 1, "status": "publish"}, headers=_h, timeout=8, verify=False)
                d["pages_count"] = int(_pr.headers.get("X-WP-Total", 0))
            if not d.get("admin_email"):
                _sr = _req.get(f"{_base}/wp-json/wp/v2/settings", headers={**_h, "Authorization": f"Bearer {site.api_key}"}, timeout=8, verify=False)
                if _sr.status_code == 200:
                    d["admin_email"] = _sr.json().get("email", "")
        except Exception:
            pass
    if "pages_count" not in d:
        d["pages_count"] = 0

    # updates_count — reuse already-fixed plugins route logic
    try:
        plugins_r = site.get_plugins()
        pr2 = plugins_r.get("data", {})
        if isinstance(pr2, dict) and "data" in pr2:
            pr2 = pr2["data"]
        plugins_list = pr2.get("plugins", []) if plugins_r.get("success") else []
        d["updates_count"] = sum(1 for p in plugins_list if p.get("update_available") or p.get("has_update"))
    except Exception:
        d["updates_count"] = 0

    if SMART_SYSTEM_READY:
        try:
            analysis = agent_brain.analyze_site_context(d)
            d["ai_analysis"] = analysis
        except Exception:
            pass

    return jsonify({"success": True, "data": d, "connected": site.connected})

@wp_bp.route("/plugins", methods=["POST"])
def get_plugins():
    data = request.json
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404

    r = site.get_plugins()
    if not r.get("success"):
        return jsonify({"success": False, "error": r.get("error", "Connection failed"), "data": {"plugins": [], "count": 0}})

    # WP plugin returns {success, data:{plugins:[...]}}
    # _request wraps it as {success, data:{success, data:{plugins:[...]}}, status}
    wp_body = r.get("data", {})
    if isinstance(wp_body, dict) and "data" in wp_body:
        plugins = wp_body["data"].get("plugins", [])
    else:
        plugins = wp_body.get("plugins", [])

    for p in plugins:
        if "slug" in p and "file" not in p:       p["file"]       = p["slug"]
        if "update_available" in p:                p["has_update"] = p["update_available"]
        if "name" not in p:                        p["name"]       = p.get("slug", "—")
        if SMART_SYSTEM_READY:
            p["risk_score"] = pattern_engine.get_plugin_risk(p.get("slug"))

    return jsonify({"success": True, "data": {"plugins": plugins, "count": len(plugins)}})

@wp_bp.route("/users", methods=["POST"])
def get_users():
    data = request.json
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404

    r = site.get_users()
    if not r.get("success"):
        return jsonify({"success": False, "error": r.get("error", "Connection failed"), "data": {"users": [], "count": 0}})

    # WP plugin returns {success, users:[{id,username,email,name,role,registered}], count}
    # _request wraps as {success, data:{success, users:[...], count}, status}
    wp_body = r.get("data", {})
    raw_users = wp_body.get("users", []) if isinstance(wp_body, dict) else []

    users = []
    for u in raw_users:
        users.append({
            "id":         u.get("id") or u.get("ID", ""),
            "username":   u.get("username") or u.get("user_login", ""),
            "email":      u.get("email") or u.get("user_email", ""),
            "name":       u.get("name") or u.get("display_name", ""),
            "role":       u.get("role") or u.get("roles", ""),
            "registered": u.get("registered") or u.get("user_registered", ""),
        })

    return jsonify({"success": True, "data": {"users": users, "count": len(users)}})

@wp_bp.route("/test-connection", methods=["POST"])
def test_connection():
    data = request.json or {}
    name = data.get("site") or data.get("name")
    site = wp_manager.get_site(name) if name else None
    if not site:
        return jsonify({"success": False, "error": "Site not found in system. Add it first."}), 404
    import time as _t
    t0 = _t.time()
    connected = site.ping()
    latency = round((_t.time() - t0) * 1000)
    if connected:
        info_r = site.get_site_info()
        wp_body = info_r.get("data", {})
        if isinstance(wp_body, dict) and "data" in wp_body:
            wp_body = wp_body["data"]
        plugin_version = wp_body.get("plugin_version", "unknown")
        return jsonify({
            "success": True,
            "connected": True,
            "latency_ms": latency,
            "plugin_version": plugin_version,
            "site_name": wp_body.get("name", ""),
            "wp_version": wp_body.get("wp_version", ""),
        })
    return jsonify({
        "success": False,
        "connected": False,
        "error": "Cannot reach site. Check URL and ensure AIWA plugin is installed and activated.",
        "latency_ms": latency,
    })


@wp_bp.route("/ping-url", methods=["POST"])
def ping_url():
    data = request.json or {}
    url = data.get("url", "").rstrip("/")
    api_key = data.get("api_key", "")
    if not url or not api_key:
        return jsonify({"success": False, "error": "url and api_key required"})
    try:
        import requests as _req
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        resp = _req.get(
            url + "/wp-json/ai-agent/v1/ping",
            headers={"X-AIWA-Key": api_key},
            timeout=10,
            verify=False,
        )
        if resp.status_code == 200:
            body = resp.json()
            return jsonify({"success": True, "plugin_version": body.get("plugin_version", ""), "data": body})
        else:
            return jsonify({"success": False, "error": f"HTTP {resp.status_code}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@wp_bp.route("/users/delete", methods=["POST"])
def delete_wp_user():
    data = request.json or {}
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    user_id  = data.get("user_id")
    reassign = data.get("reassign", 1)
    if not user_id: return jsonify({"success": False, "error": "user_id required"}), 400
    r = site._request("POST", "users/delete", {"user_id": user_id, "reassign": reassign})
    wp_body = r.get("data", r)
    return jsonify({"success": r.get("success", False), "data": wp_body})


@wp_bp.route("/manage-users", methods=["POST"])
def manage_users():
    data = request.json
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    
    action = data.get("action")
    user_id = data.get("user_id")
    
    # استخدام DecisionEngine قبل تنفيذ عمليات حساسة
    if SMART_SYSTEM_READY:
        allowed = decision_engine.authorize_action("manage_users", {"action": action, "user_id": user_id})
        if not allowed:
            return jsonify({"success": False, "error": "Action blocked by DecisionEngine"}), 403

    if action == "delete":
        return jsonify(site.delete_user(user_id))
    return jsonify({"success": False, "error": "Invalid action"}), 400

@wp_bp.route("/courses", methods=["POST"])
def get_courses():
    data = request.json
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    return jsonify(site.get_courses())

@wp_bp.route("/hosting", methods=["POST"])
def get_hosting_info():
    try:
        from hosting_manager import hosting_manager
        return jsonify(hosting_manager.get_status())
    except ImportError:
        return jsonify({"success": False, "error": "Hosting manager not available"}), 500

@wp_bp.route("/ai-task", methods=["POST"])
def run_ai_task():
    data = request.json
    prompt = data.get("prompt")
    site_name = data.get("site")

    if not SMART_SYSTEM_READY:
        return jsonify({"success": False, "error": "Smart System (AgentBrain) is not initialized"}), 503

    result = agent_brain.execute_autonomous_task(prompt, site_name)
    return jsonify({"success": True, "result": result})


# ── Site CRUD ─────────────────────────────────────────────────────────────────

@wp_bp.route("/sites/update", methods=["POST"])
def update_site():
    from sites_store import sites_store
    data = request.json
    name = data.get("name")
    url  = data.get("url")
    key  = data.get("api_key")
    if not name: return jsonify({"success": False, "error": "name required"}), 400
    site = wp_manager.get_site(name)
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    if url: site.url = url
    if key: site.api_key = key
    sites_store.save(name, site.url, site.api_key)
    return jsonify({"success": True})


@wp_bp.route("/sites/delete", methods=["POST"])
def delete_site():
    from sites_store import sites_store
    data = request.json
    name = data.get("name")
    if not name: return jsonify({"success": False, "error": "name required"}), 400
    wp_manager.remove_site(name)
    sites_store.delete(name)
    return jsonify({"success": True})


@wp_bp.route("/sites/<name>/status", methods=["GET"])
def site_status(name):
    site = wp_manager.get_site(name)
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    import time
    start = time.time()
    connected = site.ping()
    latency_ms = round((time.time() - start) * 1000)
    return jsonify({
        "success": True,
        "name": name,
        "connected": connected,
        "latency_ms": latency_ms,
        "url": site.url,
    })


# ── Plugin Management ─────────────────────────────────────────────────────────

@wp_bp.route("/update-plugins", methods=["POST"])
def update_plugins():
    data = request.json
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    return jsonify(site.update_all_plugins())


@wp_bp.route("/toggle-plugin", methods=["POST"])
def toggle_plugin():
    data = request.json
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    return jsonify(site.toggle_plugin(data.get("plugin", ""), data.get("action", "activate")))


# ── Elementor ─────────────────────────────────────────────────────────────────

@wp_bp.route("/elementor-get", methods=["POST"])
def elementor_get():
    data = request.json
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    return jsonify(site.get_elementor_data(data.get("post_id")))


@wp_bp.route("/elementor-set", methods=["POST"])
def elementor_set():
    data = request.json
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    return jsonify(site.update_elementor_data(data.get("post_id"), data.get("elementor_data")))


# ── Courses / MasterStudy ─────────────────────────────────────────────────────

@wp_bp.route("/create-course", methods=["POST"])
def create_course():
    data = request.json
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    return jsonify(site.create_course(
        data.get("title", ""),
        data.get("content", ""),
        data.get("status", "draft"),
    ))


# ── Media / Users / Error Log ─────────────────────────────────────────────────

@wp_bp.route("/media", methods=["POST"])
def get_media():
    data = request.json
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    return jsonify(site.get_media())


@wp_bp.route("/error-log", methods=["POST"])
def get_error_log():
    data = request.json
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    return jsonify(site.get_error_log())


@wp_bp.route("/auto-heal", methods=["POST"])
def auto_heal():
    data = request.json
    site_name = data.get("site")
    try:
        from health_monitor import health_monitor
        result = health_monitor.get_site_health(site_name)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ── Proxy ─────────────────────────────────────────────────────────────────────

@wp_bp.route("/proxy", methods=["POST"])
def proxy():
    data = request.json
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    method = data.get("method", "GET").upper()
    path   = data.get("path", "")
    body   = data.get("data")
    return jsonify(site._request(method, path, body))


# ── Site Analyze ──────────────────────────────────────────────────────────────

@wp_bp.route("/analyze", methods=["POST"])
def analyze_site():
    data = request.json
    name = data.get("site")
    if not name: return jsonify({"success": False, "error": "site required"}), 400
    return jsonify(wp_manager.analyze_site(name))


# ── Knowledge Search ──────────────────────────────────────────────────────────

@wp_bp.route("/knowledge/search", methods=["POST", "GET"])
def knowledge_search():
    data = request.json or {}
    query = data.get("query") or request.args.get("q", "")
    if not query: return jsonify({"success": False, "error": "query required"}), 400
    try:
        from knowledge_manager import knowledge_manager
        results = knowledge_manager.search(query)
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ── AI Operator / Agents ──────────────────────────────────────────────────────

@wp_bp.route("/operator/run", methods=["POST"])
@wp_bp.route("/agents/run", methods=["POST"])
def operator_run():
    data = request.json or {}
    task = data.get("task") or data.get("prompt", "")
    site_name = data.get("site")
    explain   = data.get("explain", False)
    if not task: return jsonify({"success": False, "error": "task required"}), 400
    try:
        from ai_operator import ai_operator
        site = wp_manager.get_site(site_name) if site_name else None
        result = ai_operator.execute(task, site=site, explain=explain)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@wp_bp.route("/operator/explain", methods=["POST"])
def operator_explain():
    data = request.json or {}
    data["explain"] = True
    task = data.get("task") or data.get("prompt", "")
    site_name = data.get("site")
    if not task: return jsonify({"success": False, "error": "task required"}), 400
    try:
        from ai_operator import ai_operator
        site = wp_manager.get_site(site_name) if site_name else None
        result = ai_operator.execute(task, site=site, explain=True)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ── Health ─────────────────────────────────────────────────────────────────────

@wp_bp.route("/health", methods=["GET"])
def wp_health():
    try:
        from health_monitor import health_monitor
        return jsonify({"success": True, "health": health_monitor.get_all_health()})
    except Exception as e:
        return jsonify({"success": True, "status": "ok", "note": str(e)})


# ── LLM Config ────────────────────────────────────────────────────────────────

@wp_bp.route("/llm/config", methods=["GET"])
def llm_config_get():
    try:
        from llm_bridge import llm_bridge
        return jsonify({"success": True, "config": llm_bridge.get_config()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ── MasterStudy LMS ───────────────────────────────────────────────────────────

@wp_bp.route("/masterstudy/ai-create", methods=["POST"])
def masterstudy_ai_create():
    data = request.json or {}
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    try:
        from masterstudy_manager import MasterStudyManager
        ms = MasterStudyManager(site)
        result = ms.ai_create_full_course(
            topic=data.get("topic", ""),
            lessons_count=data.get("lessons_count", 5),
            language=data.get("language", "ar"),
            price=data.get("price", 0),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@wp_bp.route("/masterstudy/analyze", methods=["POST"])
def masterstudy_analyze():
    data = request.json or {}
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    try:
        from masterstudy_manager import MasterStudyManager
        ms = MasterStudyManager(site)
        result = ms.ai_analyze_course(data.get("course_id"))
        return jsonify({"success": True, "analysis": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
