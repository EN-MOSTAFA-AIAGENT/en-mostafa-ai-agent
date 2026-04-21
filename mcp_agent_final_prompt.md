# البرومبت النهائي الشامل — EN MOSTAFA AI AGENT v6.0

> انسخ محتوى هذا الملف كاملًا وألصقه في محادثة مع `EN MOSTAFA AI AGENT`. صُمِّم ليعمل على دفعات مستقلة، كل دفعة قابلة للتحقق، ولن تكسر ما يعمل حاليًا.

---

## 🎯 الهدف العام

ترقية شاملة لنظام WordPress Control Center ليكون:
1. **آمنًا**: بلا إصلاحات تلقائية خطرة
2. **مربوطًا**: كل زر في الداشبورد يُحرّك محركًا حقيقيًا (لا بيانات وهمية)
3. **ذكيًا**: Claude/ChatGPT يستخدمان Tools حقيقية (Anthropic tool-use) بدل مولّد نصوص
4. **احترافيًا**: داشبورد بأسلوب WordPress Admin (معلومات حقيقية، Live Status، تبويبات واضحة)
5. **شاملًا**: MasterStudy كامل مع موارد (PDF/URL/Videos) + Hostinger API مربوط

---

## ⚠️ قواعد صارمة قبل أي تعديل

- لا تحذف أي ملف. لكل ملف تُعدّله: أنشئ نسخة `{file}.bak` قبل أول تعديل في الجلسة.
- بعد كل **مهمة** (وليس بعد كل دفعة): شغّل اختبار القبول المذكور وأرسل النتيجة قبل التالي.
- إذا فشل اختبار: توقّف، أرسل الخطأ + آخر 30 سطر من `C:\mcp-agent\mcp.log` و`flask.log`، واطلب إذن المتابعة.
- لا تُعد كتابة نظام موجود إن كان يعمل. أضِف/عدّل بأقل تغيير ممكن.
- استخدم `execute_shell` لتشغيل اختبارات `curl` محليًا بدل تخمين النتائج.

---

## 🔍 التشخيص المُثبَت (لا تُناقشه، ابدأ منه)

1. ملفات "العقل" كلها stubs: `agent_brain.py` (4 intents keyword)، `decision_engine.py` (IF واحد)، `strategy_engine.py`، `pattern_engine.py`، `planning_graph.py`، `state_manager.py`، `dynamic_rules.py`. المنطق الحقيقي موجود في `ai_operator.py` فقط.
2. `llm_bridge` = مولّد نصوص بلا tool-use. `LLM_PROVIDER` الافتراضي = `mock`.
3. `wp_routes.py` يستورد singletons غير موجودة (`agent_brain`, `decision_engine`, `memory_engine`, `strategy_engine`, `pattern_engine`) ⇒ `SMART_SYSTEM_READY = False` دائمًا، وكل فروع `if SMART_SYSTEM_READY` شفرة ميتة.
4. ازدواجية في نقاط الدخول: الداشبورد يستخدم `/run` (agent_core → stub brain)، بينما المحرك الحقيقي خلف `/wp/operator/run`.
5. `multi_agent.orchestrator` مكتوب بالكامل لكن لا يُستدعى من أي route.
6. `tool_registry` يُسجَّل في `server.py` لكن `choose_best_tool` لا يُستدعى من أي مسار تنفيذ.
7. `ai_operator.auto_fix_errors` يشغّل `plugin deactivate --all --skip-plugins` بمجرد ظهور كلمة "plugin" في التشخيص — خطر جسيم.
8. `ai_operator.analyze_update_risk` منطق مقلوب: يعتبر Yoast/Elementor/WooCommerce "risky" والمجهولة "safe".
9. `knowledge_manager.search_for_task` يعمل، لكن نتائجه لا تُحقن في أي LLM prompt داخل `ai_operator`.
10. `memory_engine` لا يُستشار قبل التنفيذ في `ai_operator`.
11. `wp_manager.WordPressSite` ينادي endpoints غير موجودة:
    - `delete_user` → `"manage-users"` (الصحيح: `"users/delete"`)
    - `create_user` → `"manage-users"` (الصحيح: `"users/create"`)
    - `create_course` → `"learndash-courses"` (غير موجود — LearnDash مجرد PHP stub)
    - `get_media`, `import_xml`, `export_data` → غير موجودة
12. `chrome-extension/background.js` ينادي `/wp/register-site` (الصحيح: `/wp/add-site`) و`/wp/knowledge/learn-url` (غير موجود).
13. MasterStudy PHP endpoints موجودة وتعمل. المشكلة في ربط `wp_manager.create_course`.
14. `class-aiwa-selfheal.php` يعطّل Plugins تلقائيًا عند E_ERROR — خطر في production.
15. `/wp/auto-heal` يرجع تقرير صحة فقط ولا يُصلح شيئًا.
16. الداشبورد الحالي: الـ cards تعرض labels فارغة، Active Tools كلها `0 calls` لأن لا أحد يستدعيها، Performance stats مفيدة لكن لا يوجد Real Site Metrics، Self-Heal زرّ فقط بلا إصلاح حقيقي.

---

# ═══════════════════════════════════════
# 🗂️ خريطة الدفعات (الترتيب إلزامي)
# ═══════════════════════════════════════

| الدفعة | المحتوى | الأولوية |
|---|---|---|
| **A** | Backup + إصلاحات السلامة الحرجة | ⚠️ عاجل |
| **B** | ربط plumbing المكسور (endpoints، imports) | 🔧 أساس |
| **C** | حقن Knowledge + Memory في `ai_operator` | 🧠 ذكاء |
| **D** | Tool-use حقيقي لـ Claude/ChatGPT | 🚀 نقلة نوعية |
| **E** | توحيد نقاط الدخول + Self-Heal آمن | 🛡️ استقرار |
| **F** | إعادة بناء الداشبورد بأسلوب WP-Admin | 🎨 واجهة |
| **G** | MasterStudy كامل مع موارد PDF/URL | 🎓 LMS |
| **H** | تكامل Hostinger API | 🌐 استضافة |

---

# ═══════════════════════════════════════
# ═══ دفعة A — إصلاحات السلامة ═══
# ═══════════════════════════════════════

### 📌 المهمة A1: Backup شامل

```powershell
Compress-Archive -Path C:\mcp-agent\*.py, C:\mcp-agent\templates, C:\mcp-agent\wordpress-plugin, C:\mcp-agent\chrome-extension -DestinationPath "$env:USERPROFILE\Desktop\mcp_backup_$(Get-Date -Format yyyyMMdd_HHmmss).zip" -Force
```

✅ **اختبار**: الـ zip موجود على Desktop بحجم > 500KB.

### 📌 المهمة A2: تحييد `auto_fix_errors` الخطير

في `C:\mcp-agent\ai_operator.py`، داخل `_execute_step` عند `fn == "auto_fix_errors"`:
- احذف كل سطور `site.run_cli("plugin deactivate --all --skip-plugins")` و`site.run_cli("cache flush")`.
- استبدل بإرجاع:
```python
return {
    "ok": True,
    "mode": "suggested_only",
    "diagnosis": diag,
    "requires_confirmation": True,
    "suggested_actions": self._extract_suggested_actions(diag),
    "warning": "لن يُنفَّذ أي إصلاح تلقائيًا. استخدم /wp/selfheal/apply مع confirm=true"
}
```
- أضف دالة helper `_extract_suggested_actions(diag)` ترجع list من dicts: `[{"action":"...","severity":"low|medium|high","command":"..."}]`.

✅ **اختبار**:
```bash
curl -X POST http://127.0.0.1:5001/wp/operator/run \
  -H "Content-Type: application/json" \
  -d '{"task":"حلّل أخطاء الموقع","site":"mbt"}'
```
يجب ألّا يُعطَّل أي plugin فعليًا. تحقّق بـ `wp plugin list` أو عبر الواجهة.

### 📌 المهمة A3: قلب منطق `analyze_update_risk`

في `ai_operator.py` داخل `fn == "analyze_update_risk"`:

```python
KNOWN_SAFE_PLUGINS = [
    "yoast-seo", "rank-math", "elementor", "elementor-pro",
    "woocommerce", "contact-form-7", "wordfence", "akismet",
    "jetpack", "classic-editor", "wp-super-cache", "w3-total-cache",
    "updraftplus", "redirection", "all-in-one-seo", "wpforms",
    "advanced-custom-fields", "query-monitor", "user-role-editor",
    "duplicate-post", "mailpoet", "masterstudy-lms"
]

def _is_known_safe(name: str) -> bool:
    n = (name or "").lower().replace(" ", "-")
    return any(safe in n for safe in KNOWN_SAFE_PLUGINS)
```

بدّل منطق التصنيف:
- `plugin ∈ KNOWN_SAFE_PLUGINS` → `safe`
- وإلا → `risky` (مجهول ⇒ اختبره على staging أولًا)

✅ **اختبار**: `/wp/operator/run` بمهمة "حدّث الإضافات بأمان" يجب أن يضع Elementor و WooCommerce في `safe` لا `risky`.

---

# ═══════════════════════════════════════
# ═══ دفعة B — ربط الـ plumbing ═══
# ═══════════════════════════════════════

### 📌 المهمة B1: إصلاح استيرادات `wp_routes.py` الوهمية

