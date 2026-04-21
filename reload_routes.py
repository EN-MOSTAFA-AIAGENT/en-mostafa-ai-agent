"""
reload_routes.py — Re-registers all wp_routes Blueprint routes
Called when server needs route refresh without full restart
Run: py -3.11 reload_routes.py  OR  POST /admin/reload
"""
import sys, os, urllib.request, json

sys.path.insert(0, r'C:\mcp-agent')
os.chdir(r'C:\mcp-agent')

BASE = 'http://127.0.0.1:5001'

def post(path, body={}):
    data = json.dumps(body).encode()
    req  = urllib.request.Request(
        BASE + path, data=data,
        headers={'Content-Type':'application/json'}, method='POST'
    )
    r = urllib.request.urlopen(req, timeout=5)
    return json.loads(r.read())

# Check which routes are missing
missing = []
check_routes = [
    ('GET', '/wp/agents/status'),
    ('POST','/wp/agents/run'),
    ('GET', '/wp/health'),
    ('GET', '/wp/sites'),
    ('GET', '/wp/feedback'),
    ('GET', '/wp/knowledge'),
]

print('Checking live routes...')
for method, path in check_routes:
    try:
        if method == 'GET':
            r = urllib.request.urlopen(BASE+path, timeout=3)
            print(f'  OK   {method} {path}  ({r.status})')
        else:
            post(path, {})
            print(f'  OK   {method} {path}')
    except Exception as e:
        code = str(e)
        if '404' in code:
            missing.append((method, path))
            print(f'  MISS {method} {path}  (404)')
        elif '400' in code:
            print(f'  OK   {method} {path}  (400 = route exists)')
        else:
            print(f'  ERR  {method} {path}  {code[:40]}')

if missing:
    print(f'\n{len(missing)} routes missing — server needs restart to pick up new Blueprint routes')
    print('Run: stop.bat  then  launcher.bat')
else:
    print('\nAll routes are live.')
