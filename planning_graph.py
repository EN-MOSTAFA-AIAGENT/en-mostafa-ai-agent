class PlanningGraph:
    def __init__(self):
        self.graph = {}

    def build_graph(self, plan):
        self.graph = {}
        for i, step in enumerate(plan):
            self.graph[i] = {"step": step, "depends_on": [i-1] if i > 0 else []}
        return self.graph

    def resolve_dependencies(self):
        ordered = []
        for i in sorted(self.graph.keys()):
            ordered.append(self.graph[i]["step"])
        return ordered

    def optimize_execution_order(self):
        return self.resolve_dependencies()
