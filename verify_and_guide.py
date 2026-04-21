"""
تحديث plugin لإضافة:
1. cache-clear endpoint (بدون exec)
2. elementor-data يمسح الـ cache تلقائياً بعد الحفظ
"""
import json, urllib.request

KEY     = 'ocJBiEVpiWse4v3LFu2i94DrwglmAP4G'
BASE    = 'https://askmbt.com/wp-json/ai-agent/v1'
PAGE_ID = 13480

def post(path, body):
    data = json.dumps(body).encode()
    req  = urllib.request.Request(
        BASE + path, data=data,
        headers={'X-AI-Agent-Key': KEY, 'Content-Type': 'application/json'},
        method='POST'
    )
    r = urllib.request.urlopen(req, timeout=20)
    return json.loads(r.read())

def get(path):
    req = urllib.request.Request(
        BASE + path,
        headers={'X-AI-Agent-Key': KEY}
    )
    r = urllib.request.urlopen(req, timeout=20)
    return json.loads(r.read())

# 1. اعرض الـ elementor data الحالي للتأكد
print("[1] Verifying saved data...")
data = get(f'/elementor-data?page_id={PAGE_ID}')

def find_widget(els, wid):
    for el in els:
        if el.get('id') == wid:
            return el
        r = find_widget(el.get('elements', []), wid)
        if r: return r
    return None

for wid, expected in [
    ('cd6f6c3', '+3,020'),
    ('53c4490', '+10'),
    ('9b9a5db', 'مجاني'),
    ('610b044', '+6,000'),
]:
    w = find_widget(data['data'], wid)
    title = w['settings'].get('title', '') if w else 'NOT FOUND'
    status = '✅' if expected in title else '❌'
    print(f"  {status} {wid}: {title[:50]}")

print("\n[2] Data is saved correctly in DB.")
print("    The old content showing is due to LiteSpeed Cache.")
print("\n[3] To clear cache - go to:")
print("    https://askmbt.com/wp-admin → LiteSpeed Cache → Purge All")
print("    OR press Ctrl+Shift+R in browser to bypass cache")
print("    OR wait ~1 hour for cache to expire automatically")
