import subprocess
import shutil
from typing import Dict
from logger_system import get_logger

logger = get_logger("dependency")


class DependencyManager:
    """
    مدير الاعتمادات (Dependency Manager) للتحقق والتثبيت الذكي
    """

    def __init__(self, auto_mode: bool = True):
        """
        تهيئة المدير
        """
        self.auto_mode = auto_mode

    def _run(self, command: str, timeout: int = 30):
        """
        تنفيذ أمر system
        """
        return subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)

    def check(self, name: str, dep_type: str = "python") -> Dict:
        """
        التحقق من وجود dependency
        """
        try:
            if dep_type == "python":
                result = self._run(f"py -3.11 -m pip show {name}")

                if result.returncode == 0:
                    version = ""
                    for line in result.stdout.splitlines():
                        if line.lower().startswith("version:"):
                            version = line.split(":", 1)[1].strip()
                            break

                    logger.info("Dependency exists", context={"name": name, "type": dep_type})
                    return {"exists": True, "version": version, "type": "python"}

                return {"exists": False, "version": None, "type": "python"}

            else:
                result = self._run(f"where {name}")

                if result.returncode == 0:
                    logger.info("System tool exists", context={"name": name})
                    return {"exists": True, "version": None, "type": "system"}

                return {"exists": False, "version": None, "type": "system"}

        except Exception as e:
            logger.error("Check failed", error=e, context={"name": name})
            return {"exists": False, "version": None, "type": dep_type}

    def install(self, name: str, dep_type: str = "python") -> Dict:
        """
        تثبيت dependency
        """
        logger.info("Installing dependency", context={"name": name, "type": dep_type})

        try:
            if dep_type == "python":
                cmd = f"py -3.11 -m pip install {name}"

            elif name.lower() == "git":
                cmd = "winget install Git.Git"

            elif name.lower() == "node":
                cmd = "winget install OpenJS.NodeJS"

            else:
                cmd = f"winget install {name}"

            result = self._run(cmd, timeout=120)

            if result.returncode != 0:
                logger.warning("Winget failed, trying choco", context={"name": name})
                result = self._run(f"choco install {name} -y", timeout=120)

            success = result.returncode == 0

            if success:
                logger.info("Install success", context={"name": name})
            else:
                logger.error("Install failed", context={"name": name, "stderr": result.stderr})

            return {"success": success, "stdout": result.stdout, "stderr": result.stderr}

        except Exception as e:
            logger.error("Install exception", error=e, context={"name": name})
            return {"success": False, "error": str(e)}

    def ensure(self, name: str, dep_type: str = "python"):
        """
        التأكد من وجود dependency أو تثبيته
        """
        status = self.check(name, dep_type)

        if status.get("exists"):
            return True

        logger.warning("Dependency missing", context={"name": name, "mode": "auto" if self.auto_mode else "ask"})

        if self.auto_mode:
            result = self.install(name, dep_type)
            return result.get("success", False)

        else:
            return {
                "action": "approval_required",
                "dependency": name,
                "type": dep_type
            }


# Example usage:
# dm = DependencyManager(auto_mode=True)
# dm.ensure("flask")
# dm.ensure("git", dep_type="system")
