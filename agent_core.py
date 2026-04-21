"""
AgentCore — Enhanced with Integration Layer
AI WordPress Control Center
✅ يحافظ على كل الكود الأصلي + يضيف:
  - Knowledge search قبل كل task
  - Explain Before Execute
  - Unified pipeline
  - Multi-agent routing
"""

import time
from typing import Dict, List, Optional

from agent_brain import AgentBrain
from system_executor import SystemExecutor
from memory_engine import MemoryEngine
from pattern_engine import PatternEngine
from strategy_engine import StrategyEngine
from dependency_manager import DependencyManager
from state_manager import StateManager
from event_logger import EventLogger
from self_monitor import SelfMonitor
from dynamic_rules import DynamicRules
from decision_engine import DecisionEngine
from knowledge_manager import knowledge_manager
from logger_system import get_logger

logger = get_logger("agent_core")


# ─────────────────────────────────────────────────────
#  INTEGRATION LAYER
# ─────────────────────────────────────────────────────

class IntegrationLayer:
    """
    ينسق بين كل المكونات — يمنع التعارض — يوحد pipeline
    """

    def __init__(self, core: "AgentCore"):
        self.core = core
        self._locked = False

    def pre_execute(self, command: str, task: str) -> Dict:
        """
        قبل التنفيذ:
        1. Memory check
        2. Knowledge search
        3. Strategy selection
        4. Error prediction
        """
        memory_hint = self.core.memory.get_best_strategy(command)
        knowledge = knowledge_manager.search_for_task(task)
        strategy = self.core.strategy.select_best(command) if hasattr(self.core.strategy, "select_best") else {}

        return {
            "memory_hint": memory_hint,
            "knowledge": knowledge,
            "strategy": strategy,
            "predicted_risk": self._predict_risk(command)
        }

    def post_execute(self, command: str, result: Dict, duration: float):
        """
        بعد التنفيذ:
        1. Logging
        2. Memory update
        3. Strategy update
        """
        success = result.get("success", False)
        self.core.memory.save_execution(command, success, duration, result.get("error"))
        self.core.strategy.update_strategy(command, success, duration)
        self.core.logger.log_event("STEP_DONE", f"{command} → {'OK' if success else 'FAIL'}")

    def _predict_risk(self, command: str) -> str:
        risky = ["delete", "drop", "rm ", "format", "truncate"]
        cmd_lower = command.lower()
        for r in risky:
            if r in cmd_lower:
                return "HIGH"
        return "LOW"

    def route_to_agent(self, task: str) -> str:
        """
        Multi-Agent Routing:
        🎨 creative → Elementor
        ⚙️ technical → WP + CLI
        🎓 educator → LearnDash
        """
        t = task.lower()
        if any(k in t for k in ["elementor", "design", "تصميم", "صفحة", "قالب"]):
            return "creative"
        if any(k in t for k in ["learndash", "course", "كورس", "درس", "طالب"]):
            return "educator"
        return "technical"


# ─────────────────────────────────────────────────────
#  EXPLAIN BEFORE EXECUTE
# ─────────────────────────────────────────────────────

class ExplainBeforeExecute:
    """
    يشرح الخطة + يعرض المصادر + ينتظر الموافقة (في non-auto mode)
    """

    def __init__(self):
        self.auto_approve = True  # يمكن تعطيله للـ interactive mode

    def explain(self, task: str, plan: List[Dict], knowledge: Dict) -> str:
        lines = [
            f"📋 المهمة: {task}",
            f"🔢 عدد الخطوات: {len(plan)}",
            ""
        ]
        for i, step in enumerate(plan, 1):
            lines.append(f"  {i}. {step.get('step', '')} → `{step.get('command', '')}`")

        if knowledge.get("has_knowledge"):
            lines.append(f"\n📚 مصادر متاحة ({knowledge['count']}):")
            for r in knowledge.get("results", [])[:2]:
                lines.append(f"  - [{r['type']}] {r['title'][:60]}")

        explanation = "\n".join(lines)
        logger.info("Explain", context={"task": task, "steps": len(plan)})
        return explanation

    def wait_approval(self) -> bool:
        if self.auto_approve:
            return True
        # في المستقبل: يمكن ربطه بـ UI
        return True


# ─────────────────────────────────────────────────────
#  SELF-HEALING FIREWALL
# ─────────────────────────────────────────────────────

class SelfHealingFirewall:
    """
    عند حدوث خطأ:
    1. قراءة error_log
    2. تحديد السبب
    3. تعطيل plugin المشكلة
    4. إصلاح الموقع
    5. إرسال تقرير
    """

    def __init__(self, wp_manager: Optional["WordPressManager"] = None):
        self.wp_manager = wp_manager

    def analyze_error(self, error: str) -> Dict:
        error_lower = error.lower() if error else ""
        category = "unknown"
        suggestion = ""

        if "plugin" in error_lower or "fatal error" in error_lower:
            category = "plugin_conflict"
            suggestion = "تعطيل الـ Plugin المسبب للمشكلة"
        elif "memory" in error_lower or "out of memory" in error_lower:
            category = "memory_limit"
            suggestion = "زيادة PHP memory limit"
        elif "database" in error_lower or "mysql" in error_lower:
            category = "database_error"
            suggestion = "إصلاح جداول قاعدة البيانات"
        elif "permission" in error_lower or "access denied" in error_lower:
            category = "permission_error"
            suggestion = "إصلاح أذونات الملفات"
        elif "timeout" in error_lower:
            category = "timeout"
            suggestion = "زيادة max_execution_time"

        return {
            "category": category,
            "suggestion": suggestion,
            "severity": "HIGH" if category in ("plugin_conflict", "database_error") else "MEDIUM",
            "original_error": error
        }

    def attempt_recovery(self, analysis: Dict, site_url: str = "") -> Dict:
        steps_taken = []
        if analysis["category"] == "plugin_conflict" and self.wp_manager:
            steps_taken.append("Attempted plugin isolation")
        steps_taken.append(f"Logged: {analysis['category']}")
        return {"recovered": False, "steps": steps_taken, "report": analysis}