في `wp_routes.py` السطور 7-14:
- احذف كتلة `try/except ImportError` بالكامل (الاستيرادات الستة).
- اضبط `SMART_SYSTEM_READY = False` صراحةً.
- احذف كل كتل `if SMART_SYSTEM_READY:` من الملف (4 مواضع: `add_site`, `site_info`, `get_plugins`, `manage_users`, `run_ai_task`).
- استبدل `/wp/ai-task` endpoint بحيث يستدعي `ai_operator.execute` بدل `agent_brain.execute_autonomous_task` (غير موجود أصلًا):

```python
@wp_bp.route("/ai-task", methods=["POST"])
def run_ai_task():
    from ai_operator import ai_operator
    data = request.json or {}
    prompt = data.get("prompt", "")
    site_name = data.get("site")
    site = wp_manager.get_site(site_name) if site_name else None
    result = ai_operator.execute(prompt, site=site)
    return jsonify({"success": True, "result": result})
```

✅ **اختبار**: `POST /wp/ai-task` بـ `{"prompt":"ping","site":"mbt"}` يرجع 200 (لا 503).

### 📌 المهمة B2: تصحيح مسارات `wp_manager.WordPressSite`

في `wp_manager.py`:
- `create_user`: غيّر `"manage-users"` → `"users/create"`، body: `{"username", "email", "password", "role"}`.
- `delete_user`: غيّر `"manage-users"` → `"users/delete"`.
- احذف `get_media`, `import_xml`, `export_data` (غير موجودة في PHP).
- `get_courses`: غيّر `"learndash-courses"` → `"masterstudy/courses"`.
- `create_course`: غيّر `"learndash-courses"` → `"masterstudy/courses"` ، body: `{"title", "description", "price", "status", "level"}`.

✅ **اختبار**:
```bash
curl -X POST http://127.0.0.1:5001/wp/create-course \
  -H "Content-Type: application/json" \
  -d '{"site":"mbt","title":"اختبار الربط","content":"وصف تجريبي"}'
```
يجب أن ينشئ كورسًا حقيقيًا (تحقّق بعدها بـ `GET /wp/masterstudy/ai-create` أو بتسجيل الدخول إلى WP).

### 📌 المهمة B3: توحيد `/run` و `/wp/operator/run`

في `server.py` داخل `run_task()` (السطر ~1660):
```python
@app.route("/run", methods=["POST"])
def run_task():
    from ai_operator import ai_operator
    data = request.get_json(force=True) or {}
    task = data.get("task", "")
    site_name = data.get("site")
    explain = data.get("explain", False)
    if not task:
        return jsonify({"error": "task required"}), 400
    try:
        site = wp_manager.get_site(site_name) if site_name else None
        result = ai_operator.execute(task, site=site, explain=explain)
        return jsonify(result if isinstance(result, dict) else {"result": result, "success": True})
    except Exception as e:
        logger.exception("run_task failed")
        return jsonify({"error": str(e), "status": "failed"}), 500
```
(احذف استدعاءات `agent_core.handle_task` القديمة.)

✅ **اختبار**: `POST /run` بـ `{"task":"info","site":"mbt"}` يرجع نفس هيكل `/wp/operator/run`.

### 📌 المهمة B4: إصلاح Chrome Extension

في `C:\mcp-agent\chrome-extension\background.js`:
- غيّر `/wp/register-site` → `/wp/add-site`.
- احذف handler `LEARN_URL` بالكامل (أو استبدله بـ `POST /knowledge/upload` باستخدام FormData).

✅ **اختبار**: افتح الإكستنشن، جرّب Add Site، يجب أن ينجح.

---

# ═══════════════════════════════════════
# ═══ دفعة C — حقن Knowledge + Memory ═══
# ═══════════════════════════════════════

### 📌 المهمة C1: حقن Knowledge في LLM prompts

في `ai_operator.py`:
- في بداية `execute()` بعد `intent = self._analyze_intent(task)`:
```python
from knowledge_manager import knowledge_manager
knowledge = knowledge_manager.search_for_task(task)
self._knowledge_context = knowledge.get("summary", "")
self._knowledge_count = knowledge.get("count", 0)
```
- أضف دالة helper:
```python
def _wrap_prompt(self, prompt: str) -> str:
    ctx = getattr(self, "_knowledge_context", "")
    if ctx:
        return f"=== سياق معرفي متوفر ===\n{ctx}\n\n=== المهمة ===\n{prompt}"
    return prompt
```
- استبدل كل `llm_bridge._call_llm(prompt)` داخل `_execute_step` بـ `llm_bridge._call_llm(self._wrap_prompt(prompt))` (4 مواضع: `ai_site_analysis`, `ai_elementor_suggest`, `ms_generate_structure`, `ai_diagnose_errors`, `general_ai_task`).
- في النتيجة النهائية لـ `execute()` أضف: `"knowledge_used": self._knowledge_count`.

✅ **اختبار**: ارفع عبر `/knowledge/upload` ملف TXT فيه نصوص عن Elementor، ثم `/wp/operator/run` بمهمة "حلل Elementor في الموقع". يجب أن يكون `knowledge_used >= 1` في النتيجة.

### 📌 المهمة C2: حقن Memory قبل التنفيذ

في `ai_operator.py`:
- في أعلى الملف:
```python
from memory_engine import MemoryEngine
_memory = MemoryEngine()
```
- في بداية `execute()` بعد Knowledge search:
```python
similar = _memory.find_similar(task)[:3]
if similar:
    mem_summary = "محاولات مشابهة سابقة:\n" + "\n".join([
        f"- {s['command'][:80]} | {'نجح' if s['success'] else 'فشل'} | {s['duration']:.1f}s"
        for s in similar
    ])
    self._knowledge_context = (self._knowledge_context + "\n\n" + mem_summary).strip()
```
- في نهاية `execute()` (قبل return):
```python
try:
    _memory.save_execution(task, success, duration, 
                          error=None if success else str(results))
except Exception:
    pass
```

✅ **اختبار**: شغّل نفس المهمة مرتين. المرة الثانية يجب أن يظهر في `self._knowledge_context` نص "محاولات مشابهة سابقة".

### 📌 المهمة C3: تمكين LLM حقيقي + تنبيهات Mock

- أضف endpoint في `server.py`:
```python
@app.route("/llm/status", methods=["GET"])
def llm_status():
    cfg = llm_bridge.get_config()
    return jsonify({
        "provider": cfg["provider"],
        "model": cfg["model"],
        "has_key": cfg["has_key"],
        "is_mock": cfg["provider"] == "mock",
        "warning": "LLM في وضع Mock — الذكاء غير فعّال. اضبط LLM_PROVIDER و LLM_API_KEY." if cfg["provider"] == "mock" else None
    })
```

✅ **اختبار**: `GET /llm/status` يرجع JSON صحيح مع `is_mock: true/false`.

---

# ═══════════════════════════════════════
# ═══ دفعة D — Tool-Use للـ LLM ═══
# ═══ (النقلة النوعية — الأهم) ═══
# ═══════════════════════════════════════

### 📌 المهمة D1: إنشاء `llm_tools.py`

أنشئ `C:\mcp-agent\llm_tools.py`:

