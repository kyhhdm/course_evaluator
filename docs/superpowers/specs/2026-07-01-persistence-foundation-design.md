# Persistence Foundation — Design (Sub-project A)

**Date:** 2026-07-01
**Status:** Approved, pending implementation plan
**Scope:** First of two sub-projects for the self-hosted multi-student online testing app.
This sub-project is the **headless data backbone**: store students and their saved evaluation
attempts, and render a report from a stored attempt. Sub-project B (the web app) is **out of
scope here** and will sit on this storage API.

## Goal

Persist students and their test attempts so results survive across runs and accumulate into a
per-student history — without recomputation drift. A saved attempt freezes a re-renderable
snapshot of its result, so an old report renders faithfully even after the course's items
change.

## Non-goals

- No web server, HTTP, or frontend (that is Sub-project B).
- No accounts/auth, no multi-tenant isolation, no concurrency hardening beyond SQLite defaults.
- No change to scoring, bands, path-ordering, coverage, or the item bank.
- No new third-party dependency.

## Storage — SQLite via the standard library

A single SQLite database accessed through Python's built-in `sqlite3` (**zero new
dependency**; transactional; queryable; one file). A new module **`engine/store.py`** owns all
database access — schema creation on first connect, and every query. Import direction stays
clean: `store.py` imports the engine (`loader`, `score`, `path`, `report_view`, `paper`); the
engine never imports `store`.

DB path resolution (in `store.py`): explicit `db_path` argument > `COURSE_EVAL_DB` env var >
default `var/course_evaluator.db`. `var/` is git-ignored. `init_db(db_path)` creates the parent
directory and the schema if absent (idempotent). (`db_path` is named distinctly from the
engine's learning-`path` to avoid confusion.)

## Schema

```sql
CREATE TABLE IF NOT EXISTS students (
  id         INTEGER PRIMARY KEY,
  name       TEXT NOT NULL,
  created_at TEXT NOT NULL              -- ISO-8601 string
);
CREATE TABLE IF NOT EXISTS attempts (
  id            INTEGER PRIMARY KEY,
  student_id    INTEGER NOT NULL REFERENCES students(id),
  course_id     TEXT NOT NULL,          -- e.g. "grade5_math"
  created_at    TEXT NOT NULL,
  responses_json TEXT NOT NULL,         -- source of truth: {item_id: answer}
  snapshot_json  TEXT NOT NULL          -- frozen, re-renderable result (below)
);
CREATE INDEX IF NOT EXISTS idx_attempts_student ON attempts(student_id);
```

Timestamps are ISO-8601 strings passed in by the caller (the engine forbids wall-clock calls
in some contexts; `store` accepts a `created_at` argument, defaulting to
`datetime.now().isoformat(timespec="seconds")` at the call site in `save_attempt`).

## The snapshot (frozen, structured, re-renderable)

`snapshot_json` is **structured data, not rendered HTML** — so a saved report can be restyled
later but never needs recompute or the live item bank. Shape:

```json
{
  "parent_view": { ...dataclasses.asdict(ParentReportView)... },
  "student_plan": {
    "strands": [{"strand": "...", "band": "Developing"}, ...],
    "steps":   [{"title": "...", "practice_prompts": ["...", "..."]}, ...]
  }
}
```

- `parent_view` is `dataclasses.asdict(build_parent_view(curriculum, result, path, name))`.
  It already contains resolved point **titles** (in `strand_groups`), strengths, counts, and
  `focus` (PathStep dicts), so it renders with no live curriculum.
- `student_plan.steps` stores each path step's title plus its practice-item **prompts**
  resolved at attempt time (`curriculum.items[id].prompt`), so a later-removed/renamed item
  never breaks an old plan. The full path is stored; the 5-step cap is a render-time concern.

This freezes everything the parent and student reports need.

## Module API (`engine/store.py`)

- `init_db(db_path: str | None = None) -> None` — connect, create schema if absent.
- `create_student(name: str, db_path: str | None = None) -> int` — insert, return id.
- `list_students(db_path: str | None = None) -> list[dict]` — `[{id, name, created_at}]`, by id.
- `save_attempt(student_id: int, course_id: str, responses: dict, curriculum: Curriculum, db_path: str | None = None) -> int`
  — drops blank responses (`drop_blank_responses`), runs `evaluate` then `build_path`, builds
  the snapshot, inserts the attempt, returns its id.
- `list_attempts(student_id: int, db_path: str | None = None) -> list[dict]` — `[{id, course_id,
  created_at, summary}]` newest-first, where `summary` is derived from the snapshot
  (`"{secure_strand_count} of {total_strand_count} areas secure"`).
- `get_attempt(attempt_id: int, db_path: str | None = None) -> dict` — `{id, student_id,
  course_id, created_at, responses, snapshot}` (JSON fields parsed back to objects).

`save_attempt` takes the already-loaded `Curriculum` (callers load it once via `load_course`);
`store.py` does not own course loading.

## Enabling refactor: split view-building from view-rendering

To render a parent report from a snapshot **without** the live curriculum, separate building
the view from rendering it. In `engine/paper.py`:

- Add `render_parent_view(view, templates_dir: str) -> str` — renders `report.html.j2` from an
  already-built view. It accepts **either** a `ParentReportView` dataclass **or** the plain
  dict from `dataclasses.asdict` / `json.loads` — the templates use Jinja attribute/item
  access and none of the view's keys collide with dict methods, so both work identically.
- `render_report_html(curriculum, result, path, templates_dir, student_name)` becomes
  `build_parent_view(...)` → `render_parent_view(view, templates_dir)`. Backward-compatible:
  the public signature and output are unchanged.

`store.py` exposes `render_attempt_html(attempt: dict, templates_dir: str = "templates") -> str`
= `render_parent_view(attempt["snapshot"]["parent_view"], templates_dir)`, proving the snapshot
is sufficient to render the parent report with no recompute.

## Testing (`tests/test_store.py`, temp DB via `tmp_path`)

- `init_db` is idempotent; `create_student`/`list_students` round-trip.
- `save_attempt` persists `responses_json` and a `snapshot_json` containing both `parent_view`
  and `student_plan`; `get_attempt` parses them back; `list_attempts` is newest-first with a
  correct summary.
- **Snapshot sufficiency:** `render_attempt_html(get_attempt(id))` produces the same key
  content (student name, a strand band, a "Secure:" group, the Strengths sentence) as rendering
  the same attempt live via `render_report_html`.
- **Content-drift immunity:** after saving an attempt, render it from the snapshot while the
  in-memory curriculum has had a point/item removed — the report still renders and shows the
  frozen titles.
- `render_parent_view` renders identically from a `ParentReportView` and from its
  `dataclasses.asdict` dict (a focused unit test in `tests/test_paper.py`).
- Existing `render_report_html` tests still pass (refactor is behavior-preserving).
- Run via `uv run pytest`.

## Risks / mitigations

- **Snapshot/view drift if `ParentReportView` changes shape** — mitigated by always
  serializing via `dataclasses.asdict` and rendering through the shared `render_parent_view`;
  old snapshots remain renderable as long as the template tolerates missing optional keys
  (documented: schema-evolving the view is a future concern, acceptable for a self-hosted tool).
- **DB file location/permissions** — `init_db` creates `var/` and is idempotent; path is
  configurable; `var/` git-ignored.
- **Timestamp determinism** — `store` accepts `created_at`; only `save_attempt`/`create_student`
  stamp "now" at the boundary, keeping the engine pure.
