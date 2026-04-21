"""
Unified Tool Interface — AI WordPress Control Center
كل أداة لها: اسم، نوع، حالة
AgentCore هو المرجع الوحيد
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Any
from logger_system import get_logger

logger = get_logger("tool_registry")


class ToolStatus:
    ACTIVE = "active"
    IDLE   = "idle"
    ERROR  = "error"
    BUSY   = "busy"


class ToolType:
    ANALYSIS  = "analysis"
    EXECUTION = "execution"
    MEMORY    = "memory"
    BROWSER   = "browser"
    KNOWLEDGE = "knowledge"
    WP        = "wordpress"
    LLM       = "llm"


class RegisteredTool:
    def __init__(self, name: str, tool_type: str, instance: Any,
                 description: str = "", priority: int = 5):
        self.name        = name
        self.tool_type   = tool_type
        self.instance    = instance
        self.description = description
        self.priority    = priority          # 1 = highest
        self.status      = ToolStatus.IDLE
        self.last_used   = None
        self.call_count  = 0
        self.error_count = 0
        self._lock       = threading.RLock()

    def mark_used(self):
        with self._lock:
            self.status    = ToolStatus.BUSY
            self.last_used = time.time()
            self.call_count += 1

    def mark_done(self, success: bool = True):
        with self._lock:
            self.status = ToolStatus.IDLE if success else ToolStatus.ERROR
            if not success:
                self.error_count += 1

    def to_dict(self) -> Dict:
        return {
            "name":        self.name,
            "type":        self.tool_type,
            "status":      self.status,
            "priority":    self.priority,
            "call_count":  self.call_count,
            "error_count": self.error_count,
            "last_used":   self.last_used,
            "description": self.description,
        }


class ToolRegistry:
    """
    مسجّل الأدوات — يدار بواسطة AgentCore
    يمنع التعارض ويختار الأداة المناسبة
    """

    def __init__(self):
        self._tools: Dict[str, RegisteredTool] = {}
        self._lock  = threading.RLock()
        logger.info("ToolRegistry initialized")

    def register(self, name: str, tool_type: str, instance: Any,
                 description: str = "", priority: int = 5) -> RegisteredTool:
        with self._lock:
            tool = RegisteredTool(name, tool_type, instance, description, priority)
            self._tools[name] = tool
            logger.info("Tool registered", context={"name": name, "type": tool_type})
            return tool

    def get(self, name: str) -> Optional[RegisteredTool]:
        return self._tools.get(name)

    def get_by_type(self, tool_type: str) -> List[RegisteredTool]:
        return sorted(
            [t for t in self._tools.values() if t.tool_type == tool_type],
            key=lambda t: t.priority
        )

    def get_available(self, tool_type: str = None) -> List[RegisteredTool]:
        tools = list(self._tools.values())
        if tool_type:
            tools = [t for t in tools if t.tool_type == tool_type]
        return [t for t in tools if t.status != ToolStatus.BUSY]

    def call(self, name: str, method: str, *args, **kwargs) -> Dict:
        tool = self.get(name)
        if not tool:
            return {"success": False, "error": f"Tool '{name}' not registered"}
        if tool.status == ToolStatus.BUSY:
            return {"success": False, "error": f"Tool '{name}' is busy"}

        tool.mark_used()
        try:
            fn = getattr(tool.instance, method, None)
            if not fn:
                raise AttributeError(f"Method '{method}' not found in {name}")
            result = fn(*args, **kwargs)
            tool.mark_done(success=True)
            return {"success": True, "result": result}
        except Exception as e:
            tool.mark_done(success=False)
            logger.error("Tool call failed", error=e, context={"tool": name, "method": method})
            return {"success": False, "error": str(e)}

    def get_all_status(self) -> List[Dict]:
        return [t.to_dict() for t in self._tools.values()]

    def health_check(self) -> Dict:
        total  = len(self._tools)
        idle   = sum(1 for t in self._tools.values() if t.status == ToolStatus.IDLE)
        busy   = sum(1 for t in self._tools.values() if t.status == ToolStatus.BUSY)
        errors = sum(1 for t in self._tools.values() if t.status == ToolStatus.ERROR)
        return {
            "total": total, "idle": idle,
            "busy": busy, "errors": errors,
            "healthy": errors == 0
        }

    def choose_best_tool(self, task: str, preferred_type: str = None) -> Optional[RegisteredTool]:
        """يختار الأداة المناسبة بناءً على المهمة"""
        task_lower = task.lower()
        
        # تحديد النوع تلقائياً إذا لم يُحدد
        if not preferred_type:
            if any(k in task_lower for k in ["search", "find", "look", "ابحث"]):
                preferred_type = ToolType.KNOWLEDGE
            elif any(k in task_lower for k in ["click", "navigate", "browse", "افتح"]):
                preferred_type = ToolType.BROWSER
            elif any(k in task_lower for k in ["remember", "save", "store", "احفظ"]):
                preferred_type = ToolType.MEMORY
            elif any(k in task_lower for k in ["wordpress", "plugin", "wp", "موقع"]):
                preferred_type = ToolType.WP
            else:
                preferred_type = ToolType.EXECUTION

        available = self.get_available(preferred_type)
        return available[0] if available else None


# Singleton
tool_registry = ToolRegistry()
