"""
Patch script — injects WordPress Integration into server.py
Run: py -3 apply_patch.py
"""
import os

PATCH = '''

# ======================================================
#  WordPress Integration Layer
# ======================================================
try:
    from wp_routes        import wp_bp
    from system_awareness import system_awareness
    from feedback_loop    import feedback_loop
    from knowledge_manager import knowledge_manager
    from llm_bridge       import llm_bridge
    from tool_registry    import tool_registry, ToolType
    from agent_core       import AgentCore as _AgentCore
    from wp_manager       import wp_manager as _wp_manager

    app.register_blueprint(wp_bp)

    _shared_agent = None

    def _get_agent():
        global _shared_agent
        if _shared_agent is None:
            _shared_agent = _AgentCore()
            tool_registry.register("memory_engine",   ToolType.MEMORY,    _shared_agent.memory,    "Execution memory",    1)
            tool_registry.register("pattern_engine",  ToolType.ANALYSIS,  _shared_agent.pattern,   "Error patterns",      2)
            tool_registry.register("strategy_engine", ToolType.ANALYSIS,  _shared_agent.strategy,  "Strategy engine",     2)
            tool_registry.register("system_executor", ToolType.EXECUTION, _shared_agent.executor,  "Shell execution",     3)
            tool_registry.register("knowledge_mgr",   ToolType.KNOWLEDGE, knowledge_manager,        "Knowledge base",      1)
            tool_registry.register("llm_bridge",      ToolType.LLM,       llm_bridge,               "LLM interface",       1)
            tool_registry.register("wp_manager",      ToolType.WP,        _wp_manager,              "WP multi-site",       1)
            feedback_loop.on_result(
                lambda r: logger.info("[FB] " + ("OK" if r["success"] else "FAIL") + " " + r["task"][:40])
            )
        return _shared_agent

    _get_agent()
    system_awareness.start_heartbeat(_wp_manager, interval=60)
    _wp_manager.start_heartbeat(interval=60)
    logger.info("WordPress Integration Layer loaded OK")

except Exception as _wp_init_err:
    import logging as _log
    _log.getLogger("server").warning(f"WordPress layer optional: {_wp_init_err}")


@app.route("/run", methods=["POST"])
def run_task():
    import time as _t
    data      = request.get_json(force=True) or {}
    task      = data.get("task", "")
    site      = data.get("site")
    all_sites = data.get("all_sites", False)
    explain   = data.get("explain", False)
    if not task:
        return jsonify({"error": "task required"}), 400
    try:
        agent = _get_agent()
        system_awareness.begin_task(task, tool="agent_core", site=site)
        t0 = _t.time()
        if all_sites:
            result = agent.execute_on_all_sites(task)
        elif site:
            result = agent.execute_wordpress_task(site, task)
        else:
            result = agent.handle_task(task, explain=explain)
        dur    = _t.time() - t0
        r_dict = result if isinstance(result, dict) else {"result": result, "status": "completed"}
        system_awareness.end_task(success=True)
        feedback_loop.record(
            task=task, result=r_dict, tool="agent_core",
            site=site or "", duration=dur,
            memory_engine=agent.memory,
            strategy_engine=agent.strategy
        )
        return jsonify(r_dict)
    except Exception as e:
        system_awareness.end_task(success=False)
        return jsonify({"error": str(e), "status": "failed"}), 500


@app.route("/knowledge/upload", methods=["POST"])
def knowledge_upload():
    import tempfile as _tmp
    f    = request.files.get("file")
    tags = request.form.get("tags", "").split(",")
    if not f:
        return jsonify({"success": False, "reason": "no file"}), 400
    ext  = os.path.splitext(f.filename)[1]
    tmp  = _tmp.mktemp(suffix=ext)
    f.save(tmp)
    res  = knowledge_manager.learn_from_file(tmp, tags=[t.strip() for t in tags if t.strip()])
    try:
        os.remove(tmp)
    except Exception:
        pass
    return jsonify(res)


@app.route("/system/status", methods=["GET"])
def system_full_status():
    return jsonify({
        "awareness":    system_awareness.get_snapshot(),
        "tools":        tool_registry.get_all_status(),
        "tools_health": tool_registry.health_check(),
        "feedback":     feedback_loop.get_stats(),
        "knowledge":    knowledge_manager.get_stats(),
        "llm":          llm_bridge.get_config(),
        "improvements": feedback_loop.suggest_improvements(),
    })


@app.route("/llm/configure", methods=["POST"])
def configure_llm():
    data = request.get_json(force=True) or {}
    llm_bridge.configure(
        provider=data.get("provider", "mock"),
        api_key=data.get("api_key", ""),
        model=data.get("model", ""),
        base_url=data.get("base_url", ""),
    )
    return jsonify({"success": True, "config": llm_bridge.get_config()})


@app.route("/wp-dashboard", methods=["GET"])
def wp_dashboard_page():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "wp-dashboard.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as fh:
            return fh.read(), 200, {"Content-Type": "text/html; charset=utf-8"}
    return "WordPress Dashboard not found", 404

'''

TARGET = r"C:\mcp-agent\server.py"
MARKER = 'if __name__ == "__main__":'

with open(TARGET, "r", encoding="utf-8", errors="replace") as f:
    original = f.read()

if MARKER not in original:
    print("ERROR: marker not found in server.py")
    exit(1)

if "WordPress Integration Layer" in original:
    print("ALREADY PATCHED — skipping")
    exit(0)

patched = original.replace(MARKER, PATCH + MARKER, 1)

# backup
with open(TARGET + ".bak", "w", encoding="utf-8") as f:
    f.write(original)

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(patched)

new_size = os.path.getsize(TARGET)
print(f"PATCH APPLIED OK — server.py: {new_size} bytes")
print(f"Backup saved: server.py.bak")
