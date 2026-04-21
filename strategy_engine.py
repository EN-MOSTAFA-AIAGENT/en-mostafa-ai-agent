import sqlite3

DB_PATH = r"C:\\mcp-agent\\agent_state.db"


class StrategyEngine:
    def __init__(self):
        self._init_db()

    def _connect(self):
        return sqlite3.connect(DB_PATH, check_same_thread=False)

    def _init_db(self):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            command TEXT,
            success_rate FLOAT,
            avg_duration FLOAT
        )
        """)

        conn.commit()
        conn.close()

    def get_best_strategy(self, task_type: str):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT command FROM strategies ORDER BY success_rate DESC LIMIT 3")
        rows = cur.fetchall()
        conn.close()
        return [r[0] for r in rows]

    def update_strategy(self, command, success, duration):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("SELECT success_rate, avg_duration FROM strategies WHERE command=?", (command,))
        row = cur.fetchone()

        if row:
            sr, ad = row
            sr = (sr + int(success)) / 2
            ad = (ad + duration) / 2
            cur.execute("UPDATE strategies SET success_rate=?, avg_duration=? WHERE command=?", (sr, ad, command))
        else:
            cur.execute("INSERT INTO strategies VALUES (?, ?, ?)", (command, float(success), duration))

        conn.commit()
        conn.close()

    def generate_new_strategy(self, command, error):
        if "pip" in command:
            return "py -3.11 -m pip install"
        return command
