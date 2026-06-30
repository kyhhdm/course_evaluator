# Online Testing Web App — Design (Sub-project B)

**Date:** 2026-07-01
**Status:** Approved, pending implementation plan
**Scope:** The self-hosted multi-student web app that lets a child take a diagnostic test
online and produces an auto-scored report, with per-student history. Built entirely on the
merged persistence foundation (`engine/store.py`, PR #7) and the existing engine. This is the
second and final sub-project of the web-app effort.

## Goal

A small Flask web app a family/tutor self-hosts: add students, have a child take a diagnostic
test one question at a time in the browser, auto-score on completion, and view the resulting
report plus the student's past attempts.

## Non-goals

- No accounts/auth/login, no multi-tenant isolation, no public-internet hardening.
- No partial-attempt persistence in the DB (in-progress state lives in the session cookie).
- No change to scoring, bands, path-ordering, coverage, the item bank, or the report content.
- No production WSGI server, HTTPS, or deployment automation (dev server only; documented).
- No editing of students/attempts beyond create (delete/update are a later concern).

## Dependency

Add **Flask** via `uv add flask` — the one deliberate new runtime dependency. It renders the
jinja2 templates already in use and ships a `test_client` for route tests. Documented in
CLAUDE.md's runtime-deps line.

## Architecture

- **`engine/web.py`** — the only web module: a Flask app factory `create_app()` plus the
  routes. It imports `engine.store`, `engine.loader`, and `engine.paper` (`ordered_items`);
  it never adds logic the engine owns. `python -m engine.web` runs the dev server.
- **`templates/web/`** — new jinja2 HTML templates (`base.html` + page templates), separate
  from the report/print templates. The report itself is rendered by the existing
  `store.render_attempt_html`.
- Config from the environment: `COURSE_EVAL_DB` (already honored by `store`),
  `COURSE_EVAL_SECRET` (Flask session signing key; falls back to a persisted `var/secret_key`),
  `COURSE_EVAL_HOST`/`COURSE_EVAL_PORT` (default `127.0.0.1:5000`).

### Import direction
`engine/web.py` imports the engine + store; nothing in the engine imports `web`. Flask is
imported only in `engine/web.py`, keeping the rest of the engine framework-free and its tests
Flask-free.

## Routes & flow

| Method & path | Purpose |
|---|---|
| `GET /` | Home: list students (in `store.list_students` id order) + an "add student" form; list available courses. |
| `POST /students` | `create_student(name)`; reject empty name (flash + redirect home); else redirect to the student page. |
| `GET /students/<id>` | Student page: the student's attempt history (each links to its report) + a "Start test" control per available course. |
| `GET /students/<id>/test` | Wizard: render the current question (seeds session state on first entry / fresh start). |
| `POST /students/<id>/test` | Record the submitted answer, advance (Next) or step back (Back); on the last question, save the attempt and redirect to its report. |
| `GET /attempts/<aid>` | The saved report, via `store.render_attempt_html(get_attempt(aid))`; 404 if unknown. |

Unknown `student_id`/`attempt_id` → 404. The report page is the complete styled HTML the
snapshot renderer already produces (reused directly, no duplication).

## Wizard state machine (signed session cookie)

In-progress state lives in the Flask session under one key, e.g.
`session["attempt"] = {"student_id": int, "course_id": str, "item_ids": [str, ...], "idx": int,
"answers": {item_id: str}}`.

- **Seed/reset:** entering `GET /students/<id>/test` with `?start=1` (the "Start test" button),
  or when no session attempt exists, or when the session's `student_id`/`course_id` doesn't
  match the request, (re)seeds: `item_ids = [it.id for it in ordered_items(curriculum)]`
  (deterministic diagnostic order), `idx = 0`, `answers = {}`.
- **Render:** the current item is `item_ids[idx]`; the template shows "Question {idx+1} of
  {len(item_ids)}", a progress bar, the prompt, MCQ options as radio inputs (or numeric as a
  text input), pre-filling `answers.get(current_id)`, and Back (hidden at idx 0) / Next (or
  "Finish" on the last item) buttons.
- **POST:** writes `answers[item_ids[idx]] = request.form.get("answer", "")` (blank allowed —
  unanswered), then:
  - `action == "back"` → `idx = max(0, idx - 1)`, redirect to the wizard.
  - `action == "next"` and not last → `idx += 1`, redirect to the wizard.
  - last item (finish) → load curriculum, `aid = store.save_attempt(student_id, course_id,
    answers, curriculum)`, clear `session["attempt"]`, redirect to `/attempts/<aid>`.

`save_attempt` already runs `drop_blank_responses` → `evaluate` → `build_path` and freezes the
snapshot, so blank/unanswered items are handled correctly and the DB is touched only on
completion. Cookie size: ~68 short `id:answer` pairs (~1–2 KB), well under the limit.

## Course handling

`engine/web.py` exposes `list_courses() -> list[str]` scanning `curriculum/` for directories
that contain `course.yaml` and are not `_template`. Today that yields `["grade5_math"]`. The
"Start test" control carries `course_id`, so the flow already supports multiple courses; the
curriculum is loaded per request via `load_course(...)` with the standard `schemas`/
`methodology`/`standards` dirs.

## Session secret

`create_app()` sets `app.secret_key` from `COURSE_EVAL_SECRET`; if unset, it reads
`var/secret_key`, creating it with `secrets.token_hex(32)` on first run (git-ignored, stable
across restarts so in-progress tests survive a restart). Tests pass an explicit secret via the
app config.

## Testing (`tests/test_web.py`, Flask `test_client`, temp DB + temp secret)

- Home `GET /` returns 200 and lists existing students; `POST /students` with a name creates
  one and redirects; empty name is rejected (no student created).
- `GET /students/<id>` shows the student and their history; unknown id → 404.
- **Full wizard run:** start the test, then POST `action=next` with an answer for each item in
  order; the final POST saves an attempt and redirects to `/attempts/<aid>`; `GET` that page
  returns the report HTML containing `"Learning Report for <name>"`. Assert exactly one attempt
  now exists for the student (`store.list_attempts`).
- **Navigation:** answering then `action=back` returns to the prior question with the earlier
  answer pre-filled; re-entering with `?start=1` resets to question 1.
- `GET /attempts/<unknown>` → 404.
- The engine/store test suites remain Flask-free (Flask imported only in `engine/web.py`).
- Run via `uv run pytest`.

## Risks / mitigations

- **Long diagnostic set as a wizard (~68 items)** — the progress bar + Back/Next make it
  navigable; blank answers are allowed so a child can skip and finish.
- **Cookie tampering** — signed by the secret key; there is no auth/authorization model here
  (a self-hosted family tool), and a tampered in-progress cookie only affects that session's
  own attempt, which is scored transparently.
- **Dev server only** — adequate for self-hosted single-family use; a note in the README points
  at a production WSGI server (e.g. gunicorn) as out-of-scope future work.
- **Concurrent writes** — low for single-family use; SQLite defaults suffice. WAL/busy-timeout
  is a documented future enhancement (carried over from the persistence-foundation review).
