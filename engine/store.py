from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path

DEFAULT_DB = "var/course_evaluator.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
  id         INTEGER PRIMARY KEY,
  name       TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (
  id             INTEGER PRIMARY KEY,
  student_id     INTEGER NOT NULL REFERENCES students(id),
  course_id      TEXT NOT NULL,
  created_at     TEXT NOT NULL,
  responses_json TEXT NOT NULL,
  snapshot_json  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attempts_student ON attempts(student_id);
"""


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _resolve_db_path(db_path: str | None) -> str:
    return db_path or os.environ.get("COURSE_EVAL_DB") or DEFAULT_DB


def _connect(db_path: str | None) -> sqlite3.Connection:
    resolved = _resolve_db_path(db_path)
    Path(resolved).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(resolved)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA)
    return conn


def init_db(db_path: str | None = None) -> None:
    _connect(db_path).close()


def create_student(name: str, db_path: str | None = None, created_at: str | None = None) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO students(name, created_at) VALUES (?, ?)",
            (name, created_at or _now()),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def list_students(db_path: str | None = None) -> list[dict]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, name, created_at FROM students ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
