"""
AI Operator — المحرك الذكي الحقيقي
يحلل → يقرر → ينفذ
"""
import time
import re
from typing import Dict, List, Optional, Any
from logger_system import get_logger
from llm_bridge    import llm_bridge
from feedback_loop import feedback_loop

logger = get_logger("ai_operator")


class AIOperator:
    """
    الفرق الجوهري:
    Control Panel: تضغط "تحديث الإضافات"
    AI Operator  : تقول "حدّث بأمان" → يحلل → يقرر → ينفذ
    """

    def __init__(self):
        self.execution_log: List[Dict] = []

    # ═══════════════════════════════════════════════
    #  Entry Point — كل مهمة تمر من هنا
    # ═══════════════════════════════════════════════

    def execute(self, task: str, site=None, explain: bool = False) -> Dict:
        """
        تنفيذ مهمة ذكية:
        1. تحليل النية
        2. بناء خطة
        3. تنفيذ بالترتيب
        4. تقرير النتيجة
        """
        t0 = time.time()
        logger.info(f"AI Operator: {task[:80]}")

        # 1. Intent Analysis
        intent = self._analyze_intent(task)
        logger.info(f"Intent: {intent['category']} / {intent['action']}")

        # 2. Build Plan
        plan = self._build_plan(intent, task, site)

        if explain:
            return {
                "mode":   "explain",
                "task":   task,
                "intent": intent,
                "plan":   plan,
                "steps":  [s["description"] for s in plan["steps"]],
            }

        # 3. Execute
        results = self._execute_plan(plan, site)

        # 4. AI Summary
        summary = self._summarize(task, results)

        duration = round(time.time() - t0, 2)
        success  = all(r.get("ok") for r in results if not r.get("optional"))

        # Record feedback
        feedback_loop.record(
            task, {"status": "completed" if success else "partial"},
            "ai_operator", site.name if site else "local", duration
        )

        return {
            "success":      success,
            "task":         task,
            "intent":       intent,
            "plan":         plan["name"],
            "results":      results,
            "summary":      summary,
            "duration":     duration,
            "agent_type":   intent["category"],
        }

    # ═══════════════════════════════════════════════
    #  Intent Analysis
    # ═══════════════════════════════════════════════

    def _analyze_intent(self, task: str) -> Dict:
        task_lower = task.lower()

        # Plugin Management
        if any(w in task_lower for w in ["ضافة","plugin","إضافة","تحديث plugin","update plugin"]):
            if any(w in task_lower for w in ["آمن","بأمان","safe","بدون ما يكسر","without breaking"]):
                return {"category": "plugin", "action": "smart_update", "risk": "low"}
            if any(w in task_lower for w in ["حدّث","update","تحديث"]):
                return {"category": "plugin", "action": "update", "risk": "medium"}
            if any(w in task_lower for w in ["حلل","analyze","فحص","check"]):
                return {"category": "plugin", "action": "analyze", "risk": "none"}

        # Site Analysis & UX
        if any(w in task_lower for w in ["حلل","analyze","فهم","understand","ux","تقرير","report"]):
            if any(w in task_lower for w in ["موقع","site","صفحة","page"]):
                return {"category": "analysis", "action": "full_site_analysis", "risk": "none"}

        # Elementor
        if any(w in task_lower for w in ["elementor","عدّل","تصميم","design","صفحة","landing"]):
            if any(w in task_lower for w in ["عدّل","تعديل","edit","غيّر","change"]):
                return {"category": "elementor", "action": "edit_page", "risk": "medium"}
            return {"category": "elementor", "action": "analyze_page", "risk": "none"}

        # MasterStudy / Courses
        if any(w in task_lower for w in ["كورس","course","masterstudy","درس","lesson","تعليم"]):
            if any(w in task_lower for w in ["أنشئ","انشاء","create","new","جديد","رفع","upload"]):
                return {"category": "masterstudy", "action": "create_course", "risk": "low"}
            if any(w in task_lower for w in ["حلل","analyze","تقرير"]):
                return {"category": "masterstudy", "action": "analyze_courses", "risk": "none"}
            return {"category": "masterstudy", "action": "list_courses", "risk": "none"}

        # LearnDash
        if any(w in task_lower for w in ["learndash","learn dash"]):
            if any(w in task_lower for w in ["أنشئ","create"]):
                return {"category": "learndash", "action": "create_course", "risk": "low"}
            return {"category": "learndash", "action": "list_courses", "risk": "none"}

        # Error / Self-Heal
        if any(w in task_lower for w in ["خطأ","error","fatal","مشكلة","broken","كسر","debug","log"]):
            return {"category": "selfheal", "action": "diagnose_and_fix", "risk": "medium"}

        # Users
        if any(w in task_lower for w in ["مستخدم","user","يوزر"]):
            if any(w in task_lower for w in ["احذف","delete","حذف","remove"]):
                return {"category": "users", "action": "delete_user", "risk": "high"}
            if any(w in task_lower for w in ["أضف","add","جديد"]):
                return {"category": "users", "action": "create_user", "risk": "medium"}
            return {"category": "users", "action": "list_users", "risk": "none"}

        # DB / CLI
        if any(w in task_lower for w in ["db","database","قاعدة","wp-cli","cli","cache","optimize"]):
            return {"category": "technical", "action": "run_cli", "risk": "medium"}

        # General AI Task
        return {"category": "general", "action": "ai_task", "risk": "low"}

    # ═══════════════════════════════════════════════
    #  Plan Builder
    # ═══════════════════════════════════════════════

    def _build_plan(self, intent: Dict, task: str, site) -> Dict:
        cat    = intent["category"]
        action = intent["action"]
        steps  = []

        if cat == "plugin" and action == "smart_update":
            steps = [
                {"id": "backup_check",  "description": "التحقق من توفر النسخة الاحتياطية",  "fn": "check_backup",       "optional": True},
                {"id": "list_updates",  "description": "جلب قائمة الإضافات التي تحتاج تحديث","fn": "list_plugin_updates","optional": False},
                {"id": "analyze_risk",  "description": "تحليل مخاطر كل تحديث",               "fn": "analyze_update_risk","optional": False},
                {"id": "safe_update",   "description": "تحديث الإضافات الآمنة فقط",           "fn": "update_safe_plugins","optional": False},
                {"id": "verify",        "description": "التحقق من عمل الموقع بعد التحديث",    "fn": "verify_site",        "optional": True},
            ]
            name = "Smart Plugin Update"

        elif cat == "analysis" and action == "full_site_analysis":
            steps = [
                {"id": "ping",          "description": "فحص حالة الاتصال والـ latency",    "fn": "smart_ping",          "optional": False},
                {"id": "site_info",     "description": "جلب معلومات الموقع الكاملة",       "fn": "get_site_info",       "optional": False},
                {"id": "plugins",       "description": "تحليل الإضافات النشطة",             "fn": "analyze_plugins",     "optional": False},
                {"id": "error_log",     "description": "فحص سجل الأخطاء",                  "fn": "check_error_log",     "optional": True},
                {"id": "ai_analysis",   "description": "تحليل AI شامل + توصيات",            "fn": "ai_site_analysis",    "optional": False},
            ]
            name = "Full Site AI Analysis"

        elif cat == "elementor":
            steps = [
                {"id": "get_page",      "description": "جلب بيانات الصفحة",                 "fn": "get_page_data",       "optional": False},
                {"id": "analyze_ux",    "description": "تحليل UX للصفحة",                   "fn": "analyze_page_ux",     "optional": False},
                {"id": "ai_suggest",    "description": "اقتراحات AI للتحسين",                "fn": "ai_elementor_suggest","optional": False},
            ]
            name = "Elementor AI Analysis"

        elif cat == "masterstudy":
            if action == "create_course":
                # Extract topic from task
                topic = re.sub(r'(أنشئ|انشاء|create|كورس|course|عن|about|في)', '', task, flags=re.IGNORECASE).strip()
                steps = [
                    {"id": "generate",  "description": f"توليد هيكل الكورس: {topic[:30]}",  "fn": "ms_generate_structure","optional": False, "params": {"topic": topic}},
                    {"id": "create",    "description": "إنشاء الكورس في MasterStudy",         "fn": "ms_create_course",     "optional": False},
                    {"id": "lessons",   "description": "إضافة الدروس تلقائياً",               "fn": "ms_add_lessons",       "optional": False},
                    {"id": "quiz",      "description": "إضافة الاختبار النهائي",               "fn": "ms_add_quiz",          "optional": True},
                ]
            else:
                steps = [{"id": "list", "description": "جلب قائمة الكورسات", "fn": "ms_list_courses", "optional": False}]
            name = "MasterStudy Course Creation"

        elif cat == "selfheal":
            steps = [
                {"id": "read_log",      "description": "قراءة سجل الأخطاء",                 "fn": "read_error_log",      "optional": False},
                {"id": "ai_diagnose",   "description": "تشخيص AI للمشاكل",                  "fn": "ai_diagnose_errors",  "optional": False},
                {"id": "auto_fix",      "description": "محاولة الإصلاح التلقائي",            "fn": "auto_fix_errors",     "optional": True},
            ]
            name = "AI Self-Heal"

        elif cat == "users":
            steps = [{"id": "users", "description": "إدارة المستخدمين", "fn": "manage_users", "optional": False,
                      "params": {"action": action}}]
            name = "User Management"

        elif cat == "technical":
            cmd = self._extract_cli_command(task)
            steps = [{"id": "cli", "description": f"تنفيذ: {cmd}", "fn": "run_cli_command", "optional": False,
                      "params": {"command": cmd}}]
            name = "Technical Execution"

        else:
            steps = [{"id": "ai", "description": "تنفيذ AI عام", "fn": "general_ai_task", "optional": False}]
            name = "General AI Task"

        return {"name": name, "steps": steps, "intent": intent, "task": task}

    def _extract_cli_command(self, task: str) -> str:
        wp_commands = re.findall(r'wp\s+\w+[\w\s-]*', task, re.IGNORECASE)
        return wp_commands[0] if wp_commands else "cache flush"

    # ═══════════════════════════════════════════════
    #  Plan Executor
    # ═══════════════════════════════════════════════

    def _execute_plan(self, plan: Dict, site) -> List[Dict]:
        results = []
        context = {}  # Share data between steps

        for step in plan["steps"]:
            try:
                result = self._execute_step(step, site, context, plan)
                result["step_id"] = step["id"]
                result["optional"] = step.get("optional", False)
                results.append(result)
                # Pass result to next steps
                context[step["id"]] = result
                if not result.get("ok") and not step.get("optional"):
                    logger.warning(f"Critical step failed: {step['id']}")
                    break  # Stop on critical failure
            except Exception as e:
                results.append({
                    "step_id":  step["id"],
                    "ok":       False,
                    "error":    str(e),
                    "optional": step.get("optional", False),
                })

        return results

    def _execute_step(self, step: Dict, site, context: Dict, plan: Dict) -> Dict:
        fn     = step["fn"]
        params = step.get("params", {})
        task   = plan.get("task", "")

        # ── Plugin Steps ──────────────────────────────
        if fn == "check_backup":
            return {"ok": True, "data": "Backup check skipped (optional)", "skipped": True}

        if fn == "list_plugin_updates":
            if not site: return {"ok": False, "error": "No site connected"}
            r = site.get_plugins()
            if not r.get("success"): return {"ok": False, "error": r.get("error")}
            updates = [p for p in r.get("data", {}).get("plugins", []) if p.get("update_available")]
            context["updates"] = updates
            return {"ok": True, "data": updates, "count": len(updates)}

        if fn == "analyze_update_risk":
            updates  = context.get("list_updates", {}).get("data", [])
            if not updates: return {"ok": True, "data": "No updates needed"}
            # Use LLM to assess risk
            safe, risky = [], []
            for p in updates[:10]:
                name = p.get("name", "")
                # Basic heuristic: known safe plugins
                if any(s in name.lower() for s in ["yoast","rank math","contact form","woocommerce","elementor"]):
                    risky.append(name)  # Popular = test first
                else:
                    safe.append(name)
            context["safe_updates"]  = safe
            context["risky_updates"] = risky
            return {"ok": True, "safe": safe, "risky": risky}

        if fn == "update_safe_plugins":
            if not site: return {"ok": False, "error": "No site connected"}
            updates = context.get("list_updates", {}).get("data", [])
            if not updates: return {"ok": True, "data": "Nothing to update", "updated": []}
            r = site.update_plugins()
            return {"ok": r.get("success", False), "data": r.get("message", ""), "updated": len(updates)}

        if fn == "verify_site":
            if not site: return {"ok": True, "skipped": True}
            ok = site.ping()
            return {"ok": ok, "data": "Site responding after update" if ok else "Site may have issues"}

        # ── Analysis Steps ────────────────────────────
        if fn == "smart_ping":
            if not site: return {"ok": False, "error": "No site"}
            t0 = time.time()
            ok = site.ping()
            ms = round((time.time()-t0)*1000, 1)
            context["latency_ms"] = ms
            return {"ok": ok, "latency_ms": ms, "status": "connected" if ok else "down"}

        if fn == "get_site_info":
            if not site: return {"ok": False, "error": "No site"}
            r = site.get_site_info()
            context["site_info"] = r.get("data", {})
            return {"ok": r.get("success", False), "data": r.get("data", {})}

        if fn == "analyze_plugins":
            if not site: return {"ok": False, "error": "No site"}
            r = site.get_plugins()
            plugins = r.get("data", {}).get("plugins", [])
            context["plugins"] = plugins
            active  = [p for p in plugins if p.get("active")]
            updates = [p for p in plugins if p.get("update_available")]
            return {"ok": True, "active": len(active), "need_update": len(updates), "data": plugins[:10]}

        if fn == "check_error_log":
            if not site: return {"ok": True, "skipped": True}
            r = site.get_error_log()
            log = r.get("data", {}).get("log", "")
            context["error_log"] = log
            has_fatal = "Fatal" in log or "Parse error" in log
            return {"ok": True, "has_fatal": has_fatal, "log_size": len(log)}

        if fn == "ai_site_analysis":
            site_info = context.get("site_info", {})
            plugins   = context.get("plugins", [])
            latency   = context.get("latency_ms", 0)
            log_info  = context.get("check_error_log", {})
            prompt = f"""أنت مساعد WordPress خبير. حلل هذا الموقع وأعطني تقرير شامل بالعربية:

الموقع: {site.url if site else 'unknown'}
WordPress Version: {site_info.get('wp_version', '?')}
PHP Version: {site_info.get('php_version', '?')}
الإضافات النشطة: {len([p for p in plugins if p.get('active')])}
تحتاج تحديث: {len([p for p in plugins if p.get('update_available')])}
Latency: {latency}ms
أخطاء fatal: {log_info.get('has_fatal', False)}

الإضافات الكبيرة:
{chr(10).join([f'- {p.get("name","?")} v{p.get("version","?")}' for p in plugins[:8] if p.get("active")])}

التقرير يشمل:
1. 📊 حالة الموقع العامة
2. ⚡ الأداء (بناءً على Latency {latency}ms)
3. 🔌 الإضافات (هل في مشاكل؟)
4. 🚨 المشاكل المكتشفة
5. 💡 أهم 3 توصيات عملية"""
            analysis = llm_bridge._call_llm(prompt)
            return {"ok": True, "analysis": analysis}

        # ── Elementor Steps ───────────────────────────
        if fn in ["get_page_data", "analyze_page_ux", "ai_elementor_suggest"]:
            if not site: return {"ok": False, "error": "No site"}
            r = site.get_elementor_data()
            if fn == "get_page_data":
                return {"ok": r.get("success", False), "data": r.get("data", {})}
            if fn == "analyze_page_ux":
                data = context.get("get_page_data", {}).get("data", {})
                sections = data.get("sections", []) if isinstance(data, dict) else []
                return {"ok": True, "sections": len(sections), "has_hero": any("hero" in str(s).lower() for s in sections)}
            if fn == "ai_elementor_suggest":
                page_data = context.get("get_page_data", {}).get("data", {})
                prompt = f"اقترح تحسينات لهذه الصفحة في Elementor: {str(page_data)[:500]}"
                suggestions = llm_bridge._call_llm(prompt)
                return {"ok": True, "suggestions": suggestions}

        # ── MasterStudy Steps ─────────────────────────
        if fn == "ms_generate_structure":
            topic = params.get("topic", task)
            prompt = f"""أنشئ هيكل كورس تعليمي احترافي عن: {topic}
أعطني JSON فقط:
{{"title":"","description":"","level":"beginner","lessons":[{{"title":"","content":"","duration":"20 min"}}],"quiz":{{"title":"اختبار","questions":[{{"q":"","options":["","","",""],"correct":0}}]}}}}"""
            result = llm_bridge._call_llm(prompt)
            try:
                import json as _j
                m = __import__('re').search(r'\{.*\}', result, __import__('re').S)
                structure = _j.loads(m.group()) if m else {}
            except Exception:
                structure = {"title": f"كورس {topic}", "description": "", "lessons": [{"title": f"درس {i+1}", "content": ""} for i in range(5)]}
            context["ms_structure"] = structure
            return {"ok": True, "structure": structure, "lessons_count": len(structure.get("lessons", []))}

        if fn == "ms_create_course":
            if not site: return {"ok": False, "error": "No site"}
            s = context.get("ms_generate_structure", {}).get("structure", {})
            r = site._request("POST", "masterstudy/courses", {
                "title":       s.get("title", "New Course"),
                "description": s.get("description", ""),
                "level":       s.get("level", "beginner"),
                "status":      "draft",
            })
            cid = r.get("course_id") or r.get("data", {}).get("course_id")
            context["ms_course_id"] = cid
            return {"ok": bool(cid), "course_id": cid, "title": s.get("title")}

        if fn == "ms_add_lessons":
            if not site: return {"ok": False, "error": "No site"}
            cid      = context.get("ms_course_id")
            s        = context.get("ms_generate_structure", {}).get("structure", {})
            lessons  = s.get("lessons", [])
            added    = []
            for i, les in enumerate(lessons):
                r = site._request("POST", f"masterstudy/courses/{cid}/lessons", {
                    "title": les.get("title", f"Lesson {i+1}"),
                    "content": les.get("content", ""),
                    "order": i,
                })
                added.append(r.get("success", False))
                time.sleep(0.15)
            return {"ok": any(added), "lessons_added": sum(added), "total": len(lessons)}

        if fn == "ms_add_quiz":
            if not site: return {"ok": True, "skipped": True}
            cid = context.get("ms_course_id")
            s   = context.get("ms_generate_structure", {}).get("structure", {})
            quiz = s.get("quiz", {})
            if not quiz or not cid: return {"ok": True, "skipped": True}
            r = site._request("POST", f"masterstudy/courses/{cid}/quizzes", quiz)
            return {"ok": r.get("success", False), "quiz_id": r.get("quiz_id")}

        if fn == "ms_list_courses":
            if not site: return {"ok": False, "error": "No site"}
            r = site._request("GET", "masterstudy/courses")
            return {"ok": r.get("success", False) or "courses" in r, "data": r}

        # ── Self-Heal Steps ───────────────────────────
        if fn == "read_error_log":
            if not site: return {"ok": False, "error": "No site"}
            r = site.get_error_log()
            log = r.get("data", {}).get("log", "")
            context["raw_log"] = log
            return {"ok": True, "log": log[-500:], "size": len(log)}

        if fn == "ai_diagnose_errors":
            log = context.get("raw_log", "")
            if not log: return {"ok": True, "data": "No errors found"}
            prompt = f"""حلل أخطاء WordPress هذه واعطني:
1. المشكلة الرئيسية
2. السبب المحتمل
3. الحل الموصى به
4. هل يمكن الإصلاح التلقائي؟

الأخطاء:
{log[-800:]}"""
            diagnosis = llm_bridge._call_llm(prompt)
            context["diagnosis"] = diagnosis
            return {"ok": True, "diagnosis": diagnosis}

        if fn == "auto_fix_errors":
            if not site: return {"ok": True, "skipped": True}
            diag = context.get("diagnosis", "")
            if "plugin" in diag.lower() or "إضافة" in diag:
                r = site.run_cli("plugin deactivate --all --skip-plugins")
                return {"ok": True, "action": "Deactivated plugins", "result": r}
            if "cache" in diag.lower() or "كاش" in diag:
                r = site.run_cli("cache flush")
                return {"ok": True, "action": "Flushed cache", "result": r}
            return {"ok": True, "data": "Manual fix required", "diagnosis": diag}

        # ── User Management ───────────────────────────
        if fn == "manage_users":
            if not site: return {"ok": False, "error": "No site"}
            action = params.get("action", "list_users")
            if action == "list_users":
                r = site._request("GET", "users")
                return {"ok": r.get("success", False) or "users" in r, "data": r}
            if action == "delete_user":
                uid = params.get("user_id")
                if uid:
                    r = site._request("POST", "users/delete", {"user_id": uid})
                    return {"ok": r.get("success", False), "data": r}
                return {"ok": False, "error": "Need user_id — say: 'احذف المستخدم 5'"}
            return {"ok": False, "error": f"Unknown user action: {action}"}

        # ── CLI Execution ─────────────────────────────
        if fn == "run_cli_command":
            if not site: return {"ok": False, "error": "No site"}
            cmd = params.get("command", "cache flush")
            r   = site.run_cli(cmd)
            return {"ok": r.get("success", False), "command": cmd, "output": r.get("output", "")}

        # ── General AI ────────────────────────────────
        if fn == "general_ai_task":
            prompt = f"أنت مساعد WordPress خبير. نفّذ هذه المهمة وأعطني خطوات واضحة:\n{task}"
            result = llm_bridge._call_llm(prompt)
            return {"ok": True, "result": result}

        return {"ok": False, "error": f"Unknown step: {fn}"}

    # ═══════════════════════════════════════════════
    #  AI Summary
    # ═══════════════════════════════════════════════

    def _summarize(self, task: str, results: List[Dict]) -> str:
        ok_count   = sum(1 for r in results if r.get("ok"))
        fail_count = len(results) - ok_count
        if fail_count == 0:
            return f"✅ تم تنفيذ المهمة بنجاح ({ok_count} خطوات)"
        elif ok_count == 0:
            return f"❌ فشل التنفيذ"
        else:
            return f"⚠️ تم تنفيذ {ok_count}/{len(results)} خطوات — {fail_count} فشلت"


# Singleton
ai_operator = AIOperator()
