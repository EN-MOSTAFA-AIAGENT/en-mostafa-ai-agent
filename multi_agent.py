"""
Multi-Agent System — AI WordPress Control Center
تقسيم الأدوار:
  CreativeAgent   → Elementor / Design
  TechnicalAgent  → WP + CLI + Plugins
  EducatorAgent   → LearnDash / Courses
كل Agent يعمل مستقلاً ويُنسَّق عبر AgentOrchestrator
"""

import time
import threading
from typing import Dict, List, Optional, Any
from logger_system import get_logger
from memory_engine  import MemoryEngine
from llm_bridge     import llm_bridge, LLMProvider
from feedback_loop  import feedback_loop
from knowledge_manager import knowledge_manager

logger = get_logger("multi_agent")


# ─────────────────────────────────────────────────────
#  BASE AGENT
# ─────────────────────────────────────────────────────

class BaseAgent:
    """الكلاس الأساسي لكل Agent"""

    role: str = "base"
    keywords: List[str] = []

    def __init__(self, name: str):
        self.name    = name
        self.memory  = MemoryEngine()
        self._busy   = False
        self._lock   = threading.RLock()
        self.tasks_done   = 0
        self.tasks_failed = 0
        logger.info(f"Agent ready: {name} [{self.role}]")

    def can_handle(self, task: str) -> bool:
        t = task.lower()
        return any(k in t for k in self.keywords)

    def handle(self, task: str, context: Dict = None, site=None) -> Dict:
        with self._lock:
            if self._busy:
                return {"success": False, "error": f"{self.name} is busy"}
            self._busy = True

        t0 = time.time()
        try:
            logger.info(f"[{self.name}] handling: {task[:50]}")

            # 1. Knowledge search
            knowledge = knowledge_manager.search_for_task(task)

            # 2. LLM planning
            ctx = {"agent": self.name, "role": self.role, **(context or {})}
            if site:
                ctx["site"] = getattr(site, "name", str(site))
                ctx["site_url"] = getattr(site, "url", "")
            plan = llm_bridge.think(task, ctx, knowledge.get("summary", ""))

            # 3. Execute
            result = self._execute(task, plan, site, knowledge)

            dur = time.time() - t0
            self.tasks_done += 1

            # 4. Feedback
            feedback_loop.record(
                task=task, result=result, tool=self.name,
                site=ctx.get("site", ""), duration=dur,
                memory_engine=self.memory
            )

            return {
                "success":     result.get("success", True),
                "agent":       self.name,
                "role":        self.role,
                "plan":        plan.get("plan", []),
                "explanation": plan.get("explanation", ""),
                "result":      result,
                "knowledge":   knowledge.get("count", 0),
                "duration":    round(dur, 2),
            }

        except Exception as e:
            self.tasks_failed += 1
            logger.error(f"[{self.name}] error", error=e)
            return {"success": False, "agent": self.name, "error": str(e)}
        finally:
            with self._lock:
                self._busy = False

    def _execute(self, task: str, plan: Dict, site, knowledge: Dict) -> Dict:
        """Override in each agent"""
        return {"success": True, "note": "Base execute — override in subclass"}

    def status(self) -> Dict:
        return {
            "name":         self.name,
            "role":         self.role,
            "busy":         self._busy,
            "tasks_done":   self.tasks_done,
            "tasks_failed": self.tasks_failed,
            "keywords":     self.keywords,
        }


# ─────────────────────────────────────────────────────
#  CREATIVE AGENT — Elementor / Design
# ─────────────────────────────────────────────────────

class CreativeAgent(BaseAgent):
    role     = "creative"
    keywords = [
        "elementor", "design", "تصميم", "صفحة", "قالب", "theme",
        "layout", "section", "widget", "color", "لون", "header",
        "footer", "landing", "هيدر", "فوتر", "بنر", "banner"
    ]

    def __init__(self):
        super().__init__("CreativeAgent")

    def _execute(self, task: str, plan: Dict, site, knowledge: Dict) -> Dict:
        steps = []
        t = task.lower()

        if site and hasattr(site, "get_elementor_data"):
            if "page" in t or "صفحة" in t:
                # محاولة استخراج post_id من المهمة
                import re
                ids = re.findall(r'\d+', task)
                post_id = int(ids[0]) if ids else 1
                r = site.get_elementor_data(post_id)
                steps.append({"action": "get_elementor_data", "post_id": post_id, "result": r})

            if "update" in t or "تعديل" in t or "تحديث" in t:
                steps.append({"action": "elementor_edit", "note": "LLM plan ready for edit"})

        llm_analysis = llm_bridge.plan_wordpress_task(
            f"Creative task: {task}",
            {"role": "creative", "note": "Elementor/design context"}
        )
        return {
            "success": True,
            "steps":   steps,
            "llm_steps": llm_analysis.get("steps", []),
            "note":    "CreativeAgent executed"
        }


# ─────────────────────────────────────────────────────
#  TECHNICAL AGENT — WP + CLI + Plugins
# ─────────────────────────────────────────────────────

