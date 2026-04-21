import re
from planning_graph import PlanningGraph


class AgentBrain:
    def __init__(self):
        self.plan_cache = {}
        self.graph = PlanningGraph()

    def reflect_before_planning(self, task: str):
        # simple reflection hook
        return {"length": len(task), "keywords": task.split()[:3]}

    def analyze(self, task: str):
        t = task.lower()
        intent = "general"
        if "install" in t:
            intent = "install"
        elif "clone" in t:
            intent = "clone"
        elif "run" in t:
            intent = "run"
        elif "setup" in t:
            intent = "setup_project"

        words = re.findall(r"\w+", t)
        entities = [w for w in words if w not in ["install","clone","run","setup","project"]]

        return {"intent": intent, "entities": entities, "task_type": "system"}

    def generate_plan(self, analysis):
        plan = []
        entities = analysis.get("entities", [])

        if analysis["intent"] == "clone":
            repo = entities[0] if entities else ""
            plan.append({"step": "clone repo", "command": f"git clone {repo}"})

        if analysis["intent"] in ["install", "setup_project"]:
            if entities:
                pkg = entities[0]
                plan.append({"step": "install", "command": f"pip install {pkg}"})

        if analysis["intent"] == "run":
            plan.append({"step": "run", "command": "python app.py"})

        if not plan:
            plan.append({"step": "execute", "command": entities[0] if entities else "echo done"})

        return plan

    def optimize_plan(self, plan):
        self.graph.build_graph(plan)
        return self.graph.optimize_execution_order()
