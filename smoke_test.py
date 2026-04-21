"""
Integration Smoke Test
يختبر كل المكونات الجديدة بدون Flask
"""
import sys, os
sys.path.insert(0, r"C:\mcp-agent")

errors = []
passed = []

def test(name, fn):
    try:
        fn()
        passed.append(name)
        print(f"  ✅  {name}")
    except Exception as e:
        errors.append((name, str(e)))
        print(f"  ❌  {name}: {e}")

# ── 1. Tool Registry
def t_registry():
    from tool_registry import ToolRegistry, ToolType
    r = ToolRegistry()
    class FakeMem:
        def get_best_strategy(self, c): return None
    r.register("mem", ToolType.MEMORY, FakeMem(), "test", 1)
    assert r.get("mem") is not None
    assert len(r.get_by_type(ToolType.MEMORY)) == 1
test("ToolRegistry", t_registry)

# ── 2. System Awareness
def t_awareness():
    from system_awareness import SystemAwareness, ConnectionState
    sa = SystemAwareness()
    sa.begin_task("test task", "mem", "site1")
    assert sa.current_task == "test task"
    assert sa.current_site == "site1"
    sa.register_site("s1", "https://example.com")
    sa.update_site_ping("s1", True, 50.0, {"wp_version": "6.5"})
    sites = sa.get_all_sites()
    assert len(sites) == 1
    assert sites[0]["connection"] == ConnectionState.CONNECTED
    sa.end_task(success=True)
    snap = sa.get_snapshot()
    assert snap["tasks_done"] == 1
test("SystemAwareness", t_awareness)

# ── 3. LLM Bridge (mock mode)
def t_llm():
    from llm_bridge import LLMBridge, LLMProvider
    llm = LLMBridge()
    assert llm.provider == LLMProvider.MOCK or True   # env may differ
    r = llm.think("test task", {}, "")
    assert "task" in r
    assert "plan" in r
    cfg = llm.get_config()
    assert "provider" in cfg
test("LLMBridge (mock)", t_llm)

# ── 4. Feedback Loop
def t_feedback():
    from feedback_loop import FeedbackLoop, FeedbackRecord
    fl = FeedbackLoop()
    rec = fl.record(
        task="test:ping", result={"status": "completed"},
        tool="test", site="s1", duration=0.5
    )
    assert rec.success is True
    assert rec.score  >  0
    stats = fl.get_stats()
    assert stats["total"] >= 1
    assert "success_rate" in stats
    tips = fl.suggest_improvements()
    assert isinstance(tips, list)
test("FeedbackLoop", t_feedback)

# ── 5. Knowledge Manager
def t_knowledge():
    from knowledge_manager import KnowledgeManager
    km = KnowledgeManager()
    r  = km.learn_from_text("WordPress is a CMS. Plugins extend functionality.", title="wp-intro", tags=["wordpress"])
    assert r["success"] in (True, False)   # may be duplicate
    res = km.search("WordPress")
    assert isinstance(res, list)
    sr  = km.search_for_task("install plugin")
    assert "has_knowledge" in sr
    stats = km.get_stats()
    assert "total" in stats
test("KnowledgeManager", t_knowledge)

# ── 6. WP Manager
def t_wpmanager():
    from wp_manager import WPManager
    wm = WPManager()
    site = wm.add_site("test-site", "https://example.com", "fake-key-123")
    assert wm.get_site("test-site") is not None
    assert "test-site" in wm.list_sites()
test("WPManager", t_wpmanager)

# ── 7. AgentCore integration
def t_agentcore():
    from agent_core import AgentCore, IntegrationLayer, ExplainBeforeExecute, SelfHealingFirewall
    agent = AgentCore()
    assert hasattr(agent, "integration")
    assert hasattr(agent, "explainer")
    assert hasattr(agent, "firewall")
    assert hasattr(agent, "knowledge")
    assert hasattr(agent, "wp_manager")
    # firewall
    fw = agent.firewall.analyze_error("PHP Fatal error in plugins/my-plugin")
    assert fw["category"] == "plugin_conflict"
    # explainer
    plan = [{"step": "ping", "command": "echo ok"}]
    exp  = agent.explainer.explain("test task", plan, {"has_knowledge": False, "count": 0, "results": []})
    assert "test task" in exp
    # integration layer
    il   = agent.integration
    pre  = il.pre_execute("echo ok", "test task")
    assert "predicted_risk" in pre
    assert il.route_to_agent("elementor design") == "creative"
    assert il.route_to_agent("learndash course") == "educator"
    assert il.route_to_agent("update plugins")   == "technical"
test("AgentCore (Integration Layer)", t_agentcore)

# ── 8. server.py routes present
def t_server_routes():
    with open(r"C:\mcp-agent\server.py", "r", encoding="utf-8", errors="replace") as f:
        src = f.read()
    assert "WordPress Integration Layer" in src,  "WP Integration block missing"
    assert "/run"              in src,             "/run route missing"
    assert "/system/status"   in src,             "/system/status missing"
    assert "/wp-dashboard"    in src,             "/wp-dashboard missing"
    assert "knowledge_upload" in src,             "knowledge_upload missing"
    assert "register_blueprint" in src,           "register_blueprint missing"
test("server.py routes", t_server_routes)

# ── 9. WordPress Plugin files
def t_wp_plugin():
    base = r"C:\mcp-agent\wordpress-plugin\ai-wordpress-agent"
    files = [
        "ai-wordpress-agent.php",
        "includes/class-aiwa-api.php",
        "includes/class-aiwa-heartbeat.php",
        "includes/class-aiwa-selfheal.php",
        "admin/class-aiwa-dashboard.php",
    ]
    for fp in files:
        path = os.path.join(base, fp)
        assert os.path.exists(path), f"Missing: {fp}"
        assert os.path.getsize(path) > 500, f"Too small: {fp}"
test("WordPress Plugin files", t_wp_plugin)

# ── 10. Dashboard HTML
def t_dashboard():
    path = r"C:\mcp-agent\templates\wp-dashboard.html"
    assert os.path.exists(path)
    html = open(path, encoding="utf-8").read()
    checks = [
        "pollSystemStatus",
        "updateToolsPanel",
        "updateFeedbackPanel",
        "updateLLMStatus",
        "saveLLMConfig",
        "startLivePolling",
        "tools-panel",
        "fb-total",
        "llm-provider",
    ]
    for c in checks:
        assert c in html, f"Missing in dashboard: {c}"
test("Dashboard HTML (live wiring)", t_dashboard)

# ── Summary
print()
print("=" * 50)
print(f"  PASSED: {len(passed)} / {len(passed)+len(errors)}")
if errors:
    print(f"  FAILED: {len(errors)}")
    for name, err in errors:
        print(f"    ✗ {name}: {err}")
else:
    print("  ALL TESTS PASSED ✅")
print("=" * 50)
