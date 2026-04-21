"""
Feedback Loop — بعد كل عملية:
1. تسجيل النتيجة
2. تحليل النجاح أو الفشل
3. تحديث Memory
4. تحسين Strategy
5. إبلاغ الـ Dashboard
"""

import time
import json
import sqlite3
import threading
from typing import Dict, List, Optional, Callable
from logger_system import get_logger

logger = get_logger("feedback_loop")
DB_PATH = r"C:\mcp-agent\agent_state.db"


class FeedbackRecord:
    def __init__(self, task: str, tool: str, site: str,
                 success: bool, duration: float,
                 result: Dict, error: str = ""):
        self.task      = task
        self.tool      = tool
        self.site      = site
        self.success   = success
        self.duration  = duration
        self.result    = result
        self.error     = error
        self.timestamp = time.time()
        self.score     = self._calculate_score()

    def _calculate_score(self) -> float:
        """0.0 → 1.0"""
        if not self.success:
            return 0.0
        base = 1.0
        if self.duration > 10:
            base -= 0.2
        elif self.duration > 5:
            base -= 0.1
        return max(0.0, base)

    def to_dict(self) -> Dict:
        return {
            "task":      self.task,
            "tool":      self.tool,
            "site":      self.site,
            "success":   self.success,
            "duration":  self.duration,
            "score":     self.score,
            "error":     self.error,
            "timestamp": self.timestamp,
        }


class FeedbackLoop:
    """
    حلقة التغذية الراجعة — تحسين مستمر بعد كل تنفيذ
    """

    def __init__(self):
        self._lock      = threading.RLock()
        self._callbacks: List[Callable] = []   # للـ Dashboard
        self._init_db()
        logger.info("FeedbackLoop initialized")

    def _connect(self):
        return sqlite3.connect(DB_PATH, check_same_thread=False)

    def _init_db(self):
        conn = self._connect()
        cur  = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT,
            tool TEXT,
            site TEXT,
            success INTEGER,
            duration REAL,
            score REAL,
            error TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        conn.close()

    # ─────────────────────────────────────────
    #  MAIN: record
    # ─────────────────────────────────────────

    def record(self, task: str, result: Dict,
               tool: str = "", site: str = "",
               duration: float = 0.0,
               memory_engine=None, strategy_engine=None) -> FeedbackRecord:
        """
        الدالة الرئيسية — تُستدعى بعد كل تنفيذ
        """
        success = result.get("status") == "completed" or result.get("success", False)
        error   = str(result.get("error", ""))

        rec = FeedbackRecord(task, tool, site, success, duration, result, error)

        # 1. حفظ في DB
        self._save(rec)

        # 2. تحديث Memory
        if memory_engine:
            try:
                memory_engine.save_execution(task, success, duration, error or None)
            except Exception as e:
                logger.error("Memory update failed", error=e)

        # 3. تحديث Strategy
        if strategy_engine:
            try:
                strategy_engine.update_strategy(task, success, duration)
            except Exception as e:
                logger.error("Strategy update failed", error=e)

        # 4. إبلاغ Dashboard
        self._notify(rec)

        # 5. Log
        status_str = "✅ SUCCESS" if success else "❌ FAILED"
        logger.info(f"Feedback [{status_str}] score={rec.score:.2f}",
                    context={"task": task[:50], "duration": duration})

        return rec

    # ─────────────────────────────────────────
    #  ANALYSIS
    # ─────────────────────────────────────────

    def get_recent(self, limit: int = 20) -> List[Dict]:
        conn = self._connect()
        cur  = conn.cursor()
        cur.execute("""
        SELECT task, tool, site, success, duration, score, error, created_at
        FROM feedback_log ORDER BY id DESC LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        conn.close()
        return [
            {"task": r[0], "tool": r[1], "site": r[2],
             "success": bool(r[3]), "duration": r[4],
             "score": r[5], "error": r[6], "time": r[7]}
            for r in rows
        ]

    def get_stats(self) -> Dict:
        conn = self._connect()
        cur  = conn.cursor()
        cur.execute("""
        SELECT
            COUNT(*) as total,
            SUM(success) as successes,
            AVG(duration) as avg_duration,
            AVG(score) as avg_score,
            MAX(created_at) as last_task
        FROM feedback_log
        """)
        row = cur.fetchone()
        conn.close()
        if not row or not row[0]:
            return {"total": 0, "success_rate": 0, "avg_duration": 0, "avg_score": 0}
        total     = row[0]
        successes = row[1] or 0
        return {
            "total":        total,
            "successes":    successes,
            "failures":     total - successes,
            "success_rate": round(successes / total * 100, 1),
            "avg_duration": round(row[2] or 0, 2),
            "avg_score":    round(row[3] or 0, 2),
            "last_task":    row[4],
        }

    def get_failing_patterns(self) -> List[Dict]:
        """أكثر المهام التي تفشل"""
        conn = self._connect()
        cur  = conn.cursor()
        cur.execute("""
        SELECT tool, COUNT(*) as total, SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as failures
        FROM feedback_log
        GROUP BY tool
        HAVING failures > 0
        ORDER BY failures DESC
        LIMIT 10
        """)
        rows = cur.fetchall()
        conn.close()
        return [{"tool": r[0], "total": r[1], "failures": r[2],
                 "fail_rate": round(r[2]/r[1]*100, 1)} for r in rows]

    def suggest_improvements(self) -> List[str]:
        """اقتراحات تحسين بناءً على البيانات"""
        stats    = self.get_stats()
        patterns = self.get_failing_patterns()
        tips     = []
        if stats.get("total", 0) > 0 and stats.get("success_rate", 100) < 70:
            tips.append("⚠️ معدل النجاح منخفض — راجع إعدادات الاتصال بالمواقع")
        if stats.get("avg_duration", 0) > 8:
            tips.append("⏱️ متوسط وقت التنفيذ مرتفع — فكر في تحسين الـ Strategy")
        for p in patterns[:2]:
            if p["fail_rate"] > 50:
                tips.append(f"🔴 أداة '{p['tool']}' فشلت {p['fail_rate']}% من الوقت")
        return tips or ["✅ النظام يعمل بكفاءة عالية"]

    # ─────────────────────────────────────────
    #  DASHBOARD CALLBACKS
    # ─────────────────────────────────────────

    def on_result(self, callback: Callable):
        """ربط Dashboard بالـ Feedback Loop مباشرة"""
        self._callbacks.append(callback)

    def _notify(self, rec: FeedbackRecord):
        for cb in self._callbacks:
            try:
                cb(rec.to_dict())
            except Exception as e:
                logger.error("Callback failed", error=e)

    def _save(self, rec: FeedbackRecord):
        try:
            conn = self._connect()
            cur  = conn.cursor()
            cur.execute("""
            INSERT INTO feedback_log (task, tool, site, success, duration, score, error, result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (rec.task, rec.tool, rec.site, int(rec.success),
                  rec.duration, rec.score, rec.error, json.dumps(rec.result)))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Feedback save failed", error=e)


# Singleton
feedback_loop = FeedbackLoop()
