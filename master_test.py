"""Master Final Test — py -3.11 -W ignore master_test.py"""
import sys, os, time
sys.path.insert(0, r'C:\mcp-agent')
os.chdir(r'C:\mcp-agent')

P = []; F = []

def t(n, fn):
    try:    fn(); P.append(n); print('PASS', n)
    except Exception as e: F.append((n, str(e)[:90])); print('FAIL', n, ':', str(e)[:90])

# 1. ToolRegistry
def t1():
    from tool_registry import ToolRegistry, ToolType
    r = ToolRegistry()
    r.register('mem', ToolType.MEMORY,    object(), '', 1)
    r.register('kn',  ToolType.KNOWLEDGE, object(), '', 1)
    assert r.health_check()['healthy']
    best = r.choose_best_tool('search plugin')
    assert best is not None
t('ToolRegistry', t1)

# 2. SystemAwareness
def t2():
    from system_awareness import SystemAwareness, ConnectionState
    sa = SystemAwareness()
    sa.register_site('s1', 'https://x.com')
    sa.update_site_ping('s1', True, 150.0, {'wp_version': '6.5', 'plugins_active': 12})
    site = sa.get_all_sites()[0]
    assert site['latency_ms'] == 150.0
    assert site['connection'] == ConnectionState.CONNECTED
    snap = sa.get_snapshot()
    assert 's1' in snap['connected_sites']
t('SystemAwareness', t2)

# 3. SitesStore
def t3():
    from sites_store import SitesStore
    s = SitesStore()
    s.save('ts', 'https://ts.com', 'key-abc', {'note': 'test'})
    loaded = s.get('ts')
    assert loaded and loaded['url'] == 'https://ts.com'
    assert loaded['meta']['note'] == 'test'
    assert s.count() >= 1
    s.delete('ts')
t('SitesStore persistence', t3)

# 4. HealthMonitor
def t4():
    from health_monitor import HealthMonitor, HealthEvent
    hm = HealthMonitor()
    received = []
    hm.on_event(lambda e: received.append(e))
    hm._emit(HealthEvent.SITE_UP,   'site1', {'latency_ms': 80})
    hm._emit(HealthEvent.SITE_DOWN, 'site2', {'latency_ms': 0})
    assert len(received) == 2
    assert received[0]['type'] == HealthEvent.SITE_UP
    assert received[1]['source'] == 'site2'
    summary = hm.get_summary()
    assert 'auto_heal_on' in summary
    assert len(hm.get_recent_events(10)) >= 2
t('HealthMonitor', t4)

# 5. LLMBridge
def t5():
    from llm_bridge import LLMBridge
    b = LLMBridge()
    r = b.think('create wordpress elementor landing page', {'role': 'creative'}, 'Elementor JSON data')
    assert 'task' in r and 'plan' in r and 'explanation' in r
    doc = b.learn_from_doc('WordPress hooks: add_action, add_filter', 'wp-docs')
    assert 'summary' in doc
    err = b.analyze_error('Fatal error: Call to undefined function in plugins/broken/code.php')
    assert 'analysis' in err
t('LLMBridge', t5)

# 6. FeedbackLoop
def t6():
    from feedback_loop import FeedbackLoop
    fl = FeedbackLoop()
    for i in range(5):
        fl.record(f'task{i}', {'status': 'completed'}, 'tool', 's', 0.5)
    fl.record('bad', {'status': 'error'}, 'tool', 's', 3.0)
    st = fl.get_stats()
    assert st['total'] >= 6 and 'success_rate' in st
    assert isinstance(fl.suggest_improvements(), list)
    assert isinstance(fl.get_failing_patterns(), list)
t('FeedbackLoop', t6)

# 7. MultiAgent routing (10 cases)
def t7():
    from multi_agent import orchestrator
    cases = [
        ('elementor landing page design', 'creative'),
        ('update plugin woocommerce',     'technical'),
        ('create course Python Basics',   'educator'),
        ('fix php fatal error',           'technical'),
        ('change header color blue',      'creative'),
        ('enroll student in course',      'educator'),
        ('wp-cli cache flush',            'technical'),
        ('learndash quiz',                'educator'),
        ('banner elementor section',      'creative'),
        ('mysql database backup',         'technical'),
    ]
    ok = sum(1 for task, exp in cases if orchestrator.route(task) == exp)
    assert ok >= 8, f'Routing {ok}/10 — need >=8'
    print(f'   routing: {ok}/10')
    st = orchestrator.status()
    assert len(st) == 3 and all(r in st for r in ('creative','technical','educator'))
t('MultiAgent routing', t7)

# 8. AgentCore firewall all categories
def t8():
    from agent_core import AgentCore
    a = AgentCore()
    cases = [
        ('Fatal error in plugins/x',  'plugin_conflict'),
        ('PHP out of memory',          'memory_limit'),
        ('MySQL connection error',     'database_error'),
        ('permission denied',          'permission_error'),
        ('connection timed out',       'timeout'),
        ('some unknown error',         'unknown'),
    ]
    for err, expected in cases:
        got = a.firewall.analyze_error(err)['category']
        assert got == expected, f'{err!r}: got {got}, expected {expected}'
    a.wp_manager.add_site('s', 'https://s.com', 'k')
    r = a.execute_on_all_sites('ping')
    assert isinstance(r, dict)