class TechnicalAgent(BaseAgent):
    role     = "technical"
    keywords = [
        "plugin", "إضافة", "update", "تحديث", "install", "تثبيت",
        "cli", "wpcli", "wp-cli", "database", "قاعدة بيانات",
        "backup", "نسخة", "cache", "كاش", "error", "خطأ",
        "maintenance", "صيانة", "activate", "deactivate", "تفعيل",
        "حماية", "security", "performance", "أداء", "optimize"
    ]

    def __init__(self):
        super().__init__("TechnicalAgent")

    def _execute(self, task: str, plan: Dict, site, knowledge: Dict) -> Dict:
        steps  = []
        t      = task.lower()
        result = {"success": True, "steps": steps}

        if site:
            if "update" in t or "تحديث" in t:
                r = site.update_all_plugins()
                steps.append({"action": "update_plugins", "result": r})

            elif "error" in t or "خطأ" in t or "log" in t:
                r = site.get_error_log()
                log_text = r.get("data", {}).get("log", "")
                from agent_core import SelfHealingFirewall
                fw = SelfHealingFirewall()
                analysis = fw.analyze_error(log_text[:500])
                steps.append({"action": "read_error_log", "analysis": analysis})

            elif "cli" in t:
                import re
                cmd_match = re.search(r'(wp\s+\w+[\w\s]*)', task)
                if cmd_match:
                    r = site.run_cli(cmd_match.group(1).strip())
                    steps.append({"action": "run_cli", "result": r})

            elif "info" in t or "معلومات" in t:
                r = site.get_site_info()
                steps.append({"action": "site_info", "result": r})

        llm_plan = llm_bridge.plan_wordpress_task(
            f"Technical task: {task}",
            {"role": "technical"}
        )
        result["llm_steps"] = llm_plan.get("steps", [])
        result["steps"]     = steps
        return result


# ─────────────────────────────────────────────────────
#  EDUCATOR AGENT — LearnDash / Courses
# ─────────────────────────────────────────────────────

class EducatorAgent(BaseAgent):
    role     = "educator"
    keywords = [
        "learndash", "course", "كورس", "درس", "lesson", "quiz",
        "student", "طالب", "enrollment", "تسجيل", "certificate",
        "محتوى", "content", "curriculum", "منهج", "import", "xml",
        "تعليمي", "educational", "lms", "section", "topic"
    ]

    def __init__(self):
        super().__init__("EducatorAgent")

    def _execute(self, task: str, plan: Dict, site, knowledge: Dict) -> Dict:
        steps = []
        t     = task.lower()

        if site:
            if "create" in t or "إنشاء" in t or "أنشئ" in t:
                import re
                title_match = re.search(r"['\"](.+?)['\"]", task)
                title = title_match.group(1) if title_match else task[:40]

                # Use LLM to generate course content
                llm_content = llm_bridge.think(
                    f"Generate LearnDash course content for: {title}",
                    {"role": "educator", "task": task},
                    knowledge.get("summary", "")
                )
                content = llm_content.get("explanation", "")
                r = site.create_course(title, content, "draft")
                steps.append({"action": "create_course", "title": title, "result": r})

            elif "list" in t or "عرض" in t or "get" in t:
                r = site.get_courses()
                steps.append({"action": "list_courses", "result": r})

            elif "import" in t or "xml" in t:
                steps.append({"action": "import_xml", "note": "Provide XML content via API"})

        llm_plan = llm_bridge.plan_wordpress_task(
            f"Educational task: {task}",
            {"role": "educator"}
        )
        return {
            "success":   True,
            "steps":     steps,
            "llm_steps": llm_plan.get("steps", []),
            "note":      "EducatorAgent executed"
        }


# ─────────────────────────────────────────────────────
#  AGENT ORCHESTRATOR
# ─────────────────────────────────────────────────────

class AgentOrchestrator:
    """
    يُنسِّق بين العملاء — يختار الصحيح ويمنع التعارض
    """

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {
            "creative":  CreativeAgent(),
            "technical": TechnicalAgent(),
            "educator":  EducatorAgent(),
        }
        self._lock = threading.RLock()
        logger.info("AgentOrchestrator ready — 3 agents")

    def route(self, task: str) -> str:
        """يختار الـ Agent الأنسب"""
        for role, agent in self.agents.items():
            if agent.can_handle(task):
                return role
        return "technical"  # default

    def handle(self, task: str, site=None, context: Dict = None) -> Dict:
        """تنفيذ المهمة بالـ Agent الصحيح"""
        role  = self.route(task)
        agent = self.agents[role]

        logger.info(f"Routing to {role}: {task[:50]}")
        return agent.handle(task, context, site)

    def handle_all(self, task: str, sites: List = None) -> Dict:
        """تنفيذ على كل المواقع بالـ Agent الصحيح"""
        results = {}
        for site in (sites or []):
            name = getattr(site, "name", str(site))
            results[name] = self.handle(task, site, context={"site": name})
        return results

    def status(self) -> Dict:
        return {
            name: agent.status()
            for name, agent in self.agents.items()
        }

    def get_agent(self, role: str) -> Optional[BaseAgent]:
        return self.agents.get(role)

    def get_busy_agents(self) -> List[str]:
        return [n for n, a in self.agents.items() if a._busy]


# ─────────────────────────────────────────────────────
#  SINGLETON
# ─────────────────────────────────────────────────────

orchestrator = AgentOrchestrator()
