"""
Knowledge Manager — AI WordPress Control Center
يدعم: PDF, TXT, URLs, أي Plugin أو Theme
"""

import os
import json
import time
import sqlite3
import hashlib
import threading
import urllib.request
from typing import List, Dict, Optional, Any
from logger_system import get_logger

logger = get_logger("knowledge_manager")

DB_PATH = r"C:\mcp-agent\agent_state.db"


class KnowledgeManager:
    """
    محرك المعرفة — يتعلم من أي مصدر ويبحث قبل كل تنفيذ
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._init_db()
        logger.info("KnowledgeManager ready")

    def _connect(self):
        return sqlite3.connect(DB_PATH, check_same_thread=False)

    def _init_db(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_type TEXT NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            tags TEXT DEFAULT '[]',
            checksum TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP
        )
        """)
        cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts
        USING fts5(id UNINDEXED, title, content, tags, source)
        """)
        conn.commit()
        conn.close()

    # ─────────────────────────────────────────
    #  INGEST
    # ─────────────────────────────────────────

    def learn_from_text(self, text: str, title: str = "", tags: List[str] = None, source: str = "manual") -> Dict:
        checksum = hashlib.md5(text.encode()).hexdigest()
        tags = tags or []
        with self._lock:
            conn = self._connect()
            cur = conn.cursor()
            try:
                cur.execute(
                    "INSERT INTO knowledge_base (source, source_type, title, content, tags, checksum) VALUES (?,?,?,?,?,?)",
                    (source, "text", title, text, json.dumps(tags), checksum)
                )
                row_id = cur.lastrowid
                cur.execute(
                    "INSERT INTO knowledge_fts (id, title, content, tags, source) VALUES (?,?,?,?,?)",
                    (row_id, title, text[:2000], json.dumps(tags), source)
                )
                conn.commit()
                logger.info("Knowledge saved", context={"title": title, "source": source})
                return {"success": True, "id": row_id, "title": title}
            except sqlite3.IntegrityError:
                return {"success": False, "reason": "duplicate", "checksum": checksum}
            finally:
                conn.close()

    def learn_from_file(self, file_path: str, tags: List[str] = None) -> Dict:
        if not os.path.exists(file_path):
            return {"success": False, "reason": "file_not_found", "path": file_path}

        ext = os.path.splitext(file_path)[1].lower()
        title = os.path.basename(file_path)
        tags = tags or []

        try:
            if ext in (".txt", ".md", ".log", ".csv"):
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

            elif ext == ".pdf":
                content = self._extract_pdf(file_path)

            elif ext in (".json",):
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                content = json.dumps(data, ensure_ascii=False, indent=2)

            elif ext in (".php", ".js", ".py", ".html", ".css"):
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                tags.append("code")
                tags.append(ext.lstrip("."))

            else:
                return {"success": False, "reason": "unsupported_format", "ext": ext}

            if not content.strip():
                return {"success": False, "reason": "empty_content"}

            return self.learn_from_text(content, title=title, tags=tags, source=file_path)

        except Exception as e:
            logger.error("learn_from_file failed", error=e)
            return {"success": False, "reason": str(e)}

    def learn_from_url(self, url: str, tags: List[str] = None) -> Dict:
        tags = tags or []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")

            # strip HTML tags basic
            import re
            text = re.sub(r"<style[^>]*>.*?</style>", "", raw, flags=re.S)
            text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.S)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s{3,}", "\n", text).strip()

            if len(text) < 50:
                return {"success": False, "reason": "content_too_short"}

            return self.learn_from_text(text, title=url, tags=tags + ["url"], source=url)

        except Exception as e:
            logger.error("learn_from_url failed", error=e)
            return {"success": False, "reason": str(e)}

    def learn_wordpress_plugin(self, plugin_path: str) -> Dict:
        """
        يتعلم من مجلد Plugin WordPress كامل
        يقرأ كل ملفات PHP, JS, CSS, README
        """
        if not os.path.isdir(plugin_path):
            return {"success": False, "reason": "not_a_directory"}

        results = []
        plugin_name = os.path.basename(plugin_path)

        for root, dirs, files in os.walk(plugin_path):
            # تجاهل vendor و node_modules
            dirs[:] = [d for d in dirs if d not in ("vendor", "node_modules", ".git")]
            for fname in files:
                fpath = os.path.join(root, fname)
                res = self.learn_from_file(fpath, tags=["wordpress", "plugin", plugin_name])
                results.append({"file": fname, **res})

        success_count = sum(1 for r in results if r.get("success"))
        logger.info("Plugin learned", context={"plugin": plugin_name, "files": success_count})
        return {"success": True, "plugin": plugin_name, "files_processed": success_count, "details": results}

    # ─────────────────────────────────────────
    #  SEARCH
    # ─────────────────────────────────────────

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        البحث في قاعدة المعرفة — يُستدعى قبل كل Task
        """
        with self._lock:
            conn = self._connect()
            cur = conn.cursor()
            results = []

            try:
                # FTS search
                cur.execute("""
                SELECT kb.id, kb.title, kb.source, kb.source_type, kb.tags,
                       snippet(knowledge_fts, 2, '[', ']', '...', 20) as snippet
                FROM knowledge_fts
                JOIN knowledge_base kb ON kb.id = knowledge_fts.id
                WHERE knowledge_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """, (query, limit))
                rows = cur.fetchall()

                for row in rows:
                    results.append({
                        "id": row[0],
                        "title": row[1],
                        "source": row[2],
                        "type": row[3],
                        "tags": json.loads(row[4] or "[]"),
                        "snippet": row[5]
                    })

                # update last_used
                if results:
                    ids = [r["id"] for r in results]
                    cur.execute(
                        f"UPDATE knowledge_base SET last_used=CURRENT_TIMESTAMP WHERE id IN ({','.join('?'*len(ids))})",
                        ids
                    )
                    conn.commit()

            except Exception as e:
                logger.error("search failed", error=e)
                # fallback: LIKE search
                cur.execute("""
                SELECT id, title, source, source_type, tags,
                       SUBSTR(content, 1, 300) as snippet
                FROM knowledge_base
                WHERE content LIKE ? OR title LIKE ?
                LIMIT ?
                """, (f"%{query}%", f"%{query}%", limit))
                rows = cur.fetchall()
                for row in rows:
                    results.append({
                        "id": row[0], "title": row[1], "source": row[2],
                        "type": row[3], "tags": json.loads(row[4] or "[]"),
                        "snippet": row[5]
                    })
            finally:
                conn.close()

            return results

    def search_for_task(self, task: str) -> Dict:
        """
        واجهة موحدة — تُستدعى قبل أي Task
        ترجع: المعرفة ذات الصلة + هل يوجد معرفة كافية
        """
        results = self.search(task, limit=3)
        has_knowledge = len(results) > 0
        summary = ""
        if results:
            summary = "\n".join([
                f"[{r['type'].upper()}] {r['title']}: {r['snippet']}"
                for r in results
            ])
        return {
            "has_knowledge": has_knowledge,
            "count": len(results),
            "results": results,
            "summary": summary
        }

    # ─────────────────────────────────────────
    #  STATS
    # ─────────────────────────────────────────

    def get_stats(self) -> Dict:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT source_type, COUNT(*) FROM knowledge_base GROUP BY source_type")
        rows = cur.fetchall()
        conn.close()
        return {
            "by_type": {row[0]: row[1] for row in rows},
            "total": sum(row[1] for row in rows)
        }

    def list_all(self) -> List[Dict]:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT id, title, source, source_type, tags, created_at FROM knowledge_base ORDER BY created_at DESC")
        rows = cur.fetchall()
        conn.close()
        return [
            {"id": r[0], "title": r[1], "source": r[2], "type": r[3],
             "tags": json.loads(r[4] or "[]"), "created_at": r[5]}
            for r in rows
        ]

    # ─────────────────────────────────────────
    #  HELPERS
    # ─────────────────────────────────────────

    def _extract_pdf(self, path: str) -> str:
        try:
            import subprocess
            result = subprocess.run(
                ["py", "-3.11", "-m", "pdfminer.high_level", path],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except Exception:
            pass
        # fallback: raw read
        try:
            with open(path, "rb") as f:
                raw = f.read()
            import re
            text = re.findall(b"BT(.+?)ET", raw, re.S)
            extracted = b" ".join(text).decode("latin-1", errors="ignore")
            return extracted[:50000]
        except Exception:
            return ""


# Singleton
knowledge_manager = KnowledgeManager()