t('AgentCore + Firewall', t8)

# 9. server.py completeness
def t9():
    import ast
    src = open('server.py', encoding='utf-8', errors='replace').read()
    required = [
        'WordPress Integration Layer', 'register_blueprint',
        '/run', '/system/status', '/wp-dashboard',
        'knowledge_upload', 'configure_llm',
        'Health Monitor + Sites Store', '/health',
    ]
    missing = [r for r in required if r not in src]
    assert not missing, 'server.py: ' + str(missing)
    ast.parse(src)
    print('   server.py syntax OK + all routes')
t('server.py complete', t9)

# 10. wp_routes all endpoints
def t10():
    src = open('wp_routes.py', encoding='utf-8', errors='replace').read()
    eps = [
        '/register-site', '/site-info', '/sites-status',
        '/plugins', '/update-plugins', '/toggle-plugin',
        '/elementor-get', '/elementor-set',
        '/courses', '/create-course',
        '/analyze', '/auto-heal', '/error-log',
        '/agents/status', '/agents/run', '/agents/route',
        '/knowledge/search', '/knowledge/learn-url',
        '/llm/config', '/llm/think',
        '/feedback', '/knowledge',
        '/sites', '/sites/delete', '/health', '/health/all',
        '/export-data', '/run-cli',
    ]
    missing = [e for e in eps if e not in src]
    assert not missing, 'wp_routes missing: ' + str(missing)
    print(f'   {len(eps)} endpoints OK')
t('wp_routes endpoints', t10)

# 11. WordPress Plugin
def t11():
    base = 'wordpress-plugin/ai-wordpress-agent'
    checks = {
        'ai-wordpress-agent.php':            ['register_with_agent','AIWA_VERSION'],
        'includes/class-aiwa-api.php':       ['elementor-data','learndash-courses','run-cli'],
        'includes/class-aiwa-heartbeat.php': ['send_heartbeat'],
        'includes/class-aiwa-selfheal.php':  ['heal','detect_plugin','disable_plugin'],
        'admin/class-aiwa-dashboard.php':    ['register_menu','render_main'],
    }
    for fname, kws in checks.items():
        p = os.path.join(base, fname)
        assert os.path.exists(p), fname + ' missing'
        c = open(p, encoding='utf-8', errors='replace').read()
        miss = [k for k in kws if k not in c]
        assert not miss, f'{fname} missing: {miss}'
t('WordPress Plugin', t11)

# 12. Chrome Extension
def t12():
    ext = 'chrome-extension'
    sizes = {'manifest.json':100,'background.js':500,'content.js':2000,'popup.html':5000}
    for f, minsize in sizes.items():
        p = os.path.join(ext, f)
        assert os.path.exists(p) and os.path.getsize(p) >= minsize, f + ' too small'
    bg = open(os.path.join(ext,'background.js'), encoding='utf-8', errors='replace').read()
    for k in ['RUN_TASK','SYSTEM_STATUS','REGISTER_SITE','LEARN_URL']:
        assert k in bg, k + ' missing in bg.js'
    ct = open(os.path.join(ext,'content.js'), encoding='utf-8', errors='replace').read()
    for k in ['analyzePage','execCommand','showOverlay','detectPageType']:
        assert k in ct, k + ' missing in content.js'
    pp = open(os.path.join(ext,'popup.html'), encoding='utf-8', errors='replace').read()
    for k in ['runTask','saveLLMConfig','loadSystemStatus','addSite']:
        assert k in pp, k + ' missing in popup.html'
t('Chrome Extension', t12)

# 13. Dashboard live wiring
def t13():
    html = open('templates/wp-dashboard.html', encoding='utf-8', errors='replace').read()
    checks = [
        'startLivePolling','pollSystemStatus','updateToolsPanel',
        'updateFeedbackPanel','updateLLMStatus','saveLLMConfig',
        'updateSitesFromAwareness','tools-panel','fb-total',
        'llm-provider','sys-uptime','sys-tasks','site-latency',
        'llm-provider-sel','POLL_INTERVAL','setGlobalStatus','formatUptime',
    ]
    miss = [c for c in checks if c not in html]
    assert not miss, 'Dashboard: ' + str(miss)
    print(f'   {len(checks)} dashboard features OK')
t('Dashboard live wiring', t13)

# 14. All 11 modules import
def t14():
    mods = [
        'tool_registry','system_awareness','llm_bridge','feedback_loop',
        'knowledge_manager','wp_manager','wp_routes','multi_agent',
        'agent_core','health_monitor','sites_store',
    ]
    for m in mods:
        mod = __import__(m)
        assert mod, m + ' import returned None'
    print(f'   {len(mods)} modules imported OK')
t('All 11 modules import', t14)

# Summary
print()
print('='*54)
print(f'PASSED: {len(P)}/{len(P)+len(F)}')
if F:
    print(f'FAILED: {len(F)}')
    for n, e in F:
        print(f'  - {n}: {e}')
else:
    print('ALL 14 TESTS PASSED')
print('='*54)
