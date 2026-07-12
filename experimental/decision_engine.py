class DecisionEngine:
    def decide_next_task(self, goal_manager):
        return goal_manager.get_next_task()

    def detect_failures(self, result):
        if not result:
            return True

        if isinstance(result, dict):
            return result.get("status") != "completed"

        return False

    def trigger_recovery(self, task, goal_manager):
        # simple retry strategy
        return task

    def process_result(self, task, result, goal_manager):
        failed = self.detect_failures(result)

        if failed:
            new_task = self.trigger_recovery(task, goal_manager)
            if new_task:
                goal_manager.create_goal("recovery", [{"task": new_task, "status": "pending"}])
