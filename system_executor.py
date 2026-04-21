import subprocess
import shutil
from typing import Dict, List
from logger_system import get_logger
from dependency_manager import DependencyManager

logger = get_logger("system_executor")


class SystemExecutor:
    """
    محرك تنفيذ ذكي (System-Aware + Self-Healing)
    """

    def __init__(self):
        """
        تهيئة النظام
        """
        self.history: List[str] = []
        self.dependency_manager = DependencyManager(auto_mode=True)

    def detect_environment(self) -> Dict[str, bool]:
        """
        اكتشاف الأدوات المتاحة
        """
        return {
            "python": shutil.which("py") is not None or shutil.which("python") is not None,
            "pip": shutil.which("pip") is not None,
            "git": shutil.which("git") is not None,
            "node": shutil.which("node") is not None,
            "npm": shutil.which("npm") is not None,
            "powershell": shutil.which("powershell") is not None,
            "cmd": True,
            "bash": shutil.which("bash") is not None,
        }

    def analyze_command(self, command: str) -> Dict:
        """
        تحليل الأمر
        """
        cmd = command.lower().strip()

        if cmd.startswith("git"):
            return {"category": "git", "preferred_tool": "git", "required_tools": ["git"], "requires_admin": False}

        if "pip" in cmd or cmd.startswith("install"):
            return {"category": "python", "preferred_tool": "pip", "required_tools": ["python", "pip"], "requires_admin": False}

        if "npm" in cmd or "npx" in cmd:
            return {"category": "node", "preferred_tool": "npm", "required_tools": ["node", "npm"], "requires_admin": False}

        return {"category": "system", "preferred_tool": "powershell", "required_tools": ["powershell"], "requires_admin": False}

    def ensure_tool_installed(self, tool_name: str):
        """
        (Deprecated - fallback) استخدام DependencyManager بدلاً منها
        """
        self.dependency_manager.ensure(tool_name, dep_type="system")

    def select_tool(self, analysis: Dict) -> str:
        """
        اختيار الأداة
        """
        return analysis.get("preferred_tool", "powershell")

    def _run(self, command: str, timeout: int = 30):
        """
        تنفيذ الأمر
        """
        return subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)

    def execute(self, command: str) -> Dict:
        """
        تنفيذ ذكي + Self Healing
        """
        self.history.append(command)
        self.history = self.history[-20:]

        analysis = self.analyze_command(command)

        logger.info("Execute", context={"command": command, **analysis})

        # Ensure dependencies (SMART)
        for tool in analysis.get("required_tools", []):
            dep_type = "system"

            if tool in ["python", "pip"]:
                dep_type = "python"
            elif tool in ["node", "npm"]:
                dep_type = "system"

            self.dependency_manager.ensure(tool, dep_type=dep_type)
            logger.info("Dependency ensured", context={"tool": tool, "type": dep_type})

        tool = self.select_tool(analysis)
        final_command = command

        if tool == "pip":
            cleaned = command.replace("pip", "").strip()
            final_command = f"py -3.11 -m pip {cleaned}"

        retries = 2

        for attempt in range(retries + 1):
            try:
                result = self._run(final_command, timeout=30 + attempt * 20)

                if result.returncode == 0:
                    logger.info("Success", context={"tool": tool})
                    return {"success": True, "stdout": result.stdout, "stderr": result.stderr}

                stderr = (result.stderr or "").lower()

                # Auto-healing
                if "not recognized" in stderr or "not found" in stderr:
                    logger.warning("Command not found → installing dependencies")

                    for t in analysis.get("required_tools", []):
                        self.dependency_manager.ensure(t)

                    logger.info("Retrying after install")
                    continue

                elif "access denied" in stderr:
                    logger.warning("Access denied → retry")

                elif "timeout" in stderr:
                    logger.warning("Timeout → retry")

                # Fallback
                if tool == "powershell":
                    final_command = f"cmd /c {command}"
                elif tool == "cmd":
                    final_command = f"powershell -Command \"{command}\""

            except subprocess.TimeoutExpired:
                logger.warning("Timeout exception")

        logger.error("Failed after retries")
        return {"success": False, "error": "failed"}


# Example
# executor = SystemExecutor()
# executor.execute("git clone repo")
# executor.execute("pip install flask")
# executor.execute("npm install")
