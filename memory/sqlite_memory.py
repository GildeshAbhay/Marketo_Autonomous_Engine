# memory/sqlite_memory.py
"""
Simple SQLite-backed memory adapter for ADK agents (POC-level).
Provides small utilities to save/retrieve query history and context.
"""

import sqlite3
import threading
import json
from typing import Any, Dict, List, Optional

DB_PATH = "memory/agent_memory.db"  # relative to project root

_LOCK = threading.Lock()


def _get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    """Create tables if missing."""
    with _LOCK:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                direction TEXT NOT NULL,  -- 'in' or 'out'
                content TEXT NOT NULL,
                metadata TEXT
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS context (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at INTEGER NOT NULL
            );
            """
        )
        conn.commit()
        conn.close()


def save_query(timestamp: int, direction: str, content: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> int:
    """
    Save a query or response to history.
    direction: 'in' for user->system, 'out' for system->user
    content: JSON-serializable dict
    returns: inserted row id
    """
    initialize_db()
    with _LOCK:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO queries (timestamp, direction, content, metadata) VALUES (?, ?, ?, ?)",
            (timestamp, direction, json.dumps(content), json.dumps(metadata or {})),
        )
        rowid = cur.lastrowid
        conn.commit()
        conn.close()
        return rowid


def fetch_recent_queries(limit: int = 20) -> List[Dict[str, Any]]:
    """Return recent query history (most recent first)."""
    initialize_db()
    with _LOCK:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, timestamp, direction, content, metadata FROM queries ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
    return [
        {
            "id": r["id"],
            "timestamp": r["timestamp"],
            "direction": r["direction"],
            "content": json.loads(r["content"]),
            "metadata": json.loads(r["metadata"] or "{}"),
        }
        for r in rows
    ]


def set_context(key: str, value: Dict[str, Any], updated_at: int):
    """Set or update key in context table."""
    initialize_db()
    with _LOCK:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO context (key, value, updated_at) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, json.dumps(value), updated_at),
        )
        conn.commit()
        conn.close()


def get_context(key: str) -> Optional[Dict[str, Any]]:
    initialize_db()
    with _LOCK:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT value FROM context WHERE key = ?", (key,))
        row = cur.fetchone()
        conn.close()
    if row:
        return json.loads(row["value"])
    return None
