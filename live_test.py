"""
Live API Test — tests all endpoints against the running server
Run: py -3.11 live_test.py
"""
import urllib.request, json, sys, time
sys.path.insert(0, r'C:\mcp-agent')

BASE = 'http://127.0.0.1:5001'
results = []

def get(path, timeout=5):
    try:
        r = urllib.request.urlopen(BASE + path, timeout=timeout)
        return json.loads(r.read()), r.status
    except Exception as e:
        return {"error": str(e)}, 0

def post(path, body=None, timeout=8):
    try:
        data = json.dumps(body or {}).encode()
        req  = urllib.request.Request(
            BASE + path, data=data,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        r = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(r.read()), r.status
    except Exception as e:
        return {"error": str(e)}, 0

def t(name, fn, expect_key=None):
    d, code = fn()
    ok = (code in (200, 201)) and "error" not in d
    if ok and expect_key:
        ok = expect_key in d
    results.append((name, ok, code))
    status = "PASS" if ok else "FAIL"
    snippet = str(d)[:60].replace("\n"," ")
    print(f"  [{status}] {name:40s} {code}  {snippet}")
    return ok

print()
print("=" * 65)
print("  LIVE API TEST — EN MOSTAFA AI AGENT")
print("=" * 65)

# ── Core ──────────────────────────────────────────────────────────
print("\n[CORE]")
t("GET /healthz",               lambda: get("/healthz"),             "ok")
t("GET /system/status",         lambda: get("/system/status"),       "awareness")
t("GET /health",                lambda: get("/health"),              "status")
t("GET /capabilities",          lambda: get("/capabilities"))

# ── WordPress ─────────────────────────────────────────────────────
print("\n[WORDPRESS]")
t("GET /wp/sites-status",       lambda: get("/wp/sites-status"),     "sites")
t("GET /wp/agents/status",      lambda: get("/wp/agents/status"),    "agents")
t("GET /wp/knowledge",          lambda: get("/wp/knowledge"),        "stats")
t("GET /wp/feedback",           lambda: get("/wp/feedback"),         "stats")
t("GET /wp/health",             lambda: get("/wp/health"),           "auto_heal_on")
t("GET /wp/health/all",         lambda: get("/wp/health/all"))
t("GET /wp/sites",              lambda: get("/wp/sites"),            "sites")
t("GET /wp/knowledge/stats",    lambda: get("/wp/knowledge/stats"),  "total")
t("GET /wp/llm/config",         lambda: get("/wp/llm/config"),       "provider")
t("GET /wp/system/snapshot",    lambda: get("/wp/system/snapshot"),  "awareness")

# ── POST endpoints ────────────────────────────────────────────────
print("\n[POST]")
t("POST /wp/knowledge/search",
  lambda: post("/wp/knowledge/search",  {"query": "wordpress hooks"}),
  "results")
t("POST /wp/agents/route",
  lambda: post("/wp/agents/route",      {"task": "elementor design page"}),
  "routed_to")
t("POST /wp/agents/route (educator)",
  lambda: post("/wp/agents/route",      {"task": "create learndash course"}),
  "routed_to")
t("POST /wp/agents/route (technical)",
  lambda: post("/wp/agents/route",      {"task": "update all plugins"}),
  "routed_to")
t("POST /wp/knowledge/learn-url (bad url)",
  lambda: post("/wp/knowledge/learn-url", {"url": "https://x-invalid-99.xyz"}))
t("POST /wp/register-site (missing data)",
  lambda: post("/wp/register-site",    {}))    # should return 400
t("POST /run (no task)",
  lambda: post("/run",                 {}))    # should return 400
t("POST /run (local echo)",
  lambda: post("/run",                 {"task": "echo hello world"}))
t("POST /llm/configure",
  lambda: post("/llm/configure",      {"provider": "mock", "model": "test-model"}),
  "success")

# ── Dashboard HTML ────────────────────────────────────────────────
print("\n[DASHBOARD]")
d, code = get("/wp-dashboard")
if code == 200 and "html" in str(type(d)).lower() or "start" in str(d).lower():
    print("  [PASS] GET /wp-dashboard                            200")
    results.append(("GET /wp-dashboard", True, 200))
else:
    # Check if it returned the HTML page
    try:
        req = urllib.request.Request(BASE + "/wp-dashboard")
        r   = urllib.request.urlopen(req, timeout=5)
        html = r.read().decode("utf-8", errors="replace")
        ok   = "startLivePolling" in html and "wp-dashboard" in html.lower()
        print("  [" + ("PASS" if ok else "FAIL") + "] GET /wp-dashboard (HTML)                     " + str(r.status))
        results.append(("GET /wp-dashboard HTML", ok, r.status))
    except Exception as e:
        print("  [FAIL] GET /wp-dashboard:", str(e)[:50])
        results.append(("GET /wp-dashboard", False, 0))

# ── Routing validation ────────────────────────────────────────────
print("\n[ROUTING VALIDATION]")
routing_cases = [
    ("elementor landing page design", "creative"),
    ("update all plugins woocommerce", "technical"),
    ("create learndash course python", "educator"),
    ("fix plugin fatal error",         "technical"),
    ("elementor banner section color", "creative"),
    ("learndash quiz enrollment",      "educator"),
]
routing_ok = 0
for task, expected in routing_cases:
    d, code = post("/wp/agents/route", {"task": task})
    got  = d.get("routed_to", "?")
    ok   = got == expected
    if ok:
        routing_ok += 1
    print(f"  [{'OK' if ok else 'NO'}] {task[:38]:38s} -> {got} (expected {expected})")
results.append(("routing_validation", routing_ok >= 5, 200))

# ── Summary ───────────────────────────────────────────────────────
passed = sum(1 for _, ok, _ in results if ok)
failed = [(n, c) for n, ok, c in results if not ok]

print()
print("=" * 65)
print(f"  LIVE TESTS:   {passed} / {len(results)} passed")
print(f"  ROUTING:      {routing_ok} / {len(routing_cases)} correct")
if failed:
    print(f"  FAILED ({len(failed)}):")
    for n, c in failed:
        print(f"    - {n}  (code={c})")
else:
    print("  ALL LIVE TESTS PASSED")
print("=" * 65)
