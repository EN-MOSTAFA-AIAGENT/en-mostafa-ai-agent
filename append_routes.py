
# ══════════════════════════════════════════════
#  APPEND: Multi-Agent + Extra Routes
#  Run: py -3.11 append_routes.py
# ══════════════════════════════════════════════

EXTRA = '''

# ══════════════════════════════════════════════
#  Multi-Agent Routes
# ══════════════════════════════════════════════

@wp_bp.route("/agents/status", methods=["GET"])
def agents_status():
    try:
        from multi_agent import orchestrator
        return jsonify({"success": True, "agents": orchestrator.status()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@wp_bp.route("/agents/run", methods=["POST"])
def agents_run():
    import time as _t
    try:
        from multi_agent import orchestrator
        from wp_manager  import wp_manager as _wpm
    except Exception as e:
        return jsonify({"error": "multi_agent not available: " + str(e)}), 500

    data      = request.get_json(force=True) or {}
    task      = data.get("task", "")
    site_name = data.get("site")
    all_sites = data.get("all_sites", False)
    if not task:
        return jsonify({"error": "task required"}), 400

    site = _wpm.get_site(site_name) if site_name else None
    t0   = _t.time()

    if all_sites:
        sites   = _wpm.get_all_sites()
        results = orchestrator.handle_all(task, sites)
        return jsonify({"success": True, "all_sites": True,
                        "results": results, "duration": round(_t.time()-t0, 2)})

    result = orchestrator.handle(task, site)
    result["duration"] = round(_t.time()-t0, 2)
    return jsonify(result)


@wp_bp.route("/agents/route", methods=["POST"])
def agents_route():
    try:
        from multi_agent import orchestrator
        data = request.get_json(force=True) or {}
        task = data.get("task", "")
        role = orchestrator.route(task)
        return jsonify({"task": task, "routed_to": role,
                        "agent": orchestrator.agents[role].name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════
#  Export Data
# ══════════════════════════════════════════════

@wp_bp.route("/export-data", methods=["POST"])
def export_data():
    data      = request.get_json(force=True) or {}
    site      = wp_manager.get_site(data.get("site"))
    post_type = data.get("type", "posts")
    if not site:
        return jsonify({"success": False, "error": "Site not found"}), 404
    return jsonify(site.export_data(post_type))


@wp_bp.route("/import-xml", methods=["POST"])
def import_xml():
    data = request.get_json(force=True) or {}
    site = wp_manager.get_site(data.get("site"))
    xml  = data.get("xml_content", "")
    if not site:
        return jsonify({"success": False, "error": "Site not found"}), 404
    return jsonify(site.import_xml(xml))


# ══════════════════════════════════════════════
#  CLI Proxy
# ══════════════════════════════════════════════

@wp_bp.route("/run-cli", methods=["POST"])
def run_cli():
    data = request.get_json(force=True) or {}
    site = wp_manager.get_site(data.get("site"))
    cmd  = data.get("command", "")
    if not site:
        return jsonify({"success": False, "error": "Site not found"}), 404
    if not cmd:
        return jsonify({"success": False, "error": "command required"}), 400
    return jsonify(site.run_cli(cmd))


# ══════════════════════════════════════════════
#  Feedback & Knowledge Stats (public)
# ══════════════════════════════════════════════

@wp_bp.route("/feedback", methods=["GET"])
def feedback_summary():
    return jsonify({
        "stats":        feedback_loop.get_stats(),
        "recent":       feedback_loop.get_recent(10),
        "improvements": feedback_loop.suggest_improvements(),
        "patterns":     feedback_loop.get_failing_patterns(),
    })


@wp_bp.route("/knowledge", methods=["GET"])
def knowledge_summary():
    return jsonify({
        "stats": knowledge_manager.get_stats(),
        "list":  knowledge_manager.list_all()[:20],
    })

'''

import os

target = r"C:\mcp-agent\wp_routes.py"
current = open(target, encoding="utf-8", errors="replace").read()

if "/agents/run" in current:
    print("Already has multi-agent routes")
else:
    with open(target, "a", encoding="utf-8") as f:
        f.write(EXTRA)
    print("Appended multi-agent + extra routes to wp_routes.py")
    print("New size:", os.path.getsize(target))