```python
"""
LLM Tool Definitions + Executor
تُمكّن Claude/ChatGPT من استدعاء أدوات فعلية بدل توليد نصوص فقط.
"""
import json
from logger_system import get_logger
logger = get_logger("llm_tools")

# Anthropic tool schema — يعمل مباشرة مع Claude API
# لـ OpenAI: نفس الـ schemas بعد تحويل بسيط في llm_bridge
LLM_TOOLS = [
    {
        "name": "get_site_info",
        "description": "Retrieve WordPress site info: WP version, PHP version, theme, plugins count, memory, admin email. Use when user asks about site status, health, or details.",
        "input_schema": {
            "type": "object",
            "properties": {"site": {"type": "string", "description": "Site name as registered in WPManager"}},
            "required": ["site"]
        }
    },
    {
        "name": "list_plugins",
        "description": "List all plugins on a WordPress site with active status, version, and update availability.",
        "input_schema": {
            "type": "object",
            "properties": {"site": {"type": "string"}},
            "required": ["site"]
        }
    },
    {
        "name": "get_error_log",
        "description": "Read the last 10KB of WordPress debug.log. Returns log text, size, and has_fatal flag.",
        "input_schema": {
            "type": "object",
            "properties": {"site": {"type": "string"}},
            "required": ["site"]
        }
    },
    {
        "name": "run_wp_cli",
        "description": "Run a READ-ONLY wp-cli command. BLOCKED commands: delete, deactivate --all, drop, truncate, rm, uninstall, install --activate. Use for: cache flush (read-only variants), option get, user list, post list, core check-update.",
        "input_schema": {
            "type": "object",
            "properties": {
                "site": {"type": "string"},
                "cmd": {"type": "string", "description": "wp-cli command without the 'wp' prefix, e.g. 'option get siteurl'"}
            },
            "required": ["site", "cmd"]
        }
    },
    {
        "name": "list_courses",
        "description": "List all MasterStudy courses on a site with id, title, status, students count, lessons count.",
        "input_schema": {
            "type": "object",
            "properties": {"site": {"type": "string"}},
            "required": ["site"]
        }
    },
    {
        "name": "get_course",
        "description": "Get full MasterStudy course details including all lessons and quizzes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "site": {"type": "string"},
                "course_id": {"type": "integer"}
            },
            "required": ["site", "course_id"]
        }
    },
    {
        "name": "search_knowledge",
        "description": "Search the knowledge base (uploaded PDFs, URLs, text). Returns up to 5 relevant snippets.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    },
    {
        "name": "list_sites",
        "description": "List all WordPress sites registered in the agent with connection status.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_hosting_info",
        "description": "Get Hostinger hosting account info (VPS list, plans, websites) if Hostinger API is configured.",
        "input_schema": {"type": "object", "properties": {}}
    }
]

# قائمة الأوامر المحظورة في wp-cli (حماية)
BLOCKED_CLI_PATTERNS = [
    "delete", "deactivate --all", "drop", "truncate",
    "rm ", "uninstall", "install --activate",
    "reset", "destroy", "flush-all"
]

def _is_cli_safe(cmd: str) -> bool:
    cmd_l = cmd.lower().strip()
    return not any(p in cmd_l for p in BLOCKED_CLI_PATTERNS)

def execute_tool(name: str, args: dict) -> dict:
    """
    ينفذ الأداة المطلوبة ويرجع النتيجة بصيغة JSON-safe.
    """
    from wp_manager import wp_manager
    from knowledge_manager import knowledge_manager
    
    logger.info(f"LLM tool call: {name} args={json.dumps(args, ensure_ascii=False)[:200]}")
    
    try:
        if name == "list_sites":
            sites = wp_manager.get_all_sites()
            return {"sites": [{"name": s.name, "url": s.url, "connected": s.connected} for s in sites]}
        
        site_name = args.get("site")
        site = wp_manager.get_site(site_name) if site_name else None
        
        if name in ("get_site_info", "list_plugins", "get_error_log", "run_wp_cli", 
                    "list_courses", "get_course") and not site:
            return {"error": f"Site '{site_name}' not found. Use list_sites first."}
        
        if name == "get_site_info":
            r = site.get_site_info()
            return r.get("data", r) if isinstance(r, dict) else {"error": "invalid response"}
        
        if name == "list_plugins":
            r = site.get_plugins()
            return r.get("data", r) if isinstance(r, dict) else {"error": "invalid response"}
        
        if name == "get_error_log":
            r = site.get_error_log()
            return r.get("data", r) if isinstance(r, dict) else {"error": "invalid response"}
        
        if name == "run_wp_cli":
            cmd = args.get("cmd", "")
            if not _is_cli_safe(cmd):
                return {"error": f"Blocked destructive command: {cmd}"}
            r = site.run_cli(cmd)
            return r.get("data", r) if isinstance(r, dict) else {"error": "invalid response"}
        
        if name == "list_courses":
            r = site._request("GET", "masterstudy/courses")
            return r.get("data", r) if isinstance(r, dict) else {"error": "invalid response"}
        
        if name == "get_course":
            cid = args.get("course_id")
            r = site._request("GET", f"masterstudy/courses/{cid}")
            return r.get("data", r) if isinstance(r, dict) else {"error": "invalid response"}
        
        if name == "search_knowledge":
            q = args.get("query", "")
            results = knowledge_manager.search(q, limit=5)
            return {"results": results, "count": len(results)}
        
        if name == "get_hosting_info":
            try:
                from hostinger_client import hostinger_client
                return hostinger_client.get_summary()
            except Exception as e:
                return {"error": f"Hostinger not configured: {str(e)}"}
        
        return {"error": f"Unknown tool: {name}"}
    
    except Exception as e:
        logger.exception(f"Tool execution failed: {name}")
        return {"error": str(e), "tool": name}
```

### 📌 المهمة D2: أضف `think_with_tools` في `llm_bridge.py`

في `llm_bridge.py` أضف دالة جديدة للـ Claude tool-use loop:

```python
def think_with_tools(self, task: str, context: dict = None, max_iterations: int = 8) -> dict:
    """
    تنفيذ Agentic loop مع Claude API:
    Claude يطلب tool → ننفذه → نعيد له النتيجة → يكمل حتى يعطي جواب نهائي.
    """
    if self.provider != "claude" or not self.api_key:
        # fallback للـ provider الحالي بدون tools
        return {"final": self._call_llm(task), "tool_calls": [], "fallback": True}
    
    from llm_tools import LLM_TOOLS, execute_tool
    
    system_prompt = (
        "أنت مساعد AI خبير في WordPress. لديك أدوات حقيقية يمكنك استدعاؤها لجلب بيانات فعلية. "
        "استخدم الأدوات قبل الإجابة — لا تخمّن. "
        "ابدأ عادةً بـ list_sites لمعرفة المواقع المتاحة، ثم استخدم الأدوات المتخصصة."
    )
    if context:
        system_prompt += f"\n\nسياق إضافي: {json.dumps(context, ensure_ascii=False)[:500]}"
    
    messages = [{"role": "user", "content": task}]
    tool_calls_log = []
    
    for iteration in range(max_iterations):
        body = {
            "model": self.model or "claude-sonnet-4-5",
            "max_tokens": 2000,
            "system": system_prompt,
            "tools": LLM_TOOLS,
            "messages": messages
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        try:
            data_bytes = json.dumps(body).encode()
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=data_bytes, headers=headers, method="POST"
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            logger.error(f"Claude tool-use HTTP {e.code}: {err_body[:300]}")
            return {"final": f"[API Error {e.code}]", "tool_calls": tool_calls_log, "error": err_body}
        except Exception as e:
            logger.error(f"Claude tool-use exception: {e}")
            return {"final": f"[Error: {e}]", "tool_calls": tool_calls_log, "error": str(e)}
        
        content = data.get("content", [])
        stop_reason = data.get("stop_reason", "")
        messages.append({"role": "assistant", "content": content})
        
        # إن انتهى (end_turn) أرجع النص النهائي
        if stop_reason != "tool_use":
            final_text = " ".join(b.get("text", "") for b in content if b.get("type") == "text")
            return {
                "final": final_text,
                "tool_calls": tool_calls_log,
                "iterations": iteration + 1,
                "stop_reason": stop_reason
            }
        
        # نفذ كل tool_use في الرد
        tool_results = []
        for block in content:
            if block.get("type") == "tool_use":
                tool_name = block["name"]
                tool_args = block.get("input", {})
                result = execute_tool(tool_name, tool_args)
                tool_calls_log.append({"tool": tool_name, "args": tool_args, "result_preview": str(result)[:200]})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block["id"],
                    "content": json.dumps(result, ensure_ascii=False)[:8000]
                })
        messages.append({"role": "user", "content": tool_results})
    
    return {
        "final": "[Max iterations reached]",
        "tool_calls": tool_calls_log,
        "iterations": max_iterations
    }
```

### 📌 المهمة D3: استخدم `think_with_tools` في `ai_operator`

في `ai_operator.py` عند `intent.category == "general"`:

```python
if fn == "general_ai_task":
    if llm_bridge.provider == "claude" and llm_bridge.api_key:
        # استخدم tool-use الحقيقي
        result = llm_bridge.think_with_tools(
            self._wrap_prompt(task),
            context={"site": site.name if site else None}
        )
        return {
            "ok": True,
            "result": result["final"],
            "tools_used": [tc["tool"] for tc in result.get("tool_calls", [])],
            "iterations": result.get("iterations", 0)
        }
    else:
        # fallback (mock أو openai بدون tools)
        prompt = f"أنت مساعد WordPress خبير. نفّذ:\n{task}"
        result = llm_bridge._call_llm(self._wrap_prompt(prompt))
        return {"ok": True, "result": result, "tools_used": [], "fallback": True}
```

### 📌 المهمة D4: endpoint جديد لاختبار الذكاء مباشرة

في `wp_routes.py`:

```python
@wp_bp.route("/ai/chat", methods=["POST"])
def ai_chat():
    """
    محادثة ذكية حقيقية — Claude يستخدم Tools.
    """
    from llm_bridge import llm_bridge
    data = request.json or {}
    message = data.get("message", "")
    site_context = data.get("site")
    if not message:
        return jsonify({"success": False, "error": "message required"}), 400
    result = llm_bridge.think_with_tools(
        message,
        context={"site": site_context} if site_context else None
    )
    return jsonify({"success": True, **result})
```

✅ **اختبار دفعة D كاملة**:

1. اضبط `.env`:
   ```
   LLM_PROVIDER=claude
   LLM_API_KEY=<your-anthropic-key>
   LLM_MODEL=claude-sonnet-4-5
   ```
2. أعد تشغيل الخادم.
3. اختبر:
   ```bash
   curl -X POST http://127.0.0.1:5001/wp/ai/chat \
     -H "Content-Type: application/json" \
     -d '{"message":"كم عدد الـ plugins النشطة في mbt ولماذا قد يكون الموقع بطيئًا؟"}'
   ```
   يجب أن يرجع:
   - `final`: نص طبيعي يذكر رقمًا حقيقيًا.
   - `tool_calls`: [{"tool":"list_sites",...}, {"tool":"list_plugins",...}, ...].
   - `iterations`: 2-4.

---

# ═══════════════════════════════════════
# ═══ دفعة E — توحيد + Self-Heal آمن ═══
# ═══════════════════════════════════════

### 📌 المهمة E1: Self-Heal يدوي مع تأكيد

في `wp_routes.py`:

