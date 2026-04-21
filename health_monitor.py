"""
Health Monitor — مراقبة مستمرة لكل المواقع والنظام
- يرصد حالة كل موقع كل 60 ثانية
- يكتشف المشاكل تلقائياً
- يُطلق Self-Heal عند الحاجة
- يُحدّث الـ Dashboard في الوقت الفعلي
"""

import time
import threading
from typing import Dict, List, Callable, Optional
from logger_system    import get_logger
from system_awareness import system_awareness
from feedback_loop    import feedback_loop

logger = get_logger("health_monitor")


class HealthEvent:
    SITE_UP       = "site_up"
    SITE_DOWN     = "site_down"
    PLUGIN_ERROR  = "plugin_error"
    HIGH_LATENCY  = "high_latency"
    DB_ERROR      = "db_error"
    MEMORY_LOW    = "memory_low"
    AUTO_HEALED   = "auto_healed"
    AGENT_IDLE    = "agent_idle"


class HealthMonitor:
    """مراقب الصحة المركزي"""

    LATENCY_WARN_MS   = 2000   # تحذير إذا تجاوز 2 ثانية
    LATENCY_CRIT_MS   = 5000   # حرج إذا تجاوز 5 ثوانٍ
    CHECK_INTERVAL    = 60     # ثانية
    AUTO_HEAL_ENABLED = True

    def __init__(self):
        self._thread:    Optional[threading.Thread] = None
        self._running:   bool  = False
        self._callbacks: List[Callable] = []
        self._events:    List[Dict]     = []
        self._lock       = threading.RLock()
        self._wp_manager = None
        logger.info("HealthMonitor initialized")

    # ─── Start / Stop ─────────────────────────
    def start(self, wp_manager, interval: int = None):
        if self._running:
            return
        self._wp_manager = wp_manager
        self._interval   = interval or self.CHECK_INTERVAL
        self._running    = True
        self._thread     = threading.Thread(
            target=self._loop, daemon=True, name="HealthMonitor"
        )
        self._thread.start()
        logger.info("HealthMonitor started", context={"interval": self._interval})

    def stop(self):
        self._running = False

    # ─── Main Loop ────────────────────────────
    def _loop(self):
        while self._running:
            try:
                self._check_all_sites()
                self._check_agent_health()
            except Exception as e:
                logger.error("HealthMonitor loop error", error=e)
            time.sleep(self._interval)

    def _check_all_sites(self):
        if not self._wp_manager:
            return
        for site in self._wp_manager.get_all_sites():
            try:
                self._check_site(site)
            except Exception as e:
                logger.error("Site check failed", error=e,
                             context={"site": site.name})

    def _check_site(self, site):
        name = site.name
        t0   = time.time()
        ok   = site.ping()
        ms   = (time.time() - t0) * 1000

        # Update awareness
        system_awareness.update_site_ping(name, ok, ms, site.info)

        if ok:
            self._emit(HealthEvent.SITE_UP, name, {"latency_ms": ms})

            # Latency check
            if ms > self.LATENCY_CRIT_MS:
                self._emit(HealthEvent.HIGH_LATENCY, name,
                           {"latency_ms": ms, "level": "critical"})
            elif ms > self.LATENCY_WARN_MS:
                self._emit(HealthEvent.HIGH_LATENCY, name,
                           {"latency_ms": ms, "level": "warning"})

            # Error log check (if connected)
            self._check_error_log(site)

        else:
            self._emit(HealthEvent.SITE_DOWN, name, {"latency_ms": ms})
            logger.info(f"Site DOWN: {name}")

    def _check_error_log(self, site):
        try:
            r   = site.get_error_log()
            log = r.get("data", {}).get("log", "") if r.get("success") else ""
            if not log:
                return

            if "Fatal" in log or "Parse error" in log:
                self._emit(HealthEvent.PLUGIN_ERROR, site.name,
                           {"log_snippet": log[-200:]})
                if self.AUTO_HEAL_ENABLED:
                    self._auto_heal(site, log)

            if "MySQL" in log or "database" in log.lower():
                self._emit(HealthEvent.DB_ERROR, site.name,
                           {"log_snippet": log[-200:]})
        except Exception:
            pass

    def _auto_heal(self, site, error_log: str):
        try:
            from agent_core import SelfHealingFirewall
            fw       = SelfHealingFirewall()
            analysis = fw.analyze_error(error_log[:500])
            recovery = fw.attempt_recovery(analysis, site.url)
            self._emit(HealthEvent.AUTO_HEALED, site.name,
                       {"analysis": analysis, "recovery": recovery})
            logger.info(f"Auto-heal triggered for {site.name}",
                        context={"category": analysis.get("category")})
        except Exception as e:
            logger.error("Auto-heal failed", error=e)

    def _check_agent_health(self):
        snap = system_awareness.get_snapshot()
        if not snap["is_running"] and snap["uptime_seconds"] > 300:
            self._emit(HealthEvent.AGENT_IDLE, "agent",
                       {"uptime": snap["uptime_seconds"],
                        "tasks_done": snap["tasks_done"]})

    # ─── Events ───────────────────────────────
    def _emit(self, event_type: str, source: str, data: Dict = None):
        event = {
            "type":      event_type,
            "source":    source,
            "data":      data or {},
            "timestamp": time.time(),
        }
        with self._lock:
            self._events.append(event)
            if len(self._events) > 500:
                self._events = self._events[-500:]

        for cb in self._callbacks:
            try:
                cb(event)
            except Exception:
                pass

    def on_event(self, callback: Callable):
        self._callbacks.append(callback)

    # ─── Queries ──────────────────────────────
    def get_recent_events(self, limit: int = 50) -> List[Dict]:
        with self._lock:
            return list(reversed(self._events[-limit:]))

    def get_site_health(self, site_name: str) -> Dict:
        snap  = system_awareness.get_site(site_name)
        if not snap:
            return {"site": site_name, "status": "unknown"}
        d = snap.to_dict()

        # latency rating
        ms = d.get("latency_ms", 0)
        rating = "good" if ms < 500 else "warn" if ms < 2000 else "critical"
        d["latency_rating"] = rating

        # time since last ping
        since = d.get("seconds_since_ping")
        d["stale"] = since is not None and since > 120

        return d

    def get_all_health(self) -> Dict:
        return {
            "sites": [
                self.get_site_health(name)
                for name in (self._wp_manager.list_sites()
                             if self._wp_manager else [])
            ],
            "agent":  system_awareness.get_snapshot(),
            "events": self.get_recent_events(10),
            "feedback": feedback_loop.get_stats(),
        }

    def get_summary(self) -> Dict:
        sites     = system_awareness.get_all_sites()
        connected = [s for s in sites if s["connection"] == "connected"]
        errors    = [s for s in sites if s.get("has_errors")]
        recent    = self.get_recent_events(5)
        return {
            "total_sites":     len(sites),
            "connected_sites": len(connected),
            "sites_with_errors": len(errors),
            "recent_events":   len(self._events),
            "auto_heal_on":    self.AUTO_HEAL_ENABLED,
            "last_events":     recent,
        }


# ── Singleton
health_monitor = HealthMonitor()
