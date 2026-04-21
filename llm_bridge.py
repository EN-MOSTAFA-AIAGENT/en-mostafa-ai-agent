"""
LLM Bridge — ربط Agent بأي LLM (Claude / GPT / Local)
يحافظ على الاتصال الحالي للـ MCP ويضيف:
  - Context جاهز من AgentCore
  - Workflow: Context → LLM → Plan → Execute
  - دعم: Claude API, OpenAI API, Ollama (local)
"""

import os
import json
import time
import threading
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any
from logger_system import get_logger

logger = get_logger("llm_bridge")


class LLMProvider:
    CLAUDE  = "claude"
    OPENAI  = "openai"
    OLLAMA  = "ollama"   # local
    MOCK    = "mock"     # للاختبار بدون API


class LLMBridge:
    """
    الجسر الذكي بين AgentCore وأي LLM
    Workflow: Agent يجهز Context → LLM → يستقبل الحل → ينفذ محلياً
    """

    def __init__(self):
        self._lock    = threading.RLock()
        self.provider = os.environ.get("LLM_PROVIDER", LLMProvider.MOCK)
        self.api_key  = os.environ.get("LLM_API_KEY", "")
        self.model    = os.environ.get("LLM_MODEL", "claude-sonnet-4-5")
        self.base_url = os.environ.get("LLM_BASE_URL", "")
        self.timeout  = int(os.environ.get("LLM_TIMEOUT", "30"))

        # History per session
        self._history: List[Dict] = []
        self._max_history = 20

        logger.info("LLMBridge initialized", context={"provider": self.provider, "model": self.model})

    # ─────────────────────────────────────────
    #  MAIN INTERFACE
    # ─────────────────────────────────────────

    def think(self, task: str, context: Dict = None, knowledge: str = "") -> Dict:
        """
        Workflow الرئيسي:
        1. يجهز context كامل
        2. يرسل للـ LLM
        3. يستقبل الخطة
        4. يرجع قابل للتنفيذ
        """
        prompt = self._build_prompt(task, context or {}, knowledge)
        response = self._call_llm(prompt)

        result = {
            "task":       task,
            "provider":   self.provider,
            "model":      self.model,
            "raw":        response,
            "plan":       self._extract_plan(response),
            "explanation":self._extract_explanation(response),
            "timestamp":  time.time(),
        }

        # حفظ في history
        with self._lock:
            self._history.append({"role": "assistant", "content": response, "task": task})
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

        return result

    def analyze_error(self, error: str, context: Dict = None) -> Dict:
        """تحليل خطأ بالذكاء الاصطناعي"""
        prompt = f"""أنت مهندس WordPress خبير. حلل هذا الخطأ:

ERROR: {error}

السياق: {json.dumps(context or {}, ensure_ascii=False, indent=2)}

المطلوب:
1. سبب الخطأ
2. الحل المباشر
3. كيف تمنع تكراره

أجب بالعربية بشكل مختصر واحترافي."""
        response = self._call_llm(prompt)
        return {"analysis": response, "error": error, "provider": self.provider}

    def plan_wordpress_task(self, task: str, site_info: Dict = None) -> Dict:
        """تخطيط مهمة WordPress"""
        prompt = f"""أنت مهندس WordPress خبير تعمل مع AI Agent.

المهمة: {task}

معلومات الموقع:
{json.dumps(site_info or {}, ensure_ascii=False, indent=2)}

ضع خطة تنفيذ واضحة بالخطوات:
- كل خطوة تبدأ بـ STEP:
- اذكر الـ WordPress REST endpoint إذا لزم
- اذكر WP-CLI command إذا لزم
- أجب بالعربية"""
        response = self._call_llm(prompt)
        return {
            "plan_text": response,
            "steps":     self._extract_steps(response),
            "task":      task,
        }

    def explain_plan(self, plan: List[Dict], task: str) -> str:
        """شرح خطة التنفيذ بالعربية"""
        steps_text = "\n".join([f"{i+1}. {s.get('step','')}: {s.get('command','')}" for i,s in enumerate(plan)])
        prompt = f"""اشرح هذه الخطة للمستخدم بالعربية بشكل واضح ومختصر:

المهمة: {task}

الخطوات:
{steps_text}

اشرح ما ستفعله وما النتيجة المتوقعة في 3-4 جمل."""
        return self._call_llm(prompt)

    def learn_from_doc(self, content: str, source: str = "") -> Dict:
        """فهم محتوى وثيقة وتحليلها"""
        # نأخذ أول 3000 حرف فقط لتجنب تجاوز الـ context
        excerpt = content[:3000]
        prompt = f"""أنت خبير تقني. حلل هذا المحتوى من المصدر: {source}

{excerpt}

المطلوب:
1. ملخص في 3 جمل
2. أهم 5 نقاط تقنية
3. كيف يفيد نظام إدارة WordPress

أجب بالعربية."""
        summary = self._call_llm(prompt)
        return {"summary": summary, "source": source, "chars_analyzed": len(excerpt)}

    # ─────────────────────────────────────────
    #  PROVIDERS
    # ─────────────────────────────────────────

    def _call_llm(self, prompt: str) -> str:
        if self.provider == LLMProvider.CLAUDE:
            return self._call_claude(prompt)
        elif self.provider == LLMProvider.OPENAI:
            return self._call_openai(prompt)
        elif self.provider == LLMProvider.OLLAMA:
            return self._call_ollama(prompt)
        else:
            return self._mock_response(prompt)

    def _call_claude(self, prompt: str) -> str:
        """Claude API (Anthropic)"""
        if not self.api_key:
            return "[Claude API key not set. Set LLM_API_KEY env var]"
        url  = "https://api.anthropic.com/v1/messages"
        body = {
            "model":      self.model or "claude-sonnet-4-5",
            "max_tokens": 1500,
            "messages":   [{"role": "user", "content": prompt}]
        }
        headers = {
            "Content-Type":      "application/json",
            "x-api-key":         self.api_key,
            "anthropic-version": "2023-06-01",
        }
        return self._http_post(url, body, headers)

    def _call_openai(self, prompt: str) -> str:
        """OpenAI API (GPT)"""
        if not self.api_key:
            return "[OpenAI API key not set. Set LLM_API_KEY env var]"
        url  = self.base_url or "https://api.openai.com/v1/chat/completions"
        body = {
            "model":    self.model or "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        return self._http_post(url, body, headers)

    def _call_ollama(self, prompt: str) -> str:
        """Ollama — local LLM (مجاني بدون API key)"""
        url  = self.base_url or "http://localhost:11434/api/generate"
        body = {
            "model":  self.model or "llama3",
            "prompt": prompt,
            "stream": False,
        }
        return self._http_post(url, body, {})

    def _http_post(self, url: str, body: Dict, headers: Dict) -> str:
        try:
            data = json.dumps(body).encode()
            req  = urllib.request.Request(url, data=data, headers={
                "Content-Type": "application/json", **headers
            }, method="POST")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode())

            # استخراج النص من كل provider
            if "content" in result:                        # Claude
                return result["content"][0]["text"]
            elif "choices" in result:                      # OpenAI
                return result["choices"][0]["message"]["content"]
            elif "response" in result:                     # Ollama
                return result["response"]
            return str(result)

        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="ignore")
            logger.error("LLM HTTP error", error=e, context={"url": url, "body": err[:200]})
            return f"[LLM Error {e.code}: {err[:200]}]"
        except Exception as e:
            logger.error("LLM call failed", error=e)
            return f"[LLM unavailable: {str(e)}]"

    def _mock_response(self, prompt: str) -> str:
        """Mock — للاختبار بدون API"""
        if "خطأ" in prompt or "error" in prompt.lower():
            return "تحليل الخطأ: يبدو أن المشكلة في إعدادات الـ Plugin. الحل: تعطيل الـ Plugin المسبب وإعادة تفعيله."
        if "wordpress" in prompt.lower() or "wp" in prompt.lower():
            return "خطة التنفيذ:\nSTEP: التحقق من الاتصال → ping endpoint\nSTEP: جلب معلومات الموقع → /site-info\nSTEP: تنفيذ المهمة المطلوبة"
        return f"[Mock LLM] تم استقبال المهمة. لتفعيل LLM حقيقي: set LLM_PROVIDER=claude و LLM_API_KEY=your_key\n\nالمهمة: {prompt[:100]}"

    # ─────────────────────────────────────────
    #  HELPERS
    # ─────────────────────────────────────────

    def _build_prompt(self, task: str, context: Dict, knowledge: str) -> str:
        parts = ["أنت AI Agent متخصص في إدارة مواقع WordPress.\n"]
        if context.get("site"):
            parts.append(f"الموقع الحالي: {context['site']}")
        if context.get("mode"):
            parts.append(f"وضع التنفيذ: {context['mode']}")
        if knowledge:
            parts.append(f"\nمعرفة متاحة:\n{knowledge[:500]}")
        parts.append(f"\nالمهمة: {task}")
        parts.append("\nضع خطة واضحة وقابلة للتنفيذ:")
        return "\n".join(parts)

    def _extract_plan(self, response: str) -> List[Dict]:
        """استخراج خطوات من النص"""
        steps = []
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("STEP:") or (line and line[0].isdigit() and "." in line[:3]):
                steps.append({"step": line, "command": ""})
        return steps

    def _extract_explanation(self, response: str) -> str:
        """أول فقرة كشرح"""
        parts = response.split("\n")
        return next((p for p in parts if len(p) > 20), response[:200])

    def _extract_steps(self, response: str) -> List[str]:
        return [l.strip() for l in response.split("\n") if l.strip().startswith("STEP:")]

    # ─────────────────────────────────────────
    #  CONFIG
    # ─────────────────────────────────────────

    def configure(self, provider: str, api_key: str = "", model: str = "", base_url: str = ""):
        with self._lock:
            self.provider = provider
            if api_key:
                self.api_key  = api_key
                os.environ["LLM_API_KEY"] = api_key
            if model:
                self.model    = model
            if base_url:
                self.base_url = base_url
            os.environ["LLM_PROVIDER"] = provider
            logger.info("LLM configured", context={"provider": provider, "model": model})

    def get_config(self) -> Dict:
        return {
            "provider": self.provider,
            "model":    self.model,
            "has_key":  bool(self.api_key),
            "base_url": self.base_url,
        }

    def get_history(self) -> List[Dict]:
        return self._history[-10:]


# Singleton
llm_bridge = LLMBridge()
