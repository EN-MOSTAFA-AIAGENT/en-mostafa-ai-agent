"""
Append health_monitor + sites_store startup to server.py
Run: py -3.11 append_startup.py
"""
import os

PATCH = '''

# ══════════════════════════════════════════════
#  Startup: Restore Sites + Health Monitor
# ══════════════════════════════════════════════

try:
    from sites_store   import sites_store, restore_sites_to_manager
    from health_monitor import health_monitor
    from wp_manager    import wp_manager as _wpm_startup

    # Restore saved sites from DB
    _restored = restore_sites_to_manager(_wpm_startup)
    if _restored:
        logger.info(f"Restored {_restored} WordPress sites from database")

    # Start health monitoring
    health_monitor.start(_wpm_startup, interval=60)

    # Wire health events to dashboard
    def _on_health_event(event):
        append_dashboard_log(
            f"[HEALTH] {event['type']} — {event['source']}",
            "warn" if "down" in event["type"] else "info"
        )
    health_monitor.on_event(_on_health_event)

    # Add /health route
    @app.route("/health", methods=["GET"])
    def agent_health():
        return jsonify({
            "status":  "ok",
            "monitor": health_monitor.get_summary(),
            "system":  system_awareness.get_snapshot(),
        })

    @app.route("/health/events", methods=["GET"])
    def health_events_direct():
        return jsonify({
            "events": health_monitor.get_recent_events(
                int(request.args.get("limit", 50))
            )
        })

    # Patch /wp/register-site to also persist
    _orig_register = None  # wp_routes handles this already

    logger.info("Health Monitor + Sites Store active")

except Exception as _hm_err:
    logger.warning(f"Health Monitor optional: {_hm_err}")

'''

TARGET = r"C:\mcp-agent\server.py"
MARKER = 'if __name__ == "__main__":'

current = open(TARGET, encoding="utf-8", errors="replace").read()

if "Health Monitor + Sites Store" in current:
    print("Already patched with health monitor")
elif MARKER in current:
    patched = current.replace(MARKER, PATCH + MARKER, 1)
    open(TARGET, "w", encoding="utf-8").write(patched)
    print("Health Monitor injected into server.py")
    print("New size:", os.path.getsize(TARGET))
else:
    print("ERROR: marker not found")