```python
@wp_bp.route("/selfheal/propose", methods=["POST"])
def selfheal_propose():
    """يقترح إصلاحات دون تنفيذ."""
    from ai_operator import ai_operator
    data = request.json or {}
    site = wp_manager.get_site(data.get("site"))
    if not site:
        return jsonify({"success": False, "error": "Site not found"}), 404
    # اقرأ log + شخّص
    r = ai_operator.execute("شخّص أخطاء الموقع واقترح إصلاحات", site=site)
    return jsonify({"success": True, "diagnosis": r, "requires_confirmation": True})

@wp_bp.route("/selfheal/apply", methods=["POST"])
def selfheal_apply():
    """ينفذ الإصلاح فقط مع confirm=true صريح."""
    data = request.json or {}
    if data.get("confirm") != True:
        return jsonify({"success": False, "error": "confirm=true required"}), 400
    site = wp_manager.get_site(data.get("site"))
    action = data.get("action")  # e.g. "deactivate_plugin"
    target = data.get("target")  # e.g. "wp-rocket/wp-rocket.php"
    if not site or not action:
        return jsonify({"success": False, "error": "site and action required"}), 400
    # نفذ الإصلاح المحدد فقط
    if action == "deactivate_plugin" and target:
        r = site.toggle_plugin(target, "deactivate")
        return jsonify({"success": r.get("success", False), "action": action, "target": target, "result": r})
    if action == "flush_cache":
        r = site.run_cli("cache flush")
        return jsonify({"success": r.get("success", False), "action": action, "result": r})
    return jsonify({"success": False, "error": f"Unknown action: {action}"}), 400
```

### 📌 المهمة E2: عطّل handle_shutdown الخطير في PHP

في `class-aiwa-selfheal.php`:
- احذف أو علّق سطر `register_shutdown_function( [ $this, 'handle_shutdown' ] )` في `init()`.
- أضف خيار في `ai-wordpress-agent.php` settings: `aiwa_autoheal_enabled = false` افتراضيًا.

### 📌 المهمة E3: تسجيل tool_registry في حلقة التنفيذ

في `ai_operator.py` قبل `_build_plan`:
```python
try:
    from tool_registry import tool_registry
    suggested = tool_registry.choose_best_tool(task)
    if suggested:
        logger.info(f"Tool registry suggestion: {suggested.name} [{suggested.tool_type}]")
        self.execution_log.append({"type": "tool_hint", "name": suggested.name})
except Exception:
    pass
```

✅ **اختبار دفعة E**: Active Tools في الداشبورد ستبدأ تظهر calls > 0.

---

# ═══════════════════════════════════════
# ═══ دفعة F — داشبورد بأسلوب WP-Admin ═══
# ═══════════════════════════════════════

> الهدف: واجهة احترافية تشبه WordPress Admin، بيانات حقيقية (لا وهمية)، كل عنصر مربوط بـ endpoint فعلي.

### 📌 المهمة F1: هيكل الداشبورد الجديد

أنشئ `C:\mcp-agent\templates\wp-dashboard-v2.html` ببنية WP-Admin:

**التخطيط العام**:
```
┌─────────────────────────────────────────────────────────────┐
│  Top Admin Bar: Logo | Site Selector ▼ | Live Status | User │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                   │
│ Sidebar  │           Main Content Area                       │
│          │                                                   │
│ Dashboard│   ┌─ At-a-Glance ───────┐  ┌─ Activity ──────┐  │
│ Posts    │   │ WP Version: 6.7     │  │ Recent: ...     │  │
│ Pages    │   │ Theme: ...          │  │                 │  │
│ Media    │   │ Plugins: 12 active  │  └─────────────────┘  │
│ Plugins  │   └─────────────────────┘                        │
│ Users    │                                                   │
│ ──────── │   ┌─ Health Check ──────────────────────────┐   │
│ MasterStd│   │ ✅ SSL  ⚠️ Debug ON  ✅ PHP  ...        │   │
│ Elementor│   └─────────────────────────────────────────┘   │
│ ──────── │                                                   │
│ Hostinger│   ┌─ AI Assistant ──────────────────────────┐   │
│ Knowledge│   │ [chat box with live tool-use display]   │   │
│ Settings │   └─────────────────────────────────────────┘   │
└──────────┴──────────────────────────────────────────────────┘
```

**التصميم المطلوب**:
- ألوان: `#1e1e1e` sidebar (WP Admin dark)، `#2271b1` للأزرار الأساسية (WP blue)، `#f0f0f1` خلفية المحتوى، `#fff` للـ cards.
- Font: Inter أو Cairo أو Segoe UI، RTL كامل، حجم 14px أساسي.
- أيقونات Dashicons من WordPress CDN: `https://s.w.org/wp-includes/css/dashicons.min.css`.
- كل card له: عنوان + أيقونة + actions زرّ "View all" + badge لعدد العناصر.

### 📌 المهمة F2: استبدل كل البيانات الوهمية ببيانات حقيقية

لكل عنصر في الداشبورد، حدد الـ endpoint الذي يغذّيه:

| عنصر الواجهة | Endpoint | حقل البيانات |
|---|---|---|
| WP Version | `/wp/site-info` | `data.wp_version` |
| Theme | `/wp/site-info` | `data.theme.name` |
| Active Plugins | `/wp/plugins` | `data.plugins` filter active |
| Updates Available | `/wp/plugins` | filter `update_available` |
| PHP Version | `/wp/site-info` | `data.php_version` |
| Memory Usage | `/wp/site-info` | `data.memory_usage` / `data.memory_limit` |
| Debug Mode | `/wp/site-info` | `data.debug_mode` |
| Pages Count | `/wp/site-info` | `data.pages_count` |
| Fatal Errors | `/wp/error-log` | `data.has_fatal` |
| Success Rate | `/system/status` | `feedback.success_rate` |
| Active Tools | `/system/status` | `tools` array |
| LLM Status | `/llm/status` | `is_mock` + `provider` |

**قاعدة**: إذا فشل الـ endpoint، اعرض "—" (شرطة) لا "0" ولا رقم وهمي. إضافة tooltip يشرح السبب.

### 📌 المهمة F3: Live Status Ticker

شريط علوي ثابت يعرض بـ polling كل 10 ثوانٍ:
- Site Status (Connected/Disconnected) مع latency
- LLM Status (Active/Mock) مع اسم الـ provider
- Hostinger Status (Connected/Not configured)
- Active Agent Status (Idle/Running + current task name)

JavaScript:
```javascript
async function pollStatus() {
    const [site, llm, sys, host] = await Promise.all([
        fetch('/wp/sites/' + state.currentSite + '/status').then(r => r.json()).catch(() => null),
        fetch('/llm/status').then(r => r.json()).catch(() => null),
        fetch('/system/status').then(r => r.json()).catch(() => null),
        fetch('/hostinger/status').then(r => r.json()).catch(() => null)
    ]);
    renderTicker({site, llm, sys, host});
}
setInterval(pollStatus, 10000);
pollStatus();
```

### 📌 المهمة F4: Health Check Card (WP Style)

استنسخ WP Site Health بشكل مختصر:

```html
<div class="card card-health">
    <h3>🏥 Site Health</h3>
    <ul class="health-checks">
        <li data-check="ssl">🔒 SSL Certificate: <span class="status"></span></li>
        <li data-check="php">⚙️ PHP Version: <span class="status"></span></li>
        <li data-check="updates">🔄 Updates: <span class="status"></span></li>
        <li data-check="debug">🐛 Debug Mode: <span class="status"></span></li>
        <li data-check="memory">💾 Memory: <span class="status"></span></li>
        <li data-check="cache">⚡ Object Cache: <span class="status"></span></li>
    </ul>
    <button class="button button-primary" onclick="runHealthScan()">فحص شامل الآن</button>
</div>
```

كل فحص يستدعي endpoint موجود (site-info + error-log + plugins).

### 📌 المهمة F5: AI Assistant Panel (لوحة المحادثة)

في الداشبورد: لوحة ثابتة أسفل اليمين (مثل Chat widget) أو صفحة مستقلة `/dashboard/ai`:

```html
<div class="ai-assistant-panel">
    <header>
        <span>🤖 AI Assistant</span>
        <span class="status-badge" id="llmBadge">Claude ✓</span>
    </header>
    <div class="messages" id="aiMessages"></div>
    <div class="tool-activity" id="toolActivity">
        <!-- يظهر أثناء tool-use: "🔍 reading plugins..." -->
    </div>
    <div class="input-bar">
        <textarea id="aiInput" placeholder="اسأل عن موقعك، أو اطلب تحليلًا، أو أنشئ كورسًا..."></textarea>
        <button onclick="sendToAI()">إرسال</button>
    </div>
</div>

<script>
async function sendToAI() {
    const msg = document.getElementById('aiInput').value.trim();
    if (!msg) return;
    appendMessage('user', msg);
    const activity = document.getElementById('toolActivity');
    activity.innerHTML = '⏳ يفكّر...';
    
    const resp = await fetch('/wp/ai/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: msg, site: state.currentSite?.name})
    });
    const data = await resp.json();
    
    // اعرض الأدوات التي استخدمها
    if (data.tool_calls?.length) {
        activity.innerHTML = 'استخدم: ' + data.tool_calls.map(t => `<span class="tool-chip">${t.tool}</span>`).join(' ');
    }
    appendMessage('ai', data.final);
}
</script>
```

### 📌 المهمة F6: Sidebar ديناميكي مربوط بالـ router

أقسام الـ Sidebar وروابطها:

| القسم | Route | Endpoint الرئيسي |
|---|---|---|
| لوحة التحكم | `#overview` | `/wp/site-info` |
| المواقع | `#sites` | `/wp/sites` |
| الإضافات | `#plugins` | `/wp/plugins` |
| المستخدمون | `#users` | `/wp/users` |
| Elementor | `#elementor` | `/wp/elementor-get` |
| MasterStudy | `#masterstudy` | `/wp/masterstudy/*` |
| معرفة | `#knowledge` | `/knowledge/*` |
| Self-Heal | `#selfheal` | `/wp/selfheal/*` |
| Hostinger | `#hostinger` | `/hostinger/*` (بعد الدفعة H) |
| إعدادات | `#settings` | `/llm/status`, `/llm/configure` |
| AI Assistant | `#ai` | `/wp/ai/chat` |

