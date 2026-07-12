from typing import Dict

PATTERNS = {
    "not recognized": {"type": "missing_dependency"},
    "access denied": {"type": "permission"}
}


class PatternEngine:
    def match_pattern(self, command: str, error: str = "") -> Dict:
        text = f"{command} {error}".lower()
        for key, value in PATTERNS.items():
            if key in text:
                return {"pattern": key, **value}
        return {}

    def classify_error(self, error: str):
        error = (error or "").lower()
        if "not recognized" in error:
            return "missing_dependency"
        if "access denied" in error:
            return "permission"
        return "unknown"

    def map_to_solution_type(self, error_type: str):
        mapping = {
            "missing_dependency": "install_tool",
            "permission": "run_as_admin"
        }
        return mapping.get(error_type, "generic_fix")

    def learn_pattern(self, command: str, result: Dict):
        pass
