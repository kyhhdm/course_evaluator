from __future__ import annotations

import dataclasses
import json
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


def save_attempt(
    student_id: int,
    course_id: str,
    responses: dict,
    curriculum,
    db_path: str | None = None,
    created_at: str | None = None,
) -> int:
    from engine.paper import drop_blank_responses
    from engine.path import build_path
    from engine.report_view import build_parent_view
    from engine.review import build_review
    from engine.score import evaluate

    clean = drop_blank_responses(responses)
    result = evaluate(curriculum, clean)
    learning_path = build_path(curriculum, result)

    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT name FROM students WHERE id = ?", (student_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"unknown student_id {student_id}")
        name = row["name"]

        view = build_parent_view(curriculum, result, learning_path, name)
        student_plan = {
            "strands": [{"strand": s.strand, "band": s.band} for s in result.strands],
            "steps": [
                {
                    "title": step.title,
                    "practice_prompts": [
                        curriculum.items[i].prompt for i in step.practice_item_ids
                    ],
                }
                for step in learning_path
            ],
        }
        snapshot = {
            "version": 2,  # v2 adds the frozen per-question review
            "parent_view": dataclasses.asdict(view),
            "student_plan": student_plan,
            "review": build_review(curriculum, clean),
        }

        cur = conn.execute(
            "INSERT INTO attempts(student_id, course_id, created_at, responses_json, snapshot_json)"
            " VALUES (?, ?, ?, ?, ?)",
            (student_id, course_id, created_at or _now(), json.dumps(clean), json.dumps(snapshot)),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def list_attempts(student_id: int, db_path: str | None = None) -> list[dict]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, course_id, created_at, snapshot_json FROM attempts"
            " WHERE student_id = ? ORDER BY created_at DESC, id DESC",
            (student_id,),
        ).fetchall()
        out = []
        for r in rows:
            pv = json.loads(r["snapshot_json"])["parent_view"]
            summary = f'{pv["secure_strand_count"]} of {pv["total_strand_count"]} areas secure'
            out.append(
                {
                    "id": r["id"],
                    "course_id": r["course_id"],
                    "created_at": r["created_at"],
                    "summary": summary,
                }
            )
        return out
    finally:
        conn.close()


def render_attempt_html(attempt: dict, templates_dir: str = "templates") -> str:
    from engine.paper import render_parent_view

    return render_parent_view(attempt["snapshot"]["parent_view"], templates_dir)


def get_attempt(attempt_id: int, db_path: str | None = None) -> dict | None:
    conn = _connect(db_path)
    try:
        r = conn.execute("SELECT * FROM attempts WHERE id = ?", (attempt_id,)).fetchone()
        if r is None:
            return None
        return {
            "id": r["id"],
            "student_id": r["student_id"],
            "course_id": r["course_id"],
            "created_at": r["created_at"],
            "responses": json.loads(r["responses_json"]),
            "snapshot": json.loads(r["snapshot_json"]),
        }
    finally:
        conn.close()
