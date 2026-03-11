import os
import sqlite3
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

_DB_PATH = os.getenv("SQLITE_DB_PATH", "./data/sessions.db")


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    return sqlite3.connect(_DB_PATH)


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role       TEXT NOT NULL,
                content    TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON sessions (session_id)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_meta (
                session_id TEXT PRIMARY KEY,
                context    TEXT NOT NULL,
                background TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def save_turn(session_id: str, role: str, content: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO sessions (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        conn.commit()


def load_turns(session_id: str, limit: int = 10) -> list:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM (
                SELECT role, content, id FROM sessions
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
            ) ORDER BY id ASC
            """,
            (session_id, limit),
        ).fetchall()
    return [{"role": row[0], "content": row[1]} for row in rows]


def save_session_meta(session_id: str, context: str, background: str) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO session_meta (session_id, context, background)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id) DO NOTHING
            """,
            (session_id, context, background),
        )
        conn.commit()


def load_session_meta(session_id: str) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT context, background FROM session_meta WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    if row is None:
        return None
    return {"context": row[0], "background": row[1]}
