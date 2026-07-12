import json


class StateManager:
    def __init__(self):
        self.reset()

    def reset(self):
        self.state = {
            "task": None,
            "steps": [],
            "final_result": None
        }

    def set_task(self, task: str):
        self.state["task"] = task

    def add_step(self, step: dict):
        self.state["steps"].append(step)

    def set_result(self, result: dict):
        self.state["final_result"] = result

    def get_state(self):
        return self.state
