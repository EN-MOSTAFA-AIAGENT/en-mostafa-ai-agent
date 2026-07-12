import time

from agent_brain import AgentBrain
from system_executor import SystemExecutor
from memory_engine import MemoryEngine
from pattern_engine import PatternEngine
from strategy_engine import StrategyEngine
from dependency_manager import DependencyManager
from state_manager import StateManager
from event_logger import EventLogger
from self_monitor import SelfMonitor
from dynamic_rules import DynamicRules


class AgentCore:
    def __init__(self):
        self.brain = AgentBrain()
        self.executor = SystemExecutor()
        self.memory = MemoryEngine()
        self.pattern = PatternEngine()
        self.strategy = StrategyEngine()
        self.dependency = DependencyManager(auto_mode=True)
        self.state = StateManager()
        self.logger = EventLogger()
        self.monitor = SelfMonitor()
        self.rules = DynamicRules()

    def handle_task(self, user_input: str):
        self.state.reset()

        self.logger.log_event("TASK_START", user_input)
        self.state.set_task(user_input)

        # cognitive reflection
        self.brain.reflect_before_planning(user_input)

        analysis = self.brain.analyze(user_input)
        plan = self.brain.generate_plan(analysis)
        plan = self.brain.optimize_plan(plan)

        results = []

        for step in plan:
            command = step.get("command")

            # apply dynamic rules
            command = self.rules.apply_rules(command)

            start = time.time()

            result = self.executor.execute(command)
            duration = time.time() - start

            if result.get("success"):
                self.memory.save_execution(command, True, duration)
                self.strategy.update_strategy(command, True, duration)
            else:
                error = result.get("error")
                err_type = self.pattern.classify_error(error)
                solution = self.pattern.map_to_solution_type(err_type)
                new_cmd = self.strategy.generate_new_strategy(command, error)
                self.rules.learn_rule(command, new_cmd)

                self.memory.save_execution(command, False, duration, error)
                self.strategy.update_strategy(command, False, duration)

            results.append(result)

        self.monitor.evaluate_task(self.state.get_state())
        self.monitor.suggest_improvements()
        self.monitor.log_reflection()

        final = {"results": results, "status": "completed"}
        self.state.set_result(final)

        self.logger.log_event("TASK_COMPLETE", user_input)

        return self.state.get_state()
