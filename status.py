"""status.py — called by launcher.bat to print live system status"""
import sys, os, urllib.request, json
sys.path.insert(0, r'C:\mcp-agent')

BASE = 'http://127.0.0.1:5001'

def ping(path, timeout=3):
    try:
        r = urllib.request.urlopen(BASE + path, timeout=timeout)
        return json.loads(r.read())
    except Exception:
        return None

# REST health
hc = ping('/healthz')
print('  REST Server     :', 'OK  (port 5001)' if hc else 'STARTING...')

# System status
st = ping('/system/status')
if st:
    aw = st.get('awareness', {})
    kb = st.get('knowledge', {})
    lm = st.get('llm', {})
    tools = st.get('tools_health', {})
    print('  Sites connected :', len(aw.get('connected_sites', [])))
    print('  Knowledge docs  :', kb.get('total', 0))
    print('  LLM Provider    :', lm.get('provider', 'mock'))
    print('  Tools active    :', tools.get('idle', 0), '/', tools.get('total', 0))
    print('  Tasks done      :', aw.get('tasks_done', 0))
else:
    print('  System status   : loading...')

# Health
hm = ping('/health')
if hm:
    print('  Monitored sites :', hm.get('total_sites', 0))
    print('  Auto-Heal       :', 'ON' if hm.get('auto_heal_on') else 'OFF')
