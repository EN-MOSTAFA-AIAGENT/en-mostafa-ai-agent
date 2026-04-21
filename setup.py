"""
Setup Script — AI WordPress Control Center
يثبت كل المتطلبات ويجهز قاعدة البيانات
Run: py -3.11 setup.py
"""
import subprocess, sys, os

DEPS = [
    "flask",
    "flask-socketio",
    "playwright",
    "httpx",
    "requests",
]

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.returncode == 0, r.stdout + r.stderr

def step(msg):
    print(f"\n{'='*50}")
    print(f"  {msg}")
    print('='*50)

step("1/5 Installing Python dependencies")
for dep in DEPS:
    ok, out = run(f"py -3.11 -m pip install {dep} --quiet --break-system-packages")
    if not ok:
        ok, out = run(f"py -3.11 -m pip install {dep} --quiet")
    print(f"  {'OK' if ok else 'WARN'} {dep}")

step("2/5 Installing Playwright browsers")
ok, out = run("py -3.11 -m playwright install chromium")
print(f"  {'OK' if ok else 'WARN'} Playwright chromium")

step("3/5 Initializing databases")
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
try:
    from knowledge_manager import knowledge_manager
    print("  OK knowledge_manager DB")
    from feedback_loop import feedback_loop
    print("  OK feedback_loop DB")
    from memory_engine import MemoryEngine
    MemoryEngine()
    print("  OK memory_engine DB")
    from task_engine import TaskEngine
    TaskEngine()
    print("  OK task_engine DB")
except Exception as e:
    print(f"  WARN DB init: {e}")

step("4/5 Loading initial WordPress knowledge")
try:
    from knowledge_manager import knowledge_manager
    entries = [
        ("WordPress REST API uses /wp-json/wp/v2/ namespace. Requires authentication for write operations via Application Passwords or OAuth.", "wp-rest-api", ["wordpress","rest","api"]),
        ("WordPress hooks: add_action(), add_filter(), do_action(), apply_filters(). Plugins use these to extend functionality without modifying core.", "wp-hooks", ["wordpress","hooks","plugin"]),
        ("Elementor stores page data in _elementor_data post meta as JSON. Use get_post_meta(post_id, '_elementor_data', true) to read.", "elementor-data", ["elementor","postmeta"]),
        ("LearnDash post types: sfwd-courses, sfwd-lessons, sfwd-topic, sfwd-quiz, sfwd-question. Use wp_insert_post() to create programmatically.", "learndash-posttypes", ["learndash","courses"]),
        ("WP-CLI common commands: wp plugin list, wp plugin update --all, wp db optimize, wp cache flush, wp cron event run --due-now", "wpcli-commands", ["wpcli","cli"]),
        ("WordPress Self-Healing: detect Fatal errors in debug.log, deactivate_plugins() for conflicting plugin, wp_cache_flush() to clear cache.", "wp-selfheal", ["wordpress","error","healing"]),
    ]
    for text, title, tags in entries:
        r = knowledge_manager.learn_from_text(text, title=title, tags=tags)
        print(f"  {'OK' if r.get('success') else 'DUP'} {title}")
except Exception as e:
    print(f"  WARN knowledge load: {e}")

step("5/5 Verifying system")
try:
    from tool_registry    import tool_registry
    from system_awareness import system_awareness
    from llm_bridge       import llm_bridge
    from multi_agent      import orchestrator
    from agent_core       import AgentCore

    # Quick integration check
    AgentCore()
    assert orchestrator.route("elementor design")  == "creative"
    assert orchestrator.route("update plugins")    == "technical"
    assert orchestrator.route("create course")     == "educator"

    import ast
    ast.parse(open("server.py", encoding="utf-8", errors="replace").read())
    print("  OK server.py syntax")
    print("  OK all modules")
    print("  OK multi-agent routing")
except Exception as e:
    print(f"  WARN: {e}")

print()
print("="*50)
print("  SETUP COMPLETE")
print()
print("  To start: py -3.11 server.py")
print("  Or:       start.bat")
print()
print("  Dashboard: http://localhost:5001/wp-dashboard")
print("  Status:    http://localhost:5001/system/status")
print("="*50)
