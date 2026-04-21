"""
WordPress Manager — Python Client
يتواصل مع مواقع WordPress عبر REST API الخاص بالـ Plugin
دعم Multi-Site + Heartbeat + Self-Heal + Elementor + LearnDash
"""

import json
import time
import threading
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, List, Optional, Any
from logger_system import get_logger

logger = get_logger("wp_manager")


class WordPressSite:
    """يمثل موقع WordPress واحد"""

    def __init__(self, name: str, url: str, api_key: str):
        self.name    = name
        self.url     = url.rstrip("/")
        self.api_key = api_key
        self.base    = f"{self.url}/wp-json/ai-agent/v1"
        self.connected = False
        self.last_ping = None
        self.info: Dict = {}

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type":   "application/json",
            "X-AI-Agent-Key": self.api_key,
            "User-Agent":     "AI-WP-Agent/2.0",
        }

    def _request(self, method: str, endpoint: str, data: Dict = None, timeout: int = 15) -> Dict:
        url = f"{self.base}/{endpoint.lstrip('/')}"
        body = json.dumps(data).encode() if data else None
        req  = urllib.request.Request(url, data=body, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                content = resp.read().decode("utf-8")
                return {"success": True, "data": json.loads(content), "status": resp.status}
        except urllib.error.HTTPError as e:
            body_txt = e.read().decode("utf-8", errors="ignore")
            return {"success": False, "error": f"HTTP {e.code}", "body": body_txt}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Connection ────────────────────────
    def ping(self) -> bool:
        r = self._request("GET", "ping")
        self.connected = r.get("success", False)
        if self.connected:
            self.last_ping = time.time()
        return self.connected

    def get_site_info(self) -> Dict:
        r = self._request("GET", "site-info")
        if r["success"]:
            self.info = r["data"]
        return r

    # ── Plugins ───────────────────────────
    def get_plugins(self) -> Dict:
        return self._request("GET", "plugins")

    def update_all_plugins(self) -> Dict:
        return self._request("POST", "update-plugins")

    def toggle_plugin(self, plugin_file: str, action: str = "activate") -> Dict:
        return self._request("POST", "toggle-plugin", {"plugin": plugin_file, "action": action})

    # ── Users ─────────────────────────────
    def get_users(self) -> Dict:
        return self._request("GET", "users")

    def create_user(self, username: str, email: str) -> Dict:
        return self._request("POST", "manage-users", {"action": "create", "username": username, "email": email})

    def delete_user(self, user_id: int) -> Dict:
        return self._request("POST", "manage-users", {"action": "delete", "user_id": user_id})

    # ── Media ─────────────────────────────
    def get_media(self) -> Dict:
        return self._request("POST", "manage-media")

    # ── Import / Export ───────────────────
    def import_xml(self, xml_content: str) -> Dict:
        return self._request("POST", "import-xml", {"xml_content": xml_content})

    def export_data(self, post_type: str = "posts") -> Dict:
        return self._request("GET", f"export-data?type={post_type}")

    # ── Elementor ─────────────────────────
    def get_elementor_data(self, post_id: int) -> Dict:
        return self._request("GET", f"elementor-data?post_id={post_id}")

    def update_elementor_data(self, post_id: int, elementor_data: Any) -> Dict:
        return self._request("POST", "elementor-data", {"post_id": post_id, "elementor_data": elementor_data})

    # ── LearnDash ─────────────────────────
    def get_courses(self) -> Dict:
        return self._request("GET", "learndash-courses")

    def create_course(self, title: str, content: str = "", status: str = "draft", meta: Dict = None) -> Dict:
        return self._request("POST", "learndash-courses", {"title": title, "content": content, "status": status, "meta": meta or {}})

    # ── WP-CLI ────────────────────────────
    def run_cli(self, command: str) -> Dict:
        return self._request("POST", "run-cli", {"command": command})

    # ── Error Log ─────────────────────────
    def get_error_log(self) -> Dict:
        return self._request("GET", "error-log")

    def __repr__(self):
        status = "✅" if self.connected else "❌"
        return f"WordPressSite({status} {self.name} → {self.url})"


# ─────────────────────────────────────────────────────
#  MULTI-SITE MANAGER
# ─────────────────────────────────────────────────────

class WPManager:
    """
    إدارة عدة مواقع WordPress من مكان واحد
    """

    def __init__(self):
        self._sites: Dict[str, WordPressSite] = {}
        self._lock  = threading.RLock()
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._running = False
        logger.info("WPManager initialized")

    def add_site(self, name: str, url: str, api_key: str) -> WordPressSite:
        with self._lock:
            site = WordPressSite(name, url, api_key)
            self._sites[name] = site
            logger.info("Site added", context={"name": name, "url": url})
            return site

    def remove_site(self, name: str):
        with self._lock:
            if name in self._sites:
                del self._sites[name]

    def get_site(self, name: str) -> Optional[WordPressSite]:
        return self._sites.get(name)

    def list_sites(self) -> List[str]:
        return list(self._sites.keys())

    def get_all_sites(self) -> List[WordPressSite]:
        return list(self._sites.values())

    # ── Bulk Operations ───────────────────
    def ping_all(self) -> Dict[str, bool]:
        results = {}
        for name, site in self._sites.items():
            results[name] = site.ping()
        return results

    def execute_on_all(self, method: str, *args, **kwargs) -> Dict[str, Any]:
        """تنفيذ أي عملية على كل المواقع"""
        results = {}
        for name, site in self._sites.items():
            try:
                fn = getattr(site, method, None)
                if fn:
                    results[name] = fn(*args, **kwargs)
                else:
                    results[name] = {"success": False, "error": f"Method '{method}' not found"}
            except Exception as e:
                results[name] = {"success": False, "error": str(e)}
        return results

    def update_all_plugins_everywhere(self) -> Dict[str, Any]:
        return self.execute_on_all("update_all_plugins")

    # ── Heartbeat ─────────────────────────
    def start_heartbeat(self, interval: int = 60):
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return
        self._running = True
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            args=(interval,),
            daemon=True,
            name="WPHeartbeat"
        )
        self._heartbeat_thread.start()
        logger.info("Heartbeat started", context={"interval": interval})

    def stop_heartbeat(self):
        self._running = False

    def _heartbeat_loop(self, interval: int):
        while self._running:
            for name, site in list(self._sites.items()):
                try:
                    was_connected = site.connected
                    site.ping()
                    if site.connected != was_connected:
                        status = "connected" if site.connected else "disconnected"
                        logger.info(f"Site {status}", context={"site": name})
                except Exception as e:
                    logger.error("Heartbeat failed", error=e, context={"site": name})
            time.sleep(interval)

    # ── AI Analysis ───────────────────────
    def analyze_site(self, name: str) -> Dict:
        """
        تحليل AI للموقع:
        - نوع الموقع
        - المشاكل
        - التحسينات المقترحة
        """
        site = self.get_site(name)
        if not site:
            return {"error": "Site not found"}

        info_r = site.get_site_info()
        if not info_r["success"]:
            return {"error": "Cannot connect", "details": info_r}

        info    = info_r["data"]
        plugins = site.get_plugins().get("data", {}).get("plugins", [])
        errors  = site.get_error_log().get("data", {})

        # تحليل نوع الموقع
        site_type  = self._detect_site_type(plugins)
        problems   = self._detect_problems(info, plugins, errors)
        suggestions = self._generate_suggestions(problems, site_type)

        return {
            "site":        name,
            "url":         site.url,
            "type":        site_type,
            "problems":    problems,
            "suggestions": suggestions,
            "info":        info,
        }

    def _detect_site_type(self, plugins: List[Dict]) -> str:
        names = " ".join([p.get("name","").lower() for p in plugins])
        if "learndash" in names or "lifterlms" in names or "tutor" in names:
            return "LMS / تعليمي"
        if "woocommerce" in names or "edd" in names:
            return "متجر إلكتروني"
        if "elementor" in names or "divi" in names:
            return "موقع تصميمي"
        return "موقع عام"

    def _detect_problems(self, info: Dict, plugins: List, errors: Dict) -> List[str]:
        problems = []
        if info.get("debug_mode"):
            problems.append("⚠️ WP_DEBUG مفعّل في بيئة Production")
        inactive = [p for p in plugins if not p.get("active")]
        if len(inactive) > 5:
            problems.append(f"⚠️ {len(inactive)} إضافة غير مفعلة (ثقل غير ضروري)")
        updates = [p for p in plugins if p.get("has_update")]
        if updates:
            problems.append(f"🔄 {len(updates)} إضافة تحتاج تحديث")
        log = errors.get("log", "")
        if "Fatal" in log or "Parse error" in log:
            problems.append("🔴 أخطاء PHP Fatal موجودة في debug.log")
        return problems

    def _generate_suggestions(self, problems: List[str], site_type: str) -> List[str]:
        suggestions = []
        for p in problems:
            if "DEBUG" in p:
                suggestions.append("تعطيل WP_DEBUG في wp-config.php")
            if "تحديث" in p:
                suggestions.append("تحديث كل الإضافات عبر AI Agent")
            if "Fatal" in p:
                suggestions.append("تفعيل Self-Heal Firewall لإصلاح تلقائي")
        if site_type == "LMS / تعليمي":
            suggestions.append("تحسين تجربة الطلاب بمراجعة إعدادات LearnDash")
        return suggestions

    def __repr__(self):
        return f"WPManager({len(self._sites)} sites: {list(self._sites.keys())})"


# Singleton
wp_manager = WPManager()
