"""Short-Term Memory Module"""
import json
import time
from collections import OrderedDict
from typing import Any, Dict, Optional
import threading

class AgentMemory:
    def __init__(self, max_items: int = 100, default_ttl: int = 3600):
        self.max_items = max_items
        self.default_ttl = default_ttl
        self._memory: OrderedDict[str, Dict] = OrderedDict()
        self._lock = threading.RLock()
        self._session_context: Dict[str, Any] = {}
        self._interaction_history: list = []
        self._max_history = 50

    def store(self, key: str, value: Any, ttl: int = None) -> None:
        with self._lock:
            if len(self._memory) >= self.max_items:
                self._memory.popitem(last=False)
            self._memory[key] = {
                "value": value,
                "expires_at": time.time() + (ttl or self.default_ttl)
            }

    def retrieve(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._memory:
                return None
            entry = self._memory[key]
            if time.time() > entry["expires_at"]:
                del self._memory[key]
                return None
            return entry["value"]

    def set_session_context(self, context: Dict[str, Any]) -> None:
        with self._lock:
            self._session_context.update(context)

    def get_context_summary(self) -> str:
        recent = self._interaction_history[-5:]
        session = self._session_context
        parts = []
        if session:
            parts.append(f"Context: {json.dumps(session, ensure_ascii=False)}")
        if recent:
            parts.append("Recent: " + ", ".join([i.get('action','?') for i in recent]))
        return "\n".join(parts) if parts else "No context."

    def add_interaction(self, interaction: Dict[str, Any]) -> None:
        with self._lock:
            self._interaction_history.append({**interaction, "timestamp": time.time()})
            if len(self._interaction_history) > self._max_history:
                self._interaction_history = self._interaction_history[-self._max_history:]

    def clear_all(self) -> None:
        with self._lock:
            self._memory.clear()
            self._session_context.clear()
            self._interaction_history.clear()

agent_memory = AgentMemory()