استخدم hash router بسيط (vanilla JS) أو Alpine.js لتبديل الصفحات بدون reload.

✅ **اختبار دفعة F**:
- كل card في الداشبورد يعرض رقمًا حقيقيًا أو "—".
- لا توجد قيم hard-coded مثل `55.6%` ظاهرة بدون بيانات فعلية.
- Live ticker يُحدَّث كل 10 ثوانٍ.
- AI Assistant يرى tool chips عند كل استخدام.

---

# ═══════════════════════════════════════
# ═══ دفعة G — MasterStudy + الموارد ═══
# ═══════════════════════════════════════

### 📌 المهمة G1: أضف جدول موارد الدورة في WordPress Plugin

في `class-aiwa-api.php` أضف routes جديدة:

```php
// ── MasterStudy Resources ──────────────
register_rest_route( $ns, '/masterstudy/courses/(?P<id>\d+)/resources', [
    ['methods' => 'GET',  'callback' => [ $this, 'ms_get_resources' ],  'permission_callback' => [ $this, 'check_auth' ]],
    ['methods' => 'POST', 'callback' => [ $this, 'ms_add_resource' ],   'permission_callback' => [ $this, 'check_auth' ]],
]);
register_rest_route( $ns, '/masterstudy/courses/(?P<id>\d+)/resources/(?P<rid>\d+)', [
    ['methods' => 'DELETE', 'callback' => [ $this, 'ms_delete_resource' ], 'permission_callback' => [ $this, 'check_auth' ]],
]);
```

Handlers:

```php
public function ms_get_resources( WP_REST_Request $req ): WP_REST_Response {
    $course_id = (int) $req->get_param('id');
    $resources = get_post_meta( $course_id, 'aiwa_resources', true ) ?: [];
    return new WP_REST_Response(['success' => true, 'resources' => $resources]);
}

public function ms_add_resource( WP_REST_Request $req ): WP_REST_Response {
    $course_id = (int) $req->get_param('id');
    $p = $req->get_json_params();
    $type = sanitize_text_field($p['type'] ?? 'url');   // url | pdf | video | file
    
    $resources = get_post_meta( $course_id, 'aiwa_resources', true ) ?: [];
    $new_id = count($resources) > 0 ? max(array_column($resources, 'id')) + 1 : 1;
    
    $resource = [
        'id'          => $new_id,
        'type'        => $type,
        'title'       => sanitize_text_field($p['title'] ?? ''),
        'url'         => esc_url_raw($p['url'] ?? ''),
        'description' => wp_kses_post($p['description'] ?? ''),
        'attached_to' => (int)($p['lesson_id'] ?? 0),  // 0 = course-level
        'added_at'    => current_time('mysql'),
    ];
    
    // لو رفع ملف PDF فعلي
    if ( $type === 'pdf' && ! empty($p['file_base64']) ) {
        $uploaded = $this->_upload_base64_file( $p['file_base64'], $p['filename'] ?? 'resource.pdf' );
        if ( $uploaded ) {
            $resource['url']         = $uploaded['url'];
            $resource['attachment_id'] = $uploaded['id'];
        }
    }
    
    $resources[] = $resource;
    update_post_meta( $course_id, 'aiwa_resources', $resources );
    
    return new WP_REST_Response(['success' => true, 'resource' => $resource]);
}

public function ms_delete_resource( WP_REST_Request $req ): WP_REST_Response {
    $course_id = (int) $req->get_param('id');
    $rid       = (int) $req->get_param('rid');
    $resources = get_post_meta( $course_id, 'aiwa_resources', true ) ?: [];
    $resources = array_filter($resources, fn($r) => $r['id'] != $rid);
    update_post_meta( $course_id, 'aiwa_resources', array_values($resources) );
    return new WP_REST_Response(['success' => true]);
}

private function _upload_base64_file( string $base64, string $filename ): ?array {
    require_once ABSPATH . 'wp-admin/includes/file.php';
    require_once ABSPATH . 'wp-admin/includes/media.php';
    require_once ABSPATH . 'wp-admin/includes/image.php';
    
    $decoded = base64_decode( preg_replace('#^data:.+?base64,#', '', $base64) );
    if ( ! $decoded ) return null;
    
    $upload = wp_upload_bits( sanitize_file_name($filename), null, $decoded );
    if ( ! empty($upload['error']) ) return null;
    
    $attachment = [
        'post_mime_type' => wp_check_filetype($filename)['type'] ?: 'application/pdf',
        'post_title'     => pathinfo($filename, PATHINFO_FILENAME),
        'post_content'   => '',
        'post_status'    => 'inherit'
    ];
    $att_id = wp_insert_attachment( $attachment, $upload['file'] );
    if ( is_wp_error($att_id) ) return null;
    
    $meta = wp_generate_attachment_metadata( $att_id, $upload['file'] );
    wp_update_attachment_metadata( $att_id, $meta );
    
    return [ 'id' => $att_id, 'url' => $upload['url'] ];
}
```

### 📌 المهمة G2: دوال Python للموارد

في `masterstudy_manager.py` أضف:

```python
def list_resources(self, course_id: int) -> Dict:
    return self.site._request("GET", f"masterstudy/courses/{course_id}/resources")

def add_resource_url(self, course_id: int, title: str, url: str, 
                     description: str = "", lesson_id: int = 0, 
                     type: str = "url") -> Dict:
    return self.site._request("POST", f"masterstudy/courses/{course_id}/resources", {
        "type": type,  # url | video | pdf-link
        "title": title,
        "url": url,
        "description": description,
        "lesson_id": lesson_id
    })

def add_resource_pdf(self, course_id: int, title: str, pdf_path: str, 
                     description: str = "", lesson_id: int = 0) -> Dict:
    import base64 as _b64
    with open(pdf_path, "rb") as f:
        b64 = _b64.b64encode(f.read()).decode()
    import os as _os
    filename = _os.path.basename(pdf_path)
    return self.site._request("POST", f"masterstudy/courses/{course_id}/resources", {
        "type": "pdf",
        "title": title,
        "description": description,
        "lesson_id": lesson_id,
        "file_base64": b64,
        "filename": filename
    })

def delete_resource(self, course_id: int, resource_id: int) -> Dict:
    return self.site._request("DELETE", f"masterstudy/courses/{course_id}/resources/{resource_id}")
```

### 📌 المهمة G3: endpoints للـ Flask

في `wp_routes.py`:

```python
@wp_bp.route("/masterstudy/resources/list", methods=["POST"])
def ms_resources_list():
    data = request.json or {}
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    from masterstudy_manager import MasterStudyManager
    return jsonify(MasterStudyManager(site).list_resources(data.get("course_id")))

@wp_bp.route("/masterstudy/resources/add-url", methods=["POST"])
def ms_resources_add_url():
    data = request.json or {}
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    from masterstudy_manager import MasterStudyManager
    ms = MasterStudyManager(site)
    return jsonify(ms.add_resource_url(
        course_id=data.get("course_id"),
        title=data.get("title", ""),
        url=data.get("url", ""),
        description=data.get("description", ""),
        lesson_id=data.get("lesson_id", 0),
        type=data.get("type", "url")
    ))

@wp_bp.route("/masterstudy/resources/add-pdf", methods=["POST"])
def ms_resources_add_pdf():
    """يقبل multipart/form-data مع file + metadata"""
    from masterstudy_manager import MasterStudyManager
    site_name = request.form.get("site")
    site = wp_manager.get_site(site_name)
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    f = request.files.get("file")
    if not f: return jsonify({"success": False, "error": "file required"}), 400
    
    import tempfile, os
    tmp = tempfile.mktemp(suffix=".pdf")
    f.save(tmp)
    try:
        ms = MasterStudyManager(site)
        result = ms.add_resource_pdf(
            course_id=int(request.form.get("course_id", 0)),
            title=request.form.get("title", f.filename),
            pdf_path=tmp,
            description=request.form.get("description", ""),
            lesson_id=int(request.form.get("lesson_id", 0))
        )
    finally:
        try: os.remove(tmp)
        except: pass
    return jsonify(result)

@wp_bp.route("/masterstudy/resources/delete", methods=["POST"])
def ms_resources_delete():
    data = request.json or {}
    site = wp_manager.get_site(data.get("site"))
    if not site: return jsonify({"success": False, "error": "Site not found"}), 404
    from masterstudy_manager import MasterStudyManager
    return jsonify(MasterStudyManager(site).delete_resource(data.get("course_id"), data.get("resource_id")))

@wp_bp.route("/masterstudy/resources/learn", methods=["POST"])
def ms_resources_learn():
    """
    ذكاء إضافي: يحوّل ملف PDF مرفوع إلى محتوى knowledge_base 
    ليستخدمه الـ LLM عند إنشاء دروس الكورس.
    """
    from knowledge_manager import knowledge_manager
    import tempfile, os
    course_id = request.form.get("course_id")
    f = request.files.get("file")
    if not f: return jsonify({"success": False, "error": "file required"}), 400
    tmp = tempfile.mktemp(suffix=os.path.splitext(f.filename)[1])
    f.save(tmp)
    try:
        res = knowledge_manager.learn_from_file(tmp, tags=["masterstudy", f"course_{course_id}"])
    finally:
        try: os.remove(tmp)
        except: pass
    return jsonify(res)
```

