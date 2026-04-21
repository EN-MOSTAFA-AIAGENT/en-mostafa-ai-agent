import json, urllib.request

KEY  = 'ocJBiEVpiWse4v3LFu2i94DrwglmAP4G'
BASE = 'https://askmbt.com/wp-json/ai-agent/v1'

# جرب مسح الـ cache عبر LiteSpeed API
def post(path, body):
    data = json.dumps(body).encode()
    req  = urllib.request.Request(
        BASE + path, data=data,
        headers={'X-AI-Agent-Key': KEY, 'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        r = urllib.request.urlopen(req, timeout=15)
        return json.loads(r.read())
    except Exception as e:
        return {'error': str(e)}

# تحديث الـ plugin لإضافة cache-clear endpoint
# استخدام LiteSpeed purge action
php_snippet = """<?php
// Clear LiteSpeed Cache
if (class_exists('LiteSpeed\\Core')) {
    do_action('litespeed_purge_all');
    echo json_encode(['cleared' => true, 'method' => 'litespeed']);
} elseif (function_exists('wp_cache_flush')) {
    wp_cache_flush();
    echo json_encode(['cleared' => true, 'method' => 'wp_cache_flush']);
} else {
    echo json_encode(['cleared' => false, 'reason' => 'no cache plugin found']);
}
"""

# نحاول نشغل PHP snippet عبر الـ API
result = post('/run-cli', {
    'command': 'litespeed-purge all',
    'use_php': True,
    'php': php_snippet
})
print("Cache clear result:", result)

# البديل: مسح الـ transient
result2 = post('/run-cli', {
    'command': 'transient delete --all'
})
print("Transient result:", result2)
