class DynamicRules:
    def __init__(self):
        self.rules = {}

    def learn_rule(self, trigger, action):
        self.rules[trigger] = action

    def apply_rules(self, command):
        for trigger, action in self.rules.items():
            if trigger in command:
                return action
        return command
