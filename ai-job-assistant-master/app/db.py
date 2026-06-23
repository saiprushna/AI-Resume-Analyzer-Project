"""SQLite storage for the latest analysis (optional audit trail)."""

import json
import sqlite3
from datetime import datetime, timezone

from config import DATA_DIR, DB_PATH


def _connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_name TEXT,
                target_role TEXT NOT NULL,
                ats_score INTEGER,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def save_analysis(response_dict: dict):
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO analyses (candidate_name, target_role, ats_score, response_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                response_dict.get("candidate_name"),
                response_dict.get("target_role"),
                response_dict.get("ats_score"),
                json.dumps(response_dict, default=str),
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def get_latest(limit: int = 5) -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT candidate_name, target_role, ats_score, created_at
            FROM analyses
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
