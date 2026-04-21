"""
Sites Store — تخزين مستمر لمواقع WordPress
يحفظ في SQLite حتى لا يُفقد البيانات عند إعادة التشغيل
"""

import json
import sqlite3
import threading
from typing import Dict, List, Optional
from logger_system import get_logger

logger  = get_logger("sites_store")
DB_PATH = r"C:\mcp-agent\agent_state.db"


class SitesStore:

    def __init__(self):
        self._lock = threading.RLock()
        self._init_db()

    def _connect(self):
        return sqlite3.connect(DB_PATH, check_same_thread=False)

    def _init_db(self):
        conn = self._connect()
        conn.execute("""
        CREATE TABLE IF NOT EXISTS registered_sites (
            name       TEXT PRIMARY KEY,
            url        TEXT NOT NULL,
            api_key    TEXT NOT NULL,
            meta       TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.commit()
        conn.close()
        logger.info("SitesStore ready")

    def save(self, name: str, url: str, api_key: str, meta: Dict = None) -> bool:
        try:
            with self._lock:
                conn = self._connect()
                conn.execute("""
                INSERT INTO registered_sites (name, url, api_key, meta, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(name) DO UPDATE SET
                    url        = excluded.url,
                    api_key    = excluded.api_key,
                    meta       = excluded.meta,
                    updated_at = CURRENT_TIMESTAMP
                """, (name, url, api_key, json.dumps(meta or {})))
                conn.commit()
                conn.close()
            logger.info("Site saved", context={"name": name})
            return True
        except Exception as e:
            logger.error("Site save failed", error=e)
            return False

    def load_all(self) -> List[Dict]:
        conn = self._connect()
        rows = conn.execute(
            "SELECT name, url, api_key, meta FROM registered_sites ORDER BY created_at"
        ).fetchall()
        conn.close()
        return [
            {"name": r[0], "url": r[1],
             "api_key": r[2], "meta": json.loads(r[3] or "{}")}
            for r in rows
        ]

    def get(self, name: str) -> Optional[Dict]:
        conn = self._connect()
        row  = conn.execute(
            "SELECT name, url, api_key, meta FROM registered_sites WHERE name=?",
            (name,)
        ).fetchone()
        conn.close()
        if not row:
            return None
        return {"name": row[0], "url": row[1],
                "api_key": row[2], "meta": json.loads(row[3] or "{}")}

    def delete(self, name: str) -> bool:
        try:
            conn = self._connect()
            conn.execute("DELETE FROM registered_sites WHERE name=?", (name,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error("Site delete failed", error=e)
            return False

    def count(self) -> int:
        conn = self._connect()
        n    = conn.execute("SELECT COUNT(*) FROM registered_sites").fetchone()[0]
        conn.close()
        return n


def restore_sites_to_manager(wp_manager) -> int:
    """
    يُستدعى عند بدء السيرفر لاستعادة المواقع المحفوظة
    """
    store    = SitesStore()
    sites    = store.load_all()
    restored = 0
    for s in sites:
        try:
            wp_manager.add_site(s["name"], s["url"], s["api_key"])
            restored += 1
        except Exception as e:
            logger.error("Restore site failed", error=e,
                         context={"name": s["name"]})
    if restored:
        logger.info(f"Restored {restored} sites from DB")
    return restored


# Singleton
sites_store = SitesStore()