### 📌 المهمة G4: واجهة MasterStudy في الداشبورد

في الـ v2 dashboard أضف صفحة `#masterstudy`:

```html
<div class="page-masterstudy">
    <header class="page-header">
        <h1>🎓 MasterStudy LMS</h1>
        <button class="button button-primary" onclick="openCreateCourseModal()">+ كورس جديد</button>
    </header>
    
    <!-- Courses List -->
    <div class="courses-grid" id="coursesGrid"></div>
    
    <!-- Modal: Create Course -->
    <div class="modal" id="createCourseModal" hidden>
        <div class="modal-body">
            <h2>إنشاء كورس جديد</h2>
            
            <!-- Tab 1: بيانات -->
            <input id="courseTitle" placeholder="عنوان الكورس" />
            <textarea id="courseDesc" placeholder="وصف مختصر"></textarea>
            <select id="courseLevel">
                <option>مبتدئ</option><option>متوسط</option><option>متقدم</option>
            </select>
            <input id="coursePrice" type="number" placeholder="السعر (0 للمجاني)" />
            
            <!-- Tab 2: موارد التعلم -->
            <h3>📚 موارد التعلم (للـ AI)</h3>
            <p class="desc">ارفع PDFs أو ألصق روابط. الـ AI سيستخدمها عند توليد محتوى الدروس.</p>
            <div id="learningResources">
                <div class="resource-inputs">
                    <input type="text" id="resUrl" placeholder="أضف رابط مصدر (YouTube, Wikipedia, Docs...)" />
                    <button onclick="addResourceUrl()">+ رابط</button>
                </div>
                <div class="resource-inputs">
                    <input type="file" id="resPdf" accept=".pdf,.txt,.md,.docx" multiple />
                    <button onclick="uploadResourceFiles()">+ ملف</button>
                </div>
                <ul id="resourcesList"></ul>
            </div>
            
            <!-- Tab 3: إعدادات AI -->
            <label>
                <input type="checkbox" id="aiGenerate" checked />
                توليد دروس تلقائيًا بالذكاء من الموارد
            </label>
            <label>
                عدد الدروس: <input type="number" id="lessonsCount" value="5" min="1" max="20" />
            </label>
            
            <div class="modal-actions">
                <button class="button" onclick="closeModal()">إلغاء</button>
                <button class="button button-primary" onclick="createCourseWithResources()">إنشاء</button>
            </div>
        </div>
    </div>
</div>

<script>
let pendingResources = []; // موارد مؤقتة قبل إنشاء الكورس

function addResourceUrl() {
    const url = document.getElementById('resUrl').value.trim();
    if (!url) return;
    pendingResources.push({ type: 'url', url, title: url });
    document.getElementById('resUrl').value = '';
    renderResourcesList();
}

async function uploadResourceFiles() {
    const files = document.getElementById('resPdf').files;
    for (const f of files) {
        pendingResources.push({ type: 'file', file: f, title: f.name });
    }
    renderResourcesList();
}

function renderResourcesList() {
    const ul = document.getElementById('resourcesList');
    ul.innerHTML = pendingResources.map((r, i) => 
        `<li>${r.type === 'url' ? '🔗' : '📄'} ${r.title} <button onclick="removeRes(${i})">×</button></li>`
    ).join('');
}

async function createCourseWithResources() {
    const title = document.getElementById('courseTitle').value;
    const desc = document.getElementById('courseDesc').value;
    const level = document.getElementById('courseLevel').value;
    const price = parseFloat(document.getElementById('coursePrice').value) || 0;
    const aiGen = document.getElementById('aiGenerate').checked;
    const count = parseInt(document.getElementById('lessonsCount').value);
    
    // Step 1: ارفع الموارد لـ knowledge base أولًا (لتغذية الـ LLM)
    for (const r of pendingResources) {
        if (r.type === 'file') {
            const fd = new FormData();
            fd.append('file', r.file);
            fd.append('course_id', 'pending');
            await fetch('/wp/masterstudy/resources/learn', {method: 'POST', body: fd});
        } else if (r.type === 'url') {
            await fetch('/wp/knowledge/learn-url', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url: r.url, tags: ['masterstudy']})
            });
        }
    }
    
    // Step 2: أنشئ الكورس (سيستفيد AI من الموارد عبر knowledge_manager)
    const endpoint = aiGen ? '/wp/masterstudy/ai-create' : '/wp/create-course';
    const body = aiGen 
        ? { site: state.currentSite.name, topic: title, lessons_count: count, price }
        : { site: state.currentSite.name, title, content: desc, status: 'draft' };
    
    const r = await fetch(endpoint, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body)
    }).then(r => r.json());
    
    if (r.success) {
        const courseId = r.course_id || r.data?.course_id;
        // Step 3: اربط الموارد بالكورس المُنشأ
        for (const res of pendingResources) {
            if (res.type === 'url') {
                await fetch('/wp/masterstudy/resources/add-url', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        site: state.currentSite.name,
                        course_id: courseId,
                        title: res.title,
                        url: res.url,
                        type: 'url'
                    })
                });
            } else if (res.type === 'file') {
                const fd = new FormData();
                fd.append('site', state.currentSite.name);
                fd.append('course_id', courseId);
                fd.append('title', res.title);
                fd.append('file', res.file);
                await fetch('/wp/masterstudy/resources/add-pdf', {method: 'POST', body: fd});
            }
        }
        alert(`✅ الكورس أُنشئ (ID: ${courseId}) مع ${pendingResources.length} موارد`);
        pendingResources = [];
        loadCourses();
    } else {
        alert('❌ فشل: ' + (r.error || 'خطأ غير معروف'));
    }
    closeModal();
}

async function loadCourses() {
    const r = await fetch('/wp/proxy', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({site: state.currentSite.name, method: 'GET', path: 'masterstudy/courses'})
    }).then(r => r.json());
    
    const courses = r.data?.courses || [];
    document.getElementById('coursesGrid').innerHTML = courses.map(c => `
        <div class="course-card">
            <h3>${c.title}</h3>
            <div class="meta">
                <span>📖 ${c.lessons} دروس</span>
                <span>👥 ${c.students} طلاب</span>
                <span>🎯 ${c.level}</span>
                <span class="status-${c.status}">${c.status}</span>
            </div>
            <div class="actions">
                <button onclick="viewCourse(${c.id})">عرض</button>
                <button onclick="manageResources(${c.id})">📚 موارد</button>
                <button onclick="aiAnalyze(${c.id})">🤖 تحليل AI</button>
            </div>
        </div>
    `).join('');
}

async function manageResources(courseId) {
    const r = await fetch('/wp/masterstudy/resources/list', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({site: state.currentSite.name, course_id: courseId})
    }).then(r => r.json());
    // اعرض modal بالموارد مع إمكانية الإضافة والحذف
    // ... (UI code)
}
</script>
```

✅ **اختبار دفعة G**:
- إنشاء كورس جديد من الداشبورد مع 2 روابط + 1 PDF → ينجح.
- الكورس يظهر في WordPress admin تحت "STM Courses".
- الموارد مخزّنة في `post_meta` للكورس.
- الـ PDF محفوظ في `wp-content/uploads/`.
- `knowledge_manager` يحتوي على محتوى الـ PDF (قابل للبحث).

---

# ═══════════════════════════════════════
# ═══ دفعة H — Hostinger API ═══
# ═══════════════════════════════════════

### 📌 المهمة H1: أنشئ `hostinger_client.py`

