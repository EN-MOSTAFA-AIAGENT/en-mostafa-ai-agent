import sqlite3
import json
import time
from typing import Dict, List
from logger_system import get_logger

logger = get_logger("memory")
DB_PATH = r"C:\\mcp-agent\\agent_state.db"


class MemoryEngine:
    def __init__(self):
        self._init_db()

    def _connect(self):
        return sqlite3.connect(DB_PATH, check_same_thread=False)

    def _init_db(self):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT,
            success INTEGER,
            duration REAL,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        conn.close()

    def save_execution(self, command: str, success: bool, duration: float, error: str = None):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO executions (command, success, duration, error) VALUES (?, ?, ?, ?)",
            (command, int(success), duration, error)
        )

        conn.commit()
        conn.close()

    def find_similar(self, command: str) -> List[Dict]:
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("SELECT command, success, duration FROM executions WHERE command LIKE ? ORDER BY created_at DESC LIMIT 10", (f"%{command.split()[0]}%",))
        rows = cur.fetchall()
        conn.close()

        return [{"command": r[0], "success": r[1], "duration": r[2]} for r in rows]

    def get_best_strategy(self, command: str):
        data = self.find_similar(command)
        success = [d for d in data if d["success"] == 1]
        if success:
            return min(success, key=lambda x: x["duration"])
        return None

    def update_stats(self, command: str):
        # placeholder for future stats aggregation
        logger.info("Stats updated", context={"command": command})
