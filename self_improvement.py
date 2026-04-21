from memory_engine import MemoryEngine


class SelfImprovementEngine:
    def __init__(self):
        self.memory = MemoryEngine()

    def analyze_performance(self):
        data = self.memory.find_similar("")

        slow = []
        failed = []

        for d in data:
            if d.get("duration", 0) > 5:
                slow.append(d)
            if d.get("success") == 0:
                failed.append(d)

        return {
            "slow": slow,
            "failed": failed
        }

    def generate_improvement_tasks(self):
        analysis = self.analyze_performance()
        tasks = []

        if analysis["slow"]:
            tasks.append("optimize execution speed")

        if analysis["failed"]:
            tasks.append("fix recurring errors")

        if not tasks:
            tasks.append("improve overall performance")

        return tasks

    def inject_tasks(self, goal_manager):
        tasks = self.generate_improvement_tasks()

        for t in tasks:
            goal_manager.create_goal(t)
