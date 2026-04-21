"""
System Awareness — الوعي الكامل بحالة النظام
Agent يعرف في أي لحظة:
  - الموقع الحالي
  - الأداة المستخدمة
  - حالة الاتصال
  - حالة التنفيذ
  - Local vs Remote mode
"""

import time
import threading
from typing import Dict, Optional, List, Any
from logger_system import get_logger

logger = get_logger("system_awareness")


class ExecutionMode:
    LOCAL  = "local"   # التحكم في الملفات + تشغيل Agent
    REMOTE = "remote"  # التحكم في WordPress عبر Plugin API


class ConnectionState:
    CONNECTED    = "connected"
    DISCONNECTED = "disconnected"
    ERROR        = "error"
    UNKNOWN      = "unknown"


class SiteState:
    def __init__(self, name: str, url: str):
        self.name          = name
        self.url           = url
        self.connection    = ConnectionState.UNKNOWN
        self.last_ping     = None
        self.wp_version    = None
        self.plugins_count = 0
        self.active_plugin = 0
        self.has_errors    = False
        self.error_msg     = ""
        self.latency_ms    = 0

    def update_ping(self, success: bool, latency_ms: float = 0, info: Dict = None):
        self.last_ping  = time.time()
        self.latency_ms = latency_ms
        if success:
            self.connection = ConnectionState.CONNECTED
            if info:
                self.wp_version    = info.get("wp_version")
                self.plugins_count = info.get("plugins_total", 0)
                self.active_plugin = info.get("plugins_active", 0)
        else:
            self.connection = ConnectionState.DISCONNECTED

    def to_dict(self) -> Dict:
        return {
            "name":          self.name,
            "url":           self.url,
            "connection":    self.connection,
            "last_ping":     self.last_ping,
            "wp_version":    self.wp_version,
            "plugins_total": self.plugins_count,
            "plugins_active":self.active_plugin,
            "has_errors":    self.has_errors,
            "latency_ms":    round(self.latency_ms, 1),
            "seconds_since_ping": round(time.time() - self.last_ping, 0) if self.last_ping else None,
        }


class SystemAwareness:
    """
    النواة المركزية للوعي بحالة النظام
    """

    def __init__(self):
        self._lock           = threading.RLock()

        # Current State
        self.current_task:   Optional[str]  = None
        self.current_tool:   Optional[str]  = None
        self.current_site:   Optional[str]  = None
        self.execution_mode: str            = ExecutionMode.LOCAL
        self.is_running:     bool           = False
        self.start_time:     float          = time.time()

        # Sites
        self._sites: Dict[str, SiteState]  = {}

        # Heartbeat
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._hb_running:       bool       = False
        self._hb_callbacks:     List       = []

        # Stats
        self.tasks_done:    int  = 0
        self.tasks_failed:  int  = 0
        self.total_uptime:  float = 0

        logger.info("SystemAwareness initialized")

    # ─── Task Tracking ────────────────────
    def begin_task(self, task: str, tool: str = None, site: str = None):
        with self._lock:
            self.current_task = task
            self.current_tool = tool
            self.is_running   = True
            if site:
                self.current_site  = site
                self.execution_mode = ExecutionMode.REMOTE
            else:
                self.execution_mode = ExecutionMode.LOCAL

    def end_task(self, success: bool = True):
        with self._lock:
            self.is_running   = False
            self.current_task = None
            self.current_tool = None
            if success:
                self.tasks_done += 1
            else:
                self.tasks_failed += 1

    def set_tool(self, tool_name: str):
        with self._lock:
            self.current_tool = tool_name

    # ─── Site Management ─────────────────
    def register_site(self, name: str, url: str) -> SiteState:
        with self._lock:
            if name not in self._sites:
                self._sites[name] = SiteState(name, url)
                logger.info("Site registered in awareness", context={"name": name})
            return self._sites[name]

    def update_site_ping(self, name: str, success: bool,
                         latency_ms: float = 0, info: Dict = None):
        with self._lock:
            if name in self._sites:
                self._sites[name].update_ping(success, latency_ms, info)

    def get_site(self, name: str) -> Optional[SiteState]:
        return self._sites.get(name)

    def get_all_sites(self) -> List[Dict]:
        return [s.to_dict() for s in self._sites.values()]

    def get_connected_sites(self) -> List[str]:
        return [n for n, s in self._sites.items() if s.connection == ConnectionState.CONNECTED]

    # ─── Heartbeat ────────────────────────
    def start_heartbeat(self, wp_manager, interval: int = 60):
        if self._hb_running:
            return
        self._hb_running = True
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            args=(wp_manager, interval),
            daemon=True,
            name="SystemHeartbeat"
        )
        self._heartbeat_thread.start()
        logger.info("Heartbeat started", context={"interval": interval})

    def stop_heartbeat(self):
        self._hb_running = False

    def _heartbeat_loop(self, wp_manager, interval: int):
        while self._hb_running:
            for name, site_state in list(self._sites.items()):
                site = wp_manager.get_site(name)
                if not site:
                    continue
                try:
                    t0 = time.time()
                    ok = site.ping()
                    latency = (time.time() - t0) * 1000
                    info    = site.info if ok else {}
                    self.update_site_ping(name, ok, latency, info)

                    # Fire callbacks
                    for cb in self._hb_callbacks:
                        try:
                            cb(name, ok, site_state.to_dict())
                        except Exception:
                            pass
                except Exception as e:
                    self.update_site_ping(name, False)
                    logger.error("Heartbeat ping failed", error=e, context={"site": name})
            time.sleep(interval)

    def on_heartbeat(self, callback):
        """تسجيل callback يُستدعى عند كل heartbeat"""
        self._hb_callbacks.append(callback)

    # ─── Snapshot ─────────────────────────
    def get_snapshot(self) -> Dict:
        with self._lock:
            uptime = time.time() - self.start_time
            return {
                "current_task":    self.current_task,
                "current_tool":    self.current_tool,
                "current_site":    self.current_site,
                "execution_mode":  self.execution_mode,
                "is_running":      self.is_running,
                "uptime_seconds":  round(uptime),
                "tasks_done":      self.tasks_done,
                "tasks_failed":    self.tasks_failed,
                "success_rate":    round(self.tasks_done / max(1, self.tasks_done + self.tasks_failed) * 100, 1),
                "sites":           self.get_all_sites(),
                "connected_sites": self.get_connected_sites(),
            }


# Singleton
system_awareness = SystemAwareness()