```python
"""
Hostinger API Client
https://developers.hostinger.com
Auth: Bearer token from hPanel → Account → API → New Token
"""
import json
import time
import sqlite3
import urllib.request
import urllib.error
from typing import Dict, List, Optional
from logger_system import get_logger

logger = get_logger("hostinger_client")

DB_PATH = r"C:\mcp-agent\agent_state.db"
BASE_URL = "https://developers.hostinger.com"


class HostingerClient:
    def __init__(self):
        self._token: Optional[str] = None
        self._init_db()
        self._load_token()
    
    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS integrations (
            provider TEXT PRIMARY KEY,
            token TEXT,
            metadata TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        conn.close()
    
    def _load_token(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT token FROM integrations WHERE provider = 'hostinger'")
        row = cur.fetchone()
        conn.close()
        if row:
            self._token = row[0]
    
    def set_token(self, token: str, metadata: Dict = None) -> Dict:
        """يحفظ الـ API token بأمان في SQLite"""
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO integrations (provider, token, metadata, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, ("hostinger", token, json.dumps(metadata or {})))
        conn.commit()
        conn.close()
        self._token = token
        # تحقق فوري
        test = self.ping()
        return {"success": test.get("ok", False), "test_result": test}
    
    def clear_token(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM integrations WHERE provider = 'hostinger'")
        conn.commit()
        conn.close()
        self._token = None
    
    def is_configured(self) -> bool:
        return bool(self._token)
    
    def _request(self, method: str, path: str, data: Dict = None, timeout: int = 20) -> Dict:
        if not self._token:
            return {"ok": False, "error": "Hostinger API token not configured"}
        url = f"{BASE_URL}{path}"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "User-Agent": "MOSTAFA-AI-Agent/1.0"
        }
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return {"ok": True, "status": resp.status, "data": json.loads(resp.read().decode())}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            logger.warning(f"Hostinger HTTP {e.code}: {err_body[:200]}")
            return {"ok": False, "status": e.code, "error": err_body[:500]}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    # ── Test Connection ──────────────────
    def ping(self) -> Dict:
        """أبسط استدعاء للتحقق من صحة التوكن"""
        return self._request("GET", "/api/billing/v1/catalog-items?category=VPS")
    
    # ── VPS ──────────────────────────────
    def list_vps(self) -> Dict:
        return self._request("GET", "/api/vps/v1/virtual-machines")
    
    def get_vps(self, vm_id: int) -> Dict:
        return self._request("GET", f"/api/vps/v1/virtual-machines/{vm_id}")
    
    def get_vps_metrics(self, vm_id: int, date_from: str = None, date_to: str = None) -> Dict:
        """
        date_from/date_to: ISO 8601 (e.g. 2026-04-20T00:00:00Z)
        """
        if not date_from:
            date_from = time.strftime("%Y-%m-%dT00:00:00Z", time.gmtime(time.time() - 86400))
        if not date_to:
            date_to = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return self._request("GET", 
            f"/api/vps/v1/virtual-machines/{vm_id}/metrics?date_from={date_from}&date_to={date_to}")
    
    def restart_vps(self, vm_id: int) -> Dict:
        return self._request("POST", f"/api/vps/v1/virtual-machines/{vm_id}/restart")
    
    def stop_vps(self, vm_id: int) -> Dict:
        return self._request("POST", f"/api/vps/v1/virtual-machines/{vm_id}/stop")
    
    def start_vps(self, vm_id: int) -> Dict:
        return self._request("POST", f"/api/vps/v1/virtual-machines/{vm_id}/start")
    
    def create_vps_snapshot(self, vm_id: int) -> Dict:
        return self._request("POST", f"/api/vps/v1/virtual-machines/{vm_id}/snapshot")
    
    # ── Hosting (Websites) ────────────────
    def list_websites(self) -> Dict:
        return self._request("GET", "/api/hosting/v1/websites")
    
    # ── Domains ───────────────────────────
    def list_domains(self) -> Dict:
        return self._request("GET", "/api/domains/v1/domains")
    
    def get_dns_zone(self, domain: str) -> Dict:
        return self._request("GET", f"/api/domains/v1/domains/{domain}/dns-zone")
    
    # ── Billing ───────────────────────────
    def list_orders(self) -> Dict:
        return self._request("GET", "/api/billing/v1/orders")
    
    # ── Summary (for dashboard) ───────────
    def get_summary(self) -> Dict:
        """تقرير شامل للداشبورد"""
        if not self._token:
            return {"configured": False}
        vps = self.list_vps()
        websites = self.list_websites()
        domains = self.list_domains()
        return {
            "configured": True,
            "vps": {
                "count": len(vps.get("data", [])) if vps.get("ok") else 0,
                "list": vps.get("data", [])[:5] if vps.get("ok") else [],
                "error": vps.get("error") if not vps.get("ok") else None
            },
            "websites": {
                "count": len(websites.get("data", [])) if websites.get("ok") else 0,
                "list": websites.get("data", [])[:5] if websites.get("ok") else [],
                "error": websites.get("error") if not websites.get("ok") else None
            },
            "domains": {
                "count": len(domains.get("data", [])) if domains.get("ok") else 0,
                "error": domains.get("error") if not domains.get("ok") else None
            }
        }


# Singleton
hostinger_client = HostingerClient()
```

### 📌 المهمة H2: Flask endpoints لـ Hostinger

في `server.py` أضف blueprint جديد أو ضعها في `wp_routes.py` (داخل `wp_bp`) — الأفضل ملف منفصل `hostinger_routes.py`:

```python
"""hostinger_routes.py"""
from flask import Blueprint, request, jsonify
from hostinger_client import hostinger_client

hostinger_bp = Blueprint("hostinger", __name__, url_prefix="/hostinger")


@hostinger_bp.route("/status", methods=["GET"])
def hostinger_status():
    return jsonify({
        "configured": hostinger_client.is_configured(),
        "connected": hostinger_client.ping().get("ok", False) if hostinger_client.is_configured() else False
    })


@hostinger_bp.route("/configure", methods=["POST"])
def hostinger_configure():
    data = request.json or {}
    token = data.get("token", "").strip()
    if not token:
        return jsonify({"success": False, "error": "token required"}), 400
    result = hostinger_client.set_token(token, metadata={"configured_via": "dashboard"})
    return jsonify(result)


@hostinger_bp.route("/disconnect", methods=["POST"])
def hostinger_disconnect():
    hostinger_client.clear_token()
    return jsonify({"success": True})


@hostinger_bp.route("/summary", methods=["GET"])
def hostinger_summary():
    return jsonify(hostinger_client.get_summary())


@hostinger_bp.route("/vps/list", methods=["GET"])
def vps_list():
    return jsonify(hostinger_client.list_vps())


@hostinger_bp.route("/vps/<int:vm_id>", methods=["GET"])
def vps_get(vm_id):
    return jsonify(hostinger_client.get_vps(vm_id))


@hostinger_bp.route("/vps/<int:vm_id>/metrics", methods=["GET"])
def vps_metrics(vm_id):
    return jsonify(hostinger_client.get_vps_metrics(
        vm_id,
        date_from=request.args.get("date_from"),
        date_to=request.args.get("date_to")
    ))


@hostinger_bp.route("/vps/<int:vm_id>/action", methods=["POST"])
def vps_action(vm_id):
    data = request.json or {}
    action = data.get("action")
    if action not in ("restart", "stop", "start", "snapshot"):
        return jsonify({"success": False, "error": "invalid action"}), 400
    # طلب confirm للأفعال المدمرة
    if action in ("stop", "restart") and not data.get("confirm"):
        return jsonify({"success": False, "error": "confirm=true required for " + action}), 400
    method = {
        "restart": hostinger_client.restart_vps,
        "stop":    hostinger_client.stop_vps,
        "start":   hostinger_client.start_vps,
        "snapshot":hostinger_client.create_vps_snapshot
    }[action]
    return jsonify(method(vm_id))


@hostinger_bp.route("/websites", methods=["GET"])
def websites_list():
    return jsonify(hostinger_client.list_websites())


@hostinger_bp.route("/domains", methods=["GET"])
def domains_list():
    return jsonify(hostinger_client.list_domains())
```

ثم في `server.py` سجّل الـ blueprint:
```python
from hostinger_routes import hostinger_bp
app.register_blueprint(hostinger_bp)
```

### 📌 المهمة H3: صفحة Hostinger في الداشبورد

في الـ v2 dashboard أضف صفحة `#hostinger`:

```html
<div class="page-hostinger">
    <header class="page-header">
        <h1>🌐 Hostinger Integration</h1>
        <span id="hostingerStatus" class="status-badge">...</span>
    </header>
    
    <!-- Setup (يظهر فقط إن لم يُضبط) -->
    <div class="card" id="hostingerSetup">
        <h3>🔑 إعداد API</h3>
        <ol>
            <li>اذهب إلى <a href="https://hpanel.hostinger.com/profile/api" target="_blank">hPanel → Account → API</a></li>
            <li>أنشئ توكنًا جديدًا، ضع له اسمًا واختر مدة الصلاحية</li>
            <li>انسخ التوكن والصقه هنا (لن يظهر مرة أخرى بعد الإغلاق)</li>
        </ol>
        <input type="password" id="hostingerToken" placeholder="hsn_xxxxxxxxxxxxxxxxxx" />
        <button class="button button-primary" onclick="saveHostingerToken()">حفظ واختبار</button>
        <p class="description">التوكن يُحفظ محليًا في SQLite. أنت وحدك من يملكه.</p>
    </div>
    
    <!-- Summary (بعد الاتصال) -->
    <div class="grid-4" id="hostingerSummary" hidden>
        <div class="stat-card">
            <span class="stat-num" id="vpsCount">—</span>
            <span class="stat-label">VPS Instances</span>
        </div>
        <div class="stat-card">
            <span class="stat-num" id="sitesCount">—</span>
            <span class="stat-label">Websites</span>
        </div>
        <div class="stat-card">
            <span class="stat-num" id="domainsCount">—</span>
            <span class="stat-label">Domains</span>
        </div>
        <div class="stat-card">
            <span class="stat-num" id="ordersCount">—</span>
            <span class="stat-label">Orders</span>
        </div>
    </div>
    
    <!-- VPS Details -->
    <div class="card" id="vpsDetails" hidden>
        <h3>🖥️ VPS Instances</h3>
        <table class="wp-list-table widefat">
            <thead>
                <tr>
                    <th>Hostname</th>
                    <th>IP</th>
                    <th>State</th>
                    <th>CPU / RAM</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="vpsTable"></tbody>
        </table>
    </div>
    
    <!-- Live Metrics (selected VPS) -->
    <div class="card" id="vpsMetrics" hidden>
        <h3>📊 متابعة الأداء</h3>
        <canvas id="metricsChart" height="200"></canvas>
    </div>
</div>

<script>
async function checkHostingerStatus() {
    const r = await fetch('/hostinger/status').then(r => r.json());
    const badge = document.getElementById('hostingerStatus');
    if (r.configured && r.connected) {
        badge.textContent = 'Connected ✓';
        badge.className = 'status-badge status-ok';
        document.getElementById('hostingerSetup').hidden = true;
        document.getElementById('hostingerSummary').hidden = false;
        document.getElementById('vpsDetails').hidden = false;
        loadHostingerSummary();
    } else if (r.configured) {
        badge.textContent = 'Token Invalid';
        badge.className = 'status-badge status-error';
    } else {
        badge.textContent = 'Not Configured';
        badge.className = 'status-badge status-warn';
    }
}

async function saveHostingerToken() {
    const token = document.getElementById('hostingerToken').value.trim();
    if (!token) return alert('أدخل التوكن');
    const r = await fetch('/hostinger/configure', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({token})
    }).then(r => r.json());
    if (r.success) {
        alert('✅ تم الاتصال بـ Hostinger');
        checkHostingerStatus();
    } else {
        alert('❌ فشل: ' + JSON.stringify(r.test_result));
    }
}

async function loadHostingerSummary() {
    const s = await fetch('/hostinger/summary').then(r => r.json());
    document.getElementById('vpsCount').textContent = s.vps?.count ?? '—';
    document.getElementById('sitesCount').textContent = s.websites?.count ?? '—';
    document.getElementById('domainsCount').textContent = s.domains?.count ?? '—';
    
    // Render VPS table
    const tbody = document.getElementById('vpsTable');
    tbody.innerHTML = (s.vps?.list || []).map(v => `
        <tr>
            <td>${v.hostname || v.id}</td>
            <td>${v.ipv4 || '—'}</td>
            <td><span class="status-${v.state}">${v.state}</span></td>
            <td>${v.resources?.cpus}cpu / ${v.resources?.memory}MB</td>
            <td>
                <button onclick="loadVpsMetrics(${v.id})">📊</button>
                <button onclick="vpsAction(${v.id}, 'restart')">🔄</button>
                <button onclick="vpsAction(${v.id}, 'snapshot')">💾</button>
            </td>
        </tr>
    `).join('');
}

async function vpsAction(vmId, action) {
    const needsConfirm = ['restart', 'stop'].includes(action);
    if (needsConfirm && !confirm(`هل أنت متأكد من ${action}؟`)) return;
    const r = await fetch(`/hostinger/vps/${vmId}/action`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action, confirm: true})
    }).then(r => r.json());
    alert(r.ok ? '✅ تم' : '❌ ' + r.error);
}

async function loadVpsMetrics(vmId) {
    const r = await fetch(`/hostinger/vps/${vmId}/metrics`).then(r => r.json());
    document.getElementById('vpsMetrics').hidden = false;
    // ارسم الرسم البياني باستخدام Chart.js (حمّلها من CDN في <head>)
    // ... (chart code)
}

// initial
checkHostingerStatus();
</script>
```

