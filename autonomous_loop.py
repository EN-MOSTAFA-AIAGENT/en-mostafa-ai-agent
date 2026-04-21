import time
from agent_core import AgentCore
from goal_manager import GoalManager
from self_improvement import SelfImprovementEngine
from self_monitor import SelfMonitor


class AutonomousLoop:
    def __init__(self):
        self.agent = AgentCore()
        self.goal_manager = GoalManager()
        self.improver = SelfImprovementEngine()
        self.monitor = SelfMonitor()

        self.max_iterations = 1000

    def run(self):
        iteration = 0

        while iteration < self.max_iterations:
            task = self.goal_manager.get_next_task()

            if not task:
                improvement_tasks = self.improver.generate_improvement_tasks()
                for t in improvement_tasks:
                    self.goal_manager.create_goal(t)

                time.sleep(2)
                iteration += 1
                continue

            result = self.agent.handle_task(task)

            # FIX: mark task completed
            if result and result.get("status") == "completed":
                self.goal_manager.mark_task_done(task)

            self.goal_manager.update_progress()

            self.monitor.evaluate_task(result)
            self.monitor.suggest_improvements()
            self.monitor.log_reflection()

            time.sleep(1)
            iteration += 1
