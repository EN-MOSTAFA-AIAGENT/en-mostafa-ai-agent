"""Final comprehensive test — run with py -3.11 final_test.py"""
import sys, os
sys.path.insert(0, r'C:\mcp-agent')
os.chdir(r'C:\mcp-agent')

P = []; F = []

def test(n, fn):
    try:
        fn(); P.append(n); print('PASS', n)
    except Exception as e:
        F.append((n, str(e)[:100])); print('FAIL', n, ':', str(e)[:100])

def t1():
    from tool_registry import ToolRegistry, ToolType
    r = ToolRegistry()
    r.register('x', ToolType.MEMORY, object(), '', 1)
    assert r.get('x') and r.health_check()['healthy']
test('ToolRegistry', t1)

def t2():
    from system_awareness import SystemAwareness, ConnectionState
    sa = SystemAwareness()
    sa.begin_task('t', 'mem', 's1')
    sa.register_site('s1', 'https://x.com')
    sa.update_site_ping('s1', True, 42.0, {'wp_version':'6.5','plugins_active':10})
    assert sa.get_all_sites()[0]['connection'] == ConnectionState.CONNECTED
    sa.end_task(True)
    assert sa.get_snapshot()['tasks_done'] == 1
test('SystemAwareness', t2)

def t3():
    from llm_bridge import LLMBridge
    b = LLMBridge()
    r = b.think('update plugins', {}, '')
    assert 'task' in r and 'plan' in r
    assert b.analyze_error('fatal') is not None
test('LLMBridge', t3)

def t4():
    from feedback_loop import FeedbackLoop
    fl = FeedbackLoop()
    r1 = fl.record('ok-task',   {'status':'completed'}, 'tool', 's', 0.5)
    r2 = fl.record('fail-task', {'status':'error'},     'tool', 's', 1.0)
    assert r1.success and not r2.success
    assert fl.get_stats()['total'] >= 2
    assert isinstance(fl.suggest_improvements(), list)
test('FeedbackLoop', t4)

def t5():
    from knowledge_manager import KnowledgeManager
    km = KnowledgeManager()
    km.learn_from_text('WordPress hooks and filters tutorial', title='wp', tags=['wp'])
    assert 'has_knowledge' in km.search_for_task('plugin hooks')
    assert 'total' in km.get_stats()
test('KnowledgeManager', t5)

def t6():
    from wp_manager import WPManager, WordPressSite
    wm = WPManager()
    s  = wm.add_site('demo', 'https://demo.test', 'key123')
    assert isinstance(s, WordPressSite)
    assert wm.get_site('demo') is not None
    assert len(wm.get_all_sites()) >= 1
test('WPManager', t6)

def t7():
    from agent_core import AgentCore
    a  = AgentCore()
    il = a.integration
    assert il.route_to_agent('elementor design') == 'creative'
    assert il.route_to_agent('learndash course') == 'educator'
    assert il.route_to_agent('update plugins')   == 'technical'
    assert il._predict_risk('rm -rf /') == 'HIGH'
    assert il._predict_risk('echo hi')  == 'LOW'
    fw = a.firewall
    assert fw.analyze_error('Fatal error in plugins/x')['category'] == 'plugin_conflict'
    assert fw.analyze_error('out of memory')['category']            == 'memory_limit'
    assert fw.analyze_error('MySQL error')['category']              == 'database_error'
    plan = [{'step':'s1','command':'echo ok'}]
    exp  = a.explainer.explain('my task', plan, {'has_knowledge':False,'count':0,'results':[]})
    assert 'my task' in exp
test('AgentCore', t7)

def t8():
    from multi_agent import orchestrator
    cases = [
        ('design elementor page',  'creative'),
        ('update all plugins',     'technical'),
        ('create learndash course','educator'),
        ('fix plugin error',       'technical'),
        ('elementor header',       'creative'),
        ('list courses',           'educator'),
        ('wp-cli db optimize',     'technical'),
    ]
    ok = sum(1 for t,e in cases if orchestrator.route(t)==e)
    assert ok >= 6, f'Only {ok}/7 routes correct'
    st = orchestrator.status()
    assert len(st) == 3
    for role in ('creative','technical','educator'):
        assert role in st and not st[role]['busy']
test('MultiAgent routing', t8)

def t9():
    src = open('server.py', encoding='utf-8', errors='replace').read()
    for kw in ['WordPress Integration Layer','register_blueprint','/run',
               '/system/status','/wp-dashboard','knowledge_upload',
               'configure_llm','_get_agent','feedback_loop','system_awareness']:
        assert kw in src, 'Missing: '+kw
test('server.py completeness', t9)

def t10():
    base = 'chrome-extension'
    for fname, minsize in [('manifest.json',20),('background.js',500),
                            ('content.js',2000),('popup.html',5000)]:
        p = os.path.join(base, fname)
        assert os.path.exists(p) and os.path.getsize(p) >= minsize, 'Bad: '+fname
    bg = open(os.path.join(base,'background.js')).read()
    for kw in ['RUN_TASK','SYSTEM_STATUS','REGISTER_SITE']:
        assert kw in bg, kw+' missing in background.js'
    ct = open(os.path.join(base,'content.js')).read()
    for kw in ['analyzePage','execCommand','showOverlay']:
        assert kw in ct, kw+' missing in content.js'
    pp = open(os.path.join(base,'popup.html')).read()
    for kw in ['runTask','saveLLMConfig','loadSystemStatus']:
        assert kw in pp, kw+' missing in popup.html'
test('Chrome Extension', t10)

def t11():
    base = r'wordpress-plugin\ai-wordpress-agent'
    checks = {
        'ai-wordpress-agent.php':            ['register_with_agent','AIWA_VERSION'],
        'includes/class-aiwa-api.php':       ['elementor-data','learndash-courses','run-cli'],
        'includes/class-aiwa-heartbeat.php': ['send_heartbeat'],
        'includes/class-aiwa-selfheal.php':  ['heal','detect_plugin'],
        'admin/class-aiwa-dashboard.php':    ['register_menu','render_main'],
    }
    for fname, kws in checks.items():
        p = os.path.join(base, fname)
        assert os.path.exists(p), fname+' missing'
        c = open(p, encoding='utf-8', errors='replace').read()
        for kw in kws:
            assert kw in c, f'{fname}: missing {kw}'
test('WordPress Plugin', t11)

def t12():
    html = open(r'templates\wp-dashboard.html', encoding='utf-8').read()
    for kw in ['startLivePolling','pollSystemStatus','updateToolsPanel',
               'updateFeedbackPanel','updateLLMStatus','saveLLMConfig',
               'updateSitesFromAwareness','tools-panel','fb-total',
               'llm-provider','sys-uptime','site-latency']:
        assert kw in html, 'Missing in dashboard: '+kw
test('Dashboard live wiring', t12)

# Summary
print()
print('='*55)
print(f'PASSED : {len(P)}/{len(P)+len(F)}')
if F:
    for n,e in F: print(f'  FAIL {n}: {e}')
else:
    print('ALL TESTS PASSED')
print('='*55)
