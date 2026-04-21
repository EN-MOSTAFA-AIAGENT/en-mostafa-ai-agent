import json, urllib.request

KEY     = 'ocJBiEVpiWse4v3LFu2i94DrwglmAP4G'
BASE    = 'https://askmbt.com/wp-json/ai-agent/v1'
PAGE_ID = 13480

# التعديلات: widget_id → title جديدة
UPDATES = {
    'cd6f6c3': '+3,020 <br> اختبار معياري',
    '53c4490': '+10 <br> دولة عربية',
    '9b9a5db': 'مجاني <br> ديمو تجريبي',
    '610b044': '+6,000 <br> مدرسة شريكة',
}

def update_widget(elements, wid, new_title):
    for el in elements:
        if el.get('id') == wid:
            old = el['settings'].get('title', '')
            el['settings']['title'] = new_title
            print(f"  ✅ {wid}: [{old}] → [{new_title}]")
            return True
        if update_widget(el.get('elements', []), wid, new_title):
            return True
    return False

# جلب البيانات
req = urllib.request.Request(
    f"{BASE}/elementor-data?page_id={PAGE_ID}",
    headers={'X-AI-Agent-Key': KEY}
)
data = json.loads(urllib.request.urlopen(req, timeout=20).read())
elements = data['data']
print("✅ Fetched Elementor data")

# تطبيق التعديلات
for wid, title in UPDATES.items():
    if not update_widget(elements, wid, title):
        print(f"  ❌ Widget {wid} not found!")

# حفظ التعديلات
body = json.dumps({"page_id": PAGE_ID, "data": elements}).encode()
req2 = urllib.request.Request(
    f"{BASE}/elementor-data",
    data=body,
    headers={'X-AI-Agent-Key': KEY, 'Content-Type': 'application/json'},
    method='POST'
)
result = json.loads(urllib.request.urlopen(req2, timeout=20).read())
print("\n📤 Save result:", result)
