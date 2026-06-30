# Persistence Foundation Implementation Plan (Sub-project A)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist students and their test attempts in a SQLite database, where each attempt freezes a re-renderable snapshot of its result so old reports render faithfully without recompute.

**Architecture:** A new `engine/store.py` owns all `sqlite3` access (stdlib). `save_attempt` runs the engine (`evaluate`→`build_path`) and stores responses + a structured snapshot (`dataclasses.asdict` of the parent view, plus a student-plan block with frozen titles/prompts). A small refactor extracts `render_parent_view` so live and snapshot rendering share one path. Headless and fully unit-tested; the web app (Sub-project B) sits on this API.

**Tech Stack:** Python ≥3.10 (stdlib `sqlite3`, `json`, `dataclasses`, `datetime`, `pathlib`), jinja2, pytest. Package management via `uv`. No new dependency.

## Global Constraints

- Python `>=3.10`. Manage packages with `uv`; run tests with `uv run pytest`. **No new dependency** (SQLite is stdlib `sqlite3`).
- Import direction is one-way: `engine/store.py` imports the engine; the engine never imports `store`.
- DB path resolution: explicit `db_path` arg > `COURSE_EVAL_DB` env var > default `var/course_evaluator.db`. `var/` is git-ignored. The DB-file argument is named `db_path` (distinct from the engine's learning-`path`).
- The snapshot is **structured data, not rendered HTML**: `{"parent_view": dataclasses.asdict(view), "student_plan": {"strands": [...], "steps": [...]}}`. Practice-item **prompts** and point **titles** are frozen at attempt time.
- No change to scoring, bands, path-ordering, coverage, or the item bank. The `render_report_html` public signature and output stay unchanged (behavior-preserving refactor).
- Timestamps are ISO-8601 strings stamped at the `store` boundary (`datetime.now().isoformat(timespec="seconds")`), overridable via a `created_at` argument for deterministic tests.

## File Structure

- Create `engine/store.py` — all DB access + snapshot building + `render_attempt_html`.
- Modify `engine/paper.py` — extract `render_parent_view`; `render_report_html` delegates.
- Modify `.gitignore` — ignore `var/`.
- Create `tests/test_store.py`; extend `tests/test_paper.py`.

---

### Task 1: Extract `render_parent_view` (enabling refactor)

**Files:**
- Modify: `engine/paper.py` (`render_report_html`)
- Test: `tests/test_paper.py`

**Interfaces:**
- Produces: `render_parent_view(view, templates_dir: str) -> str` — renders `report.html.j2` from an already-built view; accepts a `ParentReportView` dataclass OR its `dataclasses.asdict` dict.
- `render_report_html(curriculum, result, path, templates_dir, student_name="Student") -> str` unchanged externally.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_paper.py`:

```python
def test_render_parent_view_accepts_dataclass_and_dict():
    import dataclasses
    from engine.paper import render_parent_view
    from engine.report_view import build_parent_view
    c = _curriculum()
    pa = PointResult("a", 0.9, "Secure", "scored", 2)
    pb = PointResult("b", 0.4, "Not yet", "scored", 2)
    strand = StrandResult("Fractions", "Developing", 0.65, "b", [pa, pb])
    result = EvaluationResult([strand], {"a": pa, "b": pb}, {"A1"})
    path = [PathStep("b", "Add fractions", ["B1"])]
    view = build_parent_view(c, result, path, "Sam")
    html_dc = render_parent_view(view, TEMPLATES)
    html_dict = render_parent_view(dataclasses.asdict(view), TEMPLATES)
    assert html_dc == html_dict                       # dict renders identically to dataclass
    assert "Sam" in html_dc and "Strengths" in html_dc
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_paper.py::test_render_parent_view_accepts_dataclass_and_dict -v`
Expected: FAIL with `ImportError: cannot import name 'render_parent_view'`.

- [ ] **Step 3: Refactor `engine/paper.py`**

Replace the `render_report_html` function with these two functions:

```python
def render_parent_view(view, templates_dir: str) -> str:
    tmpl = _env(templates_dir).get_template("report.html.j2")
    return tmpl.render(view=view)


def render_report_html(
    curriculum: Curriculum,
    result: EvaluationResult,
    path: list[PathStep],
    templates_dir: str,
    student_name: str = "Student",
) -> str:
    from engine.report_view import build_parent_view

    view = build_parent_view(curriculum, result, path, student_name)
    return render_parent_view(view, templates_dir)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_paper.py -v`
Expected: PASS — the new test plus the existing `test_report_html_*` tests (output unchanged).

- [ ] **Step 5: Commit**

```bash
git add engine/paper.py tests/test_paper.py
git commit -m "refactor(report): extract render_parent_view for view-based rendering"
```

---

### Task 2: `store.py` foundation — DB, schema, students

**Files:**
- Create: `engine/store.py`
- Modify: `.gitignore`
- Test: `tests/test_store.py`

**Interfaces:**
- Produces:
  - `init_db(db_path: str | None = None) -> None`
  - `create_student(name: str, db_path: str | None = None, created_at: str | None = None) -> int`
  - `list_students(db_path: str | None = None) -> list[dict]` — `[{id, name, created_at}]` by id.
  - internal: `_connect(db_path)` (ensures schema, `Row` factory, FKs on), `_resolve_db_path(db_path)`.

- [ ] **Step 1: Ignore the DB directory**

Append to `.gitignore`:

```
var/
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_store.py`:

```python
from engine import store


def _db(tmp_path):
    return str(tmp_path / "test.db")


def test_init_db_is_idempotent(tmp_path):
    db = _db(tmp_path)
    store.init_db(db)
    store.init_db(db)  # second call must not raise
    assert (tmp_path / "test.db").exists()


def test_create_and_list_students(tmp_path):
    db = _db(tmp_path)
    sid1 = store.create_student("Maya", db_path=db)
    sid2 = store.create_student("Leo", db_path=db)
    assert sid1 != sid2
    students = store.list_students(db_path=db)
    assert [s["name"] for s in students] == ["Maya", "Leo"]   # ordered by id
    assert all("created_at" in s for s in students)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_store.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engine.store'`.

- [ ] **Step 4: Create `engine/store.py`**

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_store.py -v`
Expected: PASS (both tests).

- [ ] **Step 6: Commit**

```bash
git add engine/store.py tests/test_store.py .gitignore
git commit -m "feat(store): sqlite foundation with student CRUD"
```

---

### Task 3: `save_attempt` + `get_attempt` (snapshot building)

**Files:**
- Modify: `engine/store.py`
- Test: `tests/test_store.py`

**Interfaces:**
- Consumes: `_connect`, `_now` (Task 2); engine `drop_blank_responses`, `evaluate`, `build_path`, `build_parent_view`.
- Produces:
  - `save_attempt(student_id: int, course_id: str, responses: dict, curriculum: Curriculum, db_path: str | None = None, created_at: str | None = None) -> int`
  - `get_attempt(attempt_id: int, db_path: str | None = None) -> dict | None` — `{id, student_id, course_id, created_at, responses, snapshot}` (JSON parsed).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_store.py`:

```python
from engine.loader import load_course, load_yaml

CURRICULUM = "curriculum/grade5_math"


def _grade5():
    return load_course(CURRICULUM, "schemas", "methodology", "standards")


def test_save_and_get_attempt_roundtrips_with_snapshot(tmp_path):
    db = _db(tmp_path)
    sid = store.create_student("Maya", db_path=db)
    responses = load_yaml(f"{CURRICULUM}/sample_responses.yaml")["responses"]
    aid = store.save_attempt(sid, "grade5_math", responses, _grade5(), db_path=db)

    got = store.get_attempt(aid, db_path=db)
    assert got["student_id"] == sid
    assert got["course_id"] == "grade5_math"
    assert got["responses"]["EQF-1"] == responses["EQF-1"]      # source of truth stored
    snap = got["snapshot"]
    assert "parent_view" in snap and "student_plan" in snap
    assert snap["parent_view"]["student_name"] == "Maya"        # name resolved into the view
    assert "strands" in snap["student_plan"] and "steps" in snap["student_plan"]


def test_get_attempt_returns_none_for_unknown_id(tmp_path):
    store.init_db(_db(tmp_path))
    assert store.get_attempt(999, db_path=_db(tmp_path)) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_store.py::test_save_and_get_attempt_roundtrips_with_snapshot -v`
Expected: FAIL with `AttributeError: module 'engine.store' has no attribute 'save_attempt'`.

- [ ] **Step 3: Implement `save_attempt` and `get_attempt`**

Append to `engine/store.py` (add `import dataclasses` and `import json` to the top imports):

```python
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
    from engine.score import evaluate

    clean = drop_blank_responses(responses)
    result = evaluate(curriculum, clean)
    learning_path = build_path(curriculum, result)

    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT name FROM students WHERE id = ?", (student_id,)
        ).fetchone()
        name = row["name"] if row else "Student"

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
        snapshot = {"parent_view": dataclasses.asdict(view), "student_plan": student_plan}

        cur = conn.execute(
            "INSERT INTO attempts(student_id, course_id, created_at, responses_json, snapshot_json)"
            " VALUES (?, ?, ?, ?, ?)",
            (student_id, course_id, created_at or _now(), json.dumps(clean), json.dumps(snapshot)),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_store.py -v`
Expected: PASS (all store tests).

- [ ] **Step 5: Commit**

```bash
git add engine/store.py tests/test_store.py
git commit -m "feat(store): save_attempt builds frozen snapshot; get_attempt round-trips"
```

---

### Task 4: `list_attempts` + `render_attempt_html` (history + snapshot rendering)

**Files:**
- Modify: `engine/store.py`
- Test: `tests/test_store.py`

**Interfaces:**
- Consumes: `_connect` (Task 2), `save_attempt`/`get_attempt` (Task 3); engine `render_parent_view` (Task 1).
- Produces:
  - `list_attempts(student_id: int, db_path: str | None = None) -> list[dict]` — `[{id, course_id, created_at, summary}]` newest-first.
  - `render_attempt_html(attempt: dict, templates_dir: str = "templates") -> str` — renders the parent report from the stored snapshot.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_store.py`:

```python
def test_list_attempts_newest_first_with_summary(tmp_path):
    db = _db(tmp_path)
    sid = store.create_student("Maya", db_path=db)
    responses = load_yaml(f"{CURRICULUM}/sample_responses.yaml")["responses"]
    c = _grade5()
    a1 = store.save_attempt(sid, "grade5_math", responses, c, db_path=db, created_at="2026-01-01T09:00:00")
    a2 = store.save_attempt(sid, "grade5_math", responses, c, db_path=db, created_at="2026-02-01T09:00:00")

    listed = store.list_attempts(sid, db_path=db)
    assert [a["id"] for a in listed] == [a2, a1]                 # newest first
    assert "areas secure" in listed[0]["summary"]


def test_render_attempt_html_matches_live_and_survives_content_change(tmp_path):
    from engine.paper import render_report_html
    from engine.path import build_path
    from engine.score import evaluate
    from engine.paper import drop_blank_responses

    db = _db(tmp_path)
    sid = store.create_student("Maya", db_path=db)
    responses = load_yaml(f"{CURRICULUM}/sample_responses.yaml")["responses"]
    c = _grade5()
    aid = store.save_attempt(sid, "grade5_math", responses, c, db_path=db)

    # snapshot render matches a live render of the same attempt (key content)
    clean = drop_blank_responses(responses)
    live = render_report_html(c, evaluate(c, clean), build_path(c, evaluate(c, clean)), "templates", "Maya")
    from_snapshot = store.render_attempt_html(store.get_attempt(aid, db_path=db))
    for marker in ("Learning Report for Maya", "Strengths", "fully Secure in"):
        assert marker in live and marker in from_snapshot

    # content-drift immunity: mutate the in-memory curriculum, snapshot still renders
    c.points.clear()
    c.items.clear()
    still = store.render_attempt_html(store.get_attempt(aid, db_path=db))
    assert "Learning Report for Maya" in still      # frozen titles, no recompute needed
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_store.py::test_render_attempt_html_matches_live_and_survives_content_change -v`
Expected: FAIL with `AttributeError: module 'engine.store' has no attribute 'render_attempt_html'`.

- [ ] **Step 3: Implement `list_attempts` and `render_attempt_html`**

Append to `engine/store.py`:

```python
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
```

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -q`
Expected: PASS (entire suite green).

- [ ] **Step 5: Commit**

```bash
git add engine/store.py tests/test_store.py
git commit -m "feat(store): list_attempts history + render_attempt_html from snapshot"
```

---

## Self-Review

**Spec coverage:**
- SQLite/stdlib, `engine/store.py` owns DB access, one-way imports → Tasks 2–4. ✓
- DB path resolution (`db_path` > env > default), `var/` ignored, `init_db` idempotent → Task 2. ✓
- Schema (students, attempts with responses_json + snapshot_json, index) → Task 2 (`_SCHEMA`). ✓
- Snapshot = `dataclasses.asdict(view)` + student_plan (frozen titles/prompts) → Task 3. ✓
- API: init_db/create_student/list_students/save_attempt/list_attempts/get_attempt → Tasks 2–4. ✓
- `save_attempt` drops blanks, runs evaluate→build_path, resolves student name → Task 3. ✓
- Enabling refactor `render_parent_view` (dataclass or dict), behavior-preserving → Task 1. ✓
- `render_attempt_html` proves snapshot sufficiency + content-drift immunity → Task 4. ✓
- Timestamps at the boundary, `created_at` overridable for tests → Tasks 2–3 (`_now`, params). ✓
- No new dependency; no scoring/bands/path/coverage/item-bank change → honored throughout. ✓

**Placeholder scan:** No TBD/TODO/vague steps; every code and test step shows complete code and exact commands. ✓

**Type consistency:** `render_parent_view(view, templates_dir)` defined in Task 1, consumed by `render_attempt_html` in Task 4. `_connect`/`_now`/`_resolve_db_path` defined in Task 2, used in Tasks 3–4. `save_attempt(... curriculum ...)` / `get_attempt` / `list_attempts` / `render_attempt_html` signatures match between their Interfaces blocks, the test calls, and the implementations. `db_path` is the consistent DB-file argument name across all functions. Snapshot keys (`parent_view`, `student_plan`, `secure_strand_count`, `total_strand_count`) match between Task 3 (write) and Task 4 (read). ✓