### 📌 المهمة H4: أضف Hostinger إلى LLM Tools

في `llm_tools.py` (تم إضافته سابقًا في المهمة D1) تأكّد أن `get_hosting_info` فعّال — سيرجع `hostinger_client.get_summary()`.

أضف أدوات إضافية:
```python
{
    "name": "hostinger_list_vps",
    "description": "List all VPS instances on Hostinger account.",
    "input_schema": {"type": "object", "properties": {}}
},
{
    "name": "hostinger_vps_metrics",
    "description": "Get performance metrics (CPU, RAM, disk, network) for a specific VPS. Returns historical data.",
    "input_schema": {
        "type": "object",
        "properties": {"vm_id": {"type": "integer"}},
        "required": ["vm_id"]
    }
}
```

وفي `execute_tool`:
```python
if name == "hostinger_list_vps":
    from hostinger_client import hostinger_client
    return hostinger_client.list_vps()

if name == "hostinger_vps_metrics":
    from hostinger_client import hostinger_client
    return hostinger_client.get_vps_metrics(args.get("vm_id"))
```

✅ **اختبار دفعة H**:
1. احصل على Hostinger API token من hPanel.
2. في الداشبورد: Settings → Hostinger → الصق التوكن → اضغط "حفظ واختبار".
3. يجب أن تظهر: VPS count، Websites count، Domains count.
4. اضغط على VPS → يجب ظهور tabulated list.
5. اختبر tool-use:
   ```bash
   curl -X POST http://127.0.0.1:5001/wp/ai/chat \
     -H "Content-Type: application/json" \
     -d '{"message":"ما استخدام الـ CPU في خادم VPS الأحدث خلال آخر 24 ساعة؟"}'
   ```
   يجب أن تظهر `tool_calls: [hostinger_list_vps, hostinger_vps_metrics]`.

---

# ═══════════════════════════════════════
# 🧪 اختبارات القبول النهائية
# ═══════════════════════════════════════

بعد إتمام كل الدفعات (A-H)، شغّل هذه الاختبارات بترتيبها:

### T1 — السلامة
```bash
curl -X POST http://127.0.0.1:5001/wp/operator/run \
  -H "Content-Type: application/json" \
  -d '{"task":"شخّص أخطاء الموقع ولا تصلح شيئًا","site":"mbt"}'
```
✅ النتيجة تحتوي `requires_confirmation: true` و`mode: suggested_only`، ولا تعطيل plugin فعلي.

### T2 — ربط endpoints
```bash
curl -X POST http://127.0.0.1:5001/wp/create-course \
  -H "Content-Type: application/json" \
  -d '{"site":"mbt","title":"اختبار","content":"وصف"}'
```
✅ يُنشأ كورس في `stm-courses` (ليس 404).

### T3 — حقن المعرفة
```bash
# ارفع ملف knowledge عن Elementor
curl -X POST http://127.0.0.1:5001/knowledge/upload \
  -F "file=@elementor_guide.txt" -F "tags=elementor,guide"

# نفذ مهمة تعتمد على المعرفة
curl -X POST http://127.0.0.1:5001/wp/operator/run \
  -H "Content-Type: application/json" \
  -d '{"task":"حلّل إعدادات Elementor في الموقع","site":"mbt"}'
```
✅ النتيجة تحتوي `knowledge_used >= 1`.

### T4 — Tool-use الذكي (الأهم)
```bash
# اضبط .env أولًا: LLM_PROVIDER=claude, LLM_API_KEY=xxx, LLM_MODEL=claude-sonnet-4-5

curl -X POST http://127.0.0.1:5001/wp/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"كم عدد الإضافات النشطة في mbt، وأيها يحتاج تحديثًا؟"}'
```
✅ النتيجة:
- `final`: نص طبيعي يذكر عددًا حقيقيًا.
- `tool_calls`: `[{"tool":"list_sites"}, {"tool":"list_plugins"}]`.
- `iterations`: 2-3.

### T5 — MasterStudy + Resources
في الداشبورد:
1. أنشئ كورس جديد بعنوان "Python للمبتدئين".
2. أضف 2 روابط موارد (مثلًا: docs.python.org).
3. ارفع ملف PDF تعليمي.
4. فعّل "توليد دروس تلقائيًا".
5. اضغط "إنشاء".

✅ يجب:
- إنشاء كورس في WP `stm-courses`.
- حفظ الموارد في `post_meta(course, 'aiwa_resources')`.
- رفع PDF إلى `wp-content/uploads`.
- إضافة محتوى PDF إلى `knowledge_base`.
- 5 دروس مُولَّدة تعتمد على محتوى الموارد.

### T6 — Hostinger
1. في الداشبورد: صفحة Hostinger → أدخل token → اضغط حفظ.
2. تحقق من ظهور VPS list و Websites list.
3. اضغط "📊" على VPS واحد → يظهر metrics.

✅ البيانات حقيقية من Hostinger API (VPS count، IP، state).

### T7 — الداشبورد
- كل card يعرض رقمًا حقيقيًا أو "—".
- Live ticker يُحدَّث كل 10 ثوانٍ.
- Active Tools تظهر calls > 0 (بعد أي مهمة).
- AI Assistant يعرض tool chips عند كل رد.
- لا توجد قيم hard-coded مثل "55.6%" بدون بيانات فعلية.
- Sidebar يحتوي: Overview, Sites, Plugins, Users, Elementor, MasterStudy, Knowledge, Self-Heal, **Hostinger**, **AI Assistant**, Settings.

---

# ═══════════════════════════════════════
# 📤 التسليم
# ═══════════════════════════════════════

بعد انتهاء كل دفعة، أرسل:

1. **قائمة الملفات المُعدَّلة** + عدد الأسطر المُضافة/المحذوفة لكل ملف.
2. **نتائج اختبارات القبول** للدفعة.
3. **الملفات الجديدة** (مثل `llm_tools.py`، `hostinger_client.py`، `hostinger_routes.py`، `wp-dashboard-v2.html`).
4. **آخر 50 سطر** من `mcp.log` و`flask.log`.
5. **screenshot** للداشبورد بعد تطبيق الدفعة F (استخدم `smart_screenshot` tool).

---

# ═══════════════════════════════════════
# 🎯 المعايير النهائية للنجاح
# ═══════════════════════════════════════

النظام ناجح عندما:

- ✅ Claude (عبر API key) يستخدم **6+ أدوات فعلية** في مهمة واحدة ("حلّل موقعي").
- ✅ الداشبورد يشبه WordPress Admin بصريًا (sidebar داكن، cards بيضاء، ألوان WP).
- ✅ كل معلومة في الداشبورد مربوطة بـ endpoint حقيقي (لا وهم).
- ✅ إنشاء كورس MasterStudy مع 3+ موارد PDF/URL ينجح في أقل من دقيقتين.
- ✅ Hostinger API token يُضبط من الداشبورد ويعرض VPS metrics مباشرة.
- ✅ أي "Fatal error" يُشخَّص ولا يُصلَح تلقائيًا دون `confirm=true`.
- ✅ Success Rate > 80% بعد 20 مهمة اختبار.

---

**ابدأ الآن بـ المهمة A1 (Backup).**
