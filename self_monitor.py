import time
from collections import deque
from logger_system import get_logger

logger = get_logger("self_monitor")


class SelfMonitor:
    """
    نظام مراقبة ذاتي لتحليل الأداء وتحسين القرارات
    """

    def __init__(self):
        """
        تهيئة النظام مع cache بسيط
        """
        self.history = deque(maxlen=20)
        self.issues = []

    def evaluate_task(self, result: dict):
        """
        تحليل نتيجة task
        """
        try:
            success = result.get("status") == "completed"
            steps = result.get("steps", [])

            failures = len([s for s in steps if s.get("status") == "failed"])
            retries = len([s for s in steps if s.get("status") == "retry"])

            record = {
                "success": success,
                "failures": failures,
                "retries": retries,
                "timestamp": time.time()
            }

            self.history.append(record)
            logger.info("Task evaluated", context=record)

            return record

        except Exception as e:
            logger.error("Evaluation failed", error=e)
            return {}

    def detect_issues(self):
        """
        كشف المشاكل في الأداء
        """
        self.issues.clear()

        try:
            if not self.history:
                return []

            recent = list(self.history)[-5:]

            # repeated failures
            if sum(1 for r in recent if not r["success"]) >= 3:
                self.issues.append("repeated_failures")

            # high retries
            if any(r["retries"] > 2 for r in recent):
                self.issues.append("high_retries")

            # slow execution (heuristic)
            if len(self.history) >= 5:
                self.issues.append("possible_slow_execution")

            logger.warning("Issues detected", context={"issues": self.issues})
            return self.issues

        except Exception as e:
            logger.error("Issue detection failed", error=e)
            return []

    def suggest_improvements(self):
        """
        اقتراح تحسينات بناءً على المشاكل
        """
        suggestions = []

        try:
            issues = self.detect_issues()

            if "repeated_failures" in issues:
                suggestions.append("change_strategy")

            if "high_retries" in issues:
                suggestions.append("optimize_dependencies")

            if "possible_slow_execution" in issues:
                suggestions.append("optimize_execution_flow")

            logger.info("Suggestions generated", context={"suggestions": suggestions})

            return suggestions

        except Exception as e:
            logger.error("Suggestion failed", error=e)
            return []

    def log_reflection(self):
        """
        تسجيل التفكير الذاتي
        """
        try:
            reflection = {
                "history_size": len(self.history),
                "issues": self.issues
            }

            logger.info("Self reflection", context=reflection)
            return reflection

        except Exception as e:
            logger.error("Reflection failed", error=e)
            return {}
