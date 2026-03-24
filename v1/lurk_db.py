"""
lurk db — single SQLite file replacing per-user .txt memory files and the
chatter_state.json. All storage goes through this module.

Schema
------
messages   — rolling window of recent chat (pruned on each run)
memories   — per-user (and #channel) knowledge base with timestamps
bot_state  — key/value bag for scalar bot state (last_spoke_ts, style history…)
"""

import json
import sqlite3
import time

DB_PATH = "lurk.db"


class DB:
    def __init__(self, path: str = DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS messages (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                ts              INTEGER NOT NULL,
                username        TEXT    NOT NULL,
                content         TEXT    NOT NULL,
                reply_to_user   TEXT    NOT NULL DEFAULT '',
                reply_to_msg    TEXT    NOT NULL DEFAULT '',
                seen            INTEGER NOT NULL DEFAULT 0,
                is_bot          INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS memories (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user        TEXT    NOT NULL,   -- '#channel' for room-level memories
                content     TEXT    NOT NULL,
                created_at  INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS memories_user ON memories(user, created_at);

            CREATE TABLE IF NOT EXISTS bot_state (
                key     TEXT PRIMARY KEY,
                value   TEXT NOT NULL           -- JSON-encoded
            );
        """)
        self.conn.commit()

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    def add_message(
        self,
        ts: int,
        username: str,
        content: str,
        reply_to_user: str = "",
        reply_to_msg: str = "",
        is_bot: bool = False,
    ) -> int:
        cur = self.conn.execute(
            """INSERT INTO messages
               (ts, username, content, reply_to_user, reply_to_msg, is_bot)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (ts, username, content, reply_to_user, reply_to_msg, int(is_bot)),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_recent_messages(self, window_seconds: int,
                            limit: int = 20) -> list[dict]:
        """Return up to `limit` messages from the last `window_seconds`, oldest first."""
        cutoff = int(time.time()) - window_seconds
        rows = self.conn.execute(
            """SELECT * FROM messages
               WHERE ts > ?
               ORDER BY ts DESC
               LIMIT ?""",
            (cutoff, limit),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def mark_seen(self, message_id: int):
        self.conn.execute(
            "UPDATE messages SET seen=1 WHERE id=?", (message_id,))
        self.conn.commit()

    def prune_old_messages(self, window_seconds: int):
        cutoff = int(time.time()) - window_seconds
        self.conn.execute("DELETE FROM messages WHERE ts < ?", (cutoff,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Memories
    # ------------------------------------------------------------------

    def get_memories(self, user: str) -> list[dict]:
        """All memories for `user`, oldest first."""
        rows = self.conn.execute(
            "SELECT * FROM memories WHERE user=? ORDER BY created_at ASC",
            (user,),
        ).fetchall()
        return [dict(r) for r in rows]

    def add_memory(self, user: str, content: str):
        self.conn.execute(
            "INSERT INTO memories (user, content, created_at) VALUES (?, ?, ?)",
            (user, content, int(time.time())),
        )
        self.conn.commit()

    def prune_memories(self, user: str, keep_n: int):
        """Delete all but the most recent `keep_n` memories for `user`."""
        self.conn.execute(
            """DELETE FROM memories
               WHERE user = ?
                 AND id NOT IN (
                     SELECT id FROM memories
                     WHERE user = ?
                     ORDER BY created_at DESC
                     LIMIT ?
                 )""",
            (user, user, keep_n),
        )
        self.conn.commit()

    def memory_word_count(self, user: str) -> int:
        rows = self.get_memories(user)
        return sum(len(r["content"].split()) for r in rows)

    # ------------------------------------------------------------------
    # Bot state
    # ------------------------------------------------------------------

    def get_state(self, key: str, default=None):
        row = self.conn.execute(
            "SELECT value FROM bot_state WHERE key=?", (key,)
        ).fetchone()
        if row is None:
            return default
        return json.loads(row["value"])

    def set_state(self, key: str, value):
        self.conn.execute(
            "INSERT OR REPLACE INTO bot_state (key, value) VALUES (?, ?)",
            (key, json.dumps(value)),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
