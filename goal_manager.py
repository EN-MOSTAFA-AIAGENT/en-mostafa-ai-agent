import sqlite3
import json
import uuid
from agent_brain import AgentBrain

DB_PATH = r"C:\\mcp-agent\\agent_state.db"


class GoalManager:
    def __init__(self):
        self.brain = AgentBrain()
        self._init_db()

    def _connect(self):
        return sqlite3.connect(DB_PATH, check_same_thread=False)

    def _init_db(self):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            goal_id TEXT PRIMARY KEY,
            description TEXT,
            sub_tasks TEXT,
            status TEXT,
            progress INTEGER
        )
        """)

        conn.commit()
        conn.close()

    def create_goal(self, description: str):
        analysis = self.brain.analyze(description)
        plan = self.brain.generate_plan(analysis)

        tasks = [{"task": s.get("command"), "status": "pending"} for s in plan]

        goal_id = str(uuid.uuid4())

        conn = self._connect()
        cur = conn.cursor()

        cur.execute("INSERT INTO goals VALUES (?, ?, ?, ?, ?)",
                    (goal_id, description, json.dumps(tasks), "active", 0))

        conn.commit()
        conn.close()

        return goal_id

    def get_next_task(self):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("SELECT goal_id, sub_tasks FROM goals WHERE status='active'")
        rows = cur.fetchall()

        for goal_id, tasks_json in rows:
            tasks = json.loads(tasks_json)
            for t in tasks:
                if t["status"] == "pending":
                    return t["task"]

        return None

    def mark_task_done(self, task: str):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("SELECT goal_id, sub_tasks FROM goals WHERE status='active'")
        rows = cur.fetchall()

        for goal_id, tasks_json in rows:
            tasks = json.loads(tasks_json)

            updated = False
            for t in tasks:
                if t["task"] == task and t["status"] == "pending":
                    t["status"] = "completed"
                    updated = True

            if updated:
                cur.execute("UPDATE goals SET sub_tasks=? WHERE goal_id=?",
                            (json.dumps(tasks), goal_id))

        conn.commit()
        conn.close()

    def update_progress(self):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("SELECT goal_id, sub_tasks FROM goals WHERE status='active'")
        rows = cur.fetchall()

        for goal_id, tasks_json in rows:
            tasks = json.loads(tasks_json)
            total = len(tasks)
            done = len([t for t in tasks if t["status"] == "completed"])

            progress = int((done / total) * 100) if total else 0
            status = "completed" if progress == 100 else "active"

            cur.execute("UPDATE goals SET progress=?, status=? WHERE goal_id=?",
                        (progress, status, goal_id))

        conn.commit()
        conn.close()
