import json
import os
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("DATABASE_PATH", "data/interviewbuddy.db"))


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                resume_name TEXT,
                questions_json TEXT NOT NULL,
                evaluations_json TEXT NOT NULL,
                final_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def create_session(
    role: str,
    difficulty: str,
    resume_name: str,
    questions: list[dict[str, Any]],
) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO sessions
            (role, difficulty, resume_name, questions_json, evaluations_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                role,
                difficulty,
                resume_name,
                json.dumps(questions, ensure_ascii=False),
                "[]",
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def save_evaluation(
    session_id: int,
    evaluation: dict[str, Any],
) -> None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT evaluations_json FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()

        if not row:
            raise ValueError("Session not found.")

        evaluations = json.loads(row["evaluations_json"])
        evaluations.append(evaluation)

        conn.execute(
            "UPDATE sessions SET evaluations_json = ? WHERE id = ?",
            (json.dumps(evaluations, ensure_ascii=False), session_id),
        )
        conn.commit()


def save_final(
    session_id: int,
    final: dict[str, Any],
) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE sessions SET final_json = ? WHERE id = ?",
            (json.dumps(final, ensure_ascii=False), session_id),
        )
        conn.commit()


def get_sessions() -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, role, difficulty, resume_name, created_at
            FROM sessions
            ORDER BY id DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]


def get_session(session_id: int) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()

        if not row:
            return None

        data = dict(row)
        data["questions"] = json.loads(data.pop("questions_json"))
        data["evaluations"] = json.loads(data.pop("evaluations_json"))
        data["final"] = json.loads(data["final_json"]) if data.get("final_json") else None
        data.pop("final_json", None)
        return data
