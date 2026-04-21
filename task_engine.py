import sqlite3
import json
import time
import uuid
from typing import List, Dict
from logger_system import get_logger
from system_executor import SystemExecutor

logger = get_logger("task_engine")

DB_PATH = r"C:\\mcp-agent\\agent_state.db"


class TaskEngine:
    def __init__(self):
        self.executor = SystemExecutor()
        self._init_db()

    def _connect(self):
        return sqlite3.connect(DB_PATH, check_same_thread=False)

    def _init_db(self):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            mode TEXT DEFAULT 'auto',
            status TEXT DEFAULT 'pending',
            context TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS steps (
            id TEXT PRIMARY KEY,
            task_id TEXT,
            order_num INTEGER,
            description TEXT,
            tool TEXT,
            params TEXT,
            status TEXT DEFAULT 'pending',
            result TEXT,
            error TEXT,
            attempts INTEGER DEFAULT 0,
            timeout_sec INTEGER DEFAULT 30,
            executed_at TIMESTAMP,
            context_in TEXT,
            context_out TEXT
        )
        """)

        conn.commit()
        conn.close()

    def create_task(self, description: str, steps: List[Dict], mode: str = "auto") -> str:
        task_id = str(uuid.uuid4())
        conn = self._connect()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO tasks (id, description, mode, status) VALUES (?, ?, ?, ?)",
            (task_id, description, mode, "pending")
        )

        for i, step in enumerate(steps):
            step_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO steps (id, task_id, order_num, description, tool, params, context_in) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    step_id,
                    task_id,
                    i,
                    step.get("description"),
                    step.get("tool"),
                    json.dumps(step.get("params", {})),
                    json.dumps({})
                )
            )

        conn.commit()
        conn.close()

        logger.info("Task created", context={"task_id": task_id})
        return task_id

    def execute_task(self, task_id: str):
        conn = self._connect()
        cur = conn.cursor()

        logger.info("Start task", context={"task_id": task_id})

        cur.execute("UPDATE tasks SET status='running' WHERE id=?", (task_id,))
        conn.commit()

        cur.execute("SELECT * FROM steps WHERE task_id=? ORDER BY order_num ASC", (task_id,))
        steps = cur.fetchall()

        context = {}

        for step in steps:
            step_id = step[0]
            description = step[3]
            params = json.loads(step[5] or "{}")

            cur.execute("UPDATE steps SET context_in=? WHERE id=?", (json.dumps(context), step_id))
            conn.commit()

            logger.info("Executing step", context={"step_id": step_id, "desc": description})

            success = False

            for attempt in range(3):
                try:
                    cur.execute("UPDATE steps SET attempts=? WHERE id=?", (attempt + 1, step_id))
                    conn.commit()

                    command = params.get("command")

                    result = self.executor.execute(command)

                    if result.get("success"):
                        success = True

                        context_out = {"last_result": result.get("stdout")}

                        cur.execute("""
                            UPDATE steps SET status='done', result=?, context_out=?, executed_at=CURRENT_TIMESTAMP
                            WHERE id=?
                        """, (result.get("stdout"), json.dumps(context_out), step_id))

                        conn.commit()

                        context.update(context_out)
                        break

                    else:
                        raise Exception(result.get("error"))

                except Exception as e:
                    logger.warning("Step failed", context={"step_id": step_id, "error": str(e), "attempt": attempt + 1})
                    time.sleep(2)

            if not success:
                cur.execute("UPDATE steps SET status='failed', error=? WHERE id=?", ("failed after retries", step_id))
                cur.execute("UPDATE tasks SET status='failed' WHERE id=?", (task_id,))
                conn.commit()
                conn.close()
                return

        cur.execute("UPDATE tasks SET status='completed', completed_at=CURRENT_TIMESTAMP WHERE id=?", (task_id,))
        conn.commit()
        conn.close()

        logger.info("Task completed", context={"task_id": task_id})

    def resume_task(self, task_id: str):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("SELECT * FROM steps WHERE task_id=? AND status!='done' ORDER BY order_num ASC", (task_id,))
        steps = cur.fetchall()
        conn.close()

        if not steps:
            return

        self.execute_task(task_id)

    def get_task_status(self, task_id: str) -> Dict:
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("SELECT status FROM tasks WHERE id=?", (task_id,))
        task = cur.fetchone()

        cur.execute("SELECT status FROM steps WHERE task_id=?", (task_id,))
        steps = cur.fetchall()

        total = len(steps)
        done = len([s for s in steps if s[0] == "done"])

        progress = int((done / total) * 100) if total > 0 else 0

        conn.close()

        return {
            "task_id": task_id,
            "status": task[0] if task else "unknown",
            "progress_percent": progress,
            "steps": [s[0] for s in steps]
        }

    def cancel_task(self, task_id: str):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("UPDATE tasks SET status='cancelled' WHERE id=?", (task_id,))
        conn.commit()
        conn.close()

        logger.warning("Task cancelled", context={"task_id": task_id})

    def list_incomplete_tasks(self):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("SELECT id, status FROM tasks WHERE status!='completed'")
        rows = cur.fetchall()
        conn.close()

        return rows