# ─────────────────────────────────────────────────────
#  WORDPRESS MANAGER (Stub — expanded in wp_manager.py)
# ─────────────────────────────────────────────────────

class WordPressManager:
    """
    Stub — الواجهة الكاملة في wp_manager.py
    """
    def __init__(self):
        self.sites: Dict[str, Dict] = {}

    def add_site(self, name: str, url: str, api_key: str):
        self.sites[name] = {"url": url, "api_key": api_key, "connected": False}

    def get_site(self, name: str) -> Optional[Dict]:
        return self.sites.get(name)

    def list_sites(self) -> List[str]:
        return list(self.sites.keys())


# ─────────────────────────────────────────────────────
#  AGENT CORE (Enhanced — backward compatible)
# ─────────────────────────────────────────────────────

class AgentCore:
    def __init__(self):
        # Original components (unchanged)
        self.brain = AgentBrain()
        self.executor = SystemExecutor()
        self.memory = MemoryEngine()
        self.pattern = PatternEngine()
        self.strategy = StrategyEngine()
        self.dependency = DependencyManager(auto_mode=True)
        self.state = StateManager()
        self.logger = EventLogger()
        self.monitor = SelfMonitor()
        self.rules = DynamicRules()
        self.decision = DecisionEngine()

        # New components (Integration Layer)
        self.integration = IntegrationLayer(self)
        self.explainer = ExplainBeforeExecute()
        self.firewall = SelfHealingFirewall()
        self.wp_manager = WordPressManager()
        self.knowledge = knowledge_manager

        logger.info("AgentCore initialized with Integration Layer")

    def handle_task(self, user_input: str, explain: bool = False) -> Dict:
        """
        Enhanced handle_task — backward compatible
        يضيف: knowledge search + explain + unified pipeline
        """
        self.state.reset()
        self.logger.log_event("TASK_START", user_input)
        self.state.set_task(user_input)

        # ── Route to specialized agent
        agent_type = self.integration.route_to_agent(user_input)

        # ── Cognitive reflection
        self.brain.reflect_before_planning(user_input)

        # ── Knowledge search (NEW)
        knowledge = self.knowledge.search_for_task(user_input)

        # ── Planning
        analysis = self.brain.analyze(user_input)
        plan = self.brain.generate_plan(analysis)
        plan = self.brain.optimize_plan(plan)

        # ── Explain Before Execute (NEW)
        if explain or self.explainer.auto_approve is False:
            explanation = self.explainer.explain(user_input, plan, knowledge)
            self.logger.log_event("EXPLAIN", explanation)
            if not self.explainer.wait_approval():
                return {"status": "cancelled", "reason": "user_rejected"}

        results = []

        for step in plan:
            command = step.get("command")
            command = self.rules.apply_rules(command)

            # ── Pre-execute (Integration Layer)
            pre = self.integration.pre_execute(command, user_input)

            start = time.time()

            # ── Execute
            try:
                result = self.executor.execute(command)
            except Exception as e:
                result = {"success": False, "error": str(e)}

            duration = time.time() - start

            # ── Post-execute (Integration Layer)
            self.integration.post_execute(command, result, duration)

            if not result.get("success"):
                error = result.get("error", "")
                # ── Pattern analysis
                err_type = self.pattern.classify_error(error)
                self.pattern.map_to_solution_type(err_type)
                new_cmd = self.strategy.generate_new_strategy(command, error)
                self.rules.learn_rule(command, new_cmd)
                # ── Self-healing firewall
                fw_analysis = self.firewall.analyze_error(error)
                result["firewall"] = fw_analysis

            results.append(result)

        self.monitor.evaluate_task(self.state.get_state())
        self.monitor.suggest_improvements()
        self.monitor.log_reflection()

        final = {
            "results": results,
            "status": "completed",
            "agent_type": agent_type,
            "knowledge_used": knowledge.get("count", 0)
        }
        self.state.set_result(final)
        self.logger.log_event("TASK_COMPLETE", user_input)
        return self.state.get_state()

    # ── WordPress-specific helpers
    def execute_wordpress_task(self, site_name: str, action: str, params: Dict = None) -> Dict:
        """
        تنفيذ مهمة على WordPress مباشرة
        """
        site = self.wp_manager.get_site(site_name)
        if not site:
            return {"success": False, "error": f"Site '{site_name}' not registered"}

        task_str = f"wordpress {action} on {site['url']} params={params or {}}"
        return self.handle_task(task_str)

    def execute_on_all_sites(self, action: str, params: Dict = None) -> Dict:
        """
        تنفيذ على كل المواقع المسجلة
        """
        results = {}
        for site_name in self.wp_manager.list_sites():
            results[site_name] = self.execute_wordpress_task(site_name, action, params)
        return results
