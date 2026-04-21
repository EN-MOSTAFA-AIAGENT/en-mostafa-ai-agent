"""
Append persistence + health monitor to wp_routes.py
Run: py -3.11 append_persistence.py
"""
import os

PATCH = '''

# ══════════════════════════════════════════════
#  Persistence + Health Monitor
# ══════════════════════════════════════════════

@wp_bp.route("/sites", methods=["GET"])
def list_sites():
    """كل المواقع المسجلة مع حالتها"""
    from sites_store import sites_store
    saved = sites_store.load_all()
    aware = system_awareness.get_all_sites()
    aware_map = {s["name"]: s for s in aware}
    result = []
    for s in saved:
        info = aware_map.get(s["name"], {})
        result.append({
            "name":       s["name"],
            "url":        s["url"],
            "connection": info.get("connection", "unknown"),
            "latency_ms": info.get("latency_ms", 0),
            "wp_version": info.get("wp_version"),
            "plugins_active": info.get("plugins_active", 0),
        })
    # Also include in-memory only sites
    for name in wp_manager.list_sites():
        if not any(r["name"] == name for r in result):
            info = aware_map.get(name, {})
            site = wp_manager.get_site(name)
            result.append({
                "name":       name,
                "url":        site.url if site else "",
                "connection": info.get("connection", "unknown"),
                "latency_ms": info.get("latency_ms", 0),
            })
    return jsonify({"sites": result, "count": len(result)})


@wp_bp.route("/sites/delete", methods=["POST"])
def delete_site():
    from sites_store import sites_store
    data = request.get_json(force=True) or {}
    name = data.get("name", "")
    sites_store.delete(name)
    wp_manager.remove_site(name)
    return jsonify({"success": True, "deleted": name})


@wp_bp.route("/health", methods=["GET"])
def health_summary():
    """ملخص صحة كل المواقع"""
    try:
        from health_monitor import health_monitor
        return jsonify(health_monitor.get_summary())
    except Exception as e:
        return jsonify({"error": str(e), "sites": system_awareness.get_all_sites()})


@wp_bp.route("/health/all", methods=["GET"])
def health_all():
    """تقرير صحة شامل"""
    try:
        from health_monitor import health_monitor
        return jsonify(health_monitor.get_all_health())
    except Exception as e:
        return jsonify({"error": str(e)})


@wp_bp.route("/health/events", methods=["GET"])
def health_events():
    try:
        from health_monitor import health_monitor
        limit  = int(request.args.get("limit", 50))
        return jsonify({"events": health_monitor.get_recent_events(limit)})
    except Exception as e:
        return jsonify({"events": [], "error": str(e)})

'''

target = r"C:\mcp-agent\wp_routes.py"
current = open(target, encoding="utf-8", errors="replace").read()

if "/sites/delete" in current:
    print("Already has persistence routes")
else:
    with open(target, "a", encoding="utf-8") as f:
        f.write(PATCH)
    print("Appended persistence + health routes")
    print("New size:", os.path.getsize(target))
