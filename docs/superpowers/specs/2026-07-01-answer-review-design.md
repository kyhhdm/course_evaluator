# Per-Question Answer Review — Design

**Date:** 2026-07-01
**Status:** Approved, pending implementation plan
**Scope:** Add a per-question answer review to the web app: for a saved attempt, show every
diagnostic question with the student's answer, the correct answer, right/wrong, the skill it
tests, and an explanation for wrong answers. Builds on the merged persistence + web app.

## Goal

Let a parent see exactly what happened on each question — not just the skill-level bands the
report already shows. Frozen into the attempt at save time (faithful even if questions later
change), with a recompute fallback for attempts saved before this feature.

## Non-goals

- No change to scoring, bands, path-ordering, coverage, the item bank, or the existing report
  content/layout.
- No PDF of the review (web page only) and no new dependency.
- No editing of answers/attempts; review is read-only.

## What a review contains

Grouped by strand → knowledge point (the same deterministic order as the report), each
**question entry** has: `id`, `prompt`, `type`, the student's answer (`student_answer` letter/
value + `student_answer_text` = the MCQ option text), the correct answer (`correct_answer` +
`correct_answer_text`), `is_correct` (bool), `status` (`"answered"` | `"skipped"`), and
`feedback` (the item's `distractor_feedback` for the *chosen* wrong option, when present; else
`""`). Each point group carries a `title`, `correct_count`, and `total` for a mini-summary.

## Architecture

### Pure builder — `engine/review.py`
`build_review(curriculum, responses: dict) -> list[dict]`. Framework-free, deterministic,
no I/O. It iterates `engine.paper.ordered_groups(curriculum)` (diagnostic items only, in
strand→point→item-bank order) and builds, per strand:

```
[{"strand": str,
  "points": [{"title": str, "correct_count": int, "total": int,
              "questions": [{"id", "prompt", "type", "student_answer",
                             "student_answer_text", "correct_answer",
                             "correct_answer_text", "is_correct", "status",
                             "feedback"}]}]}]
```

Per item: `resp = responses.get(item.id)`; `status = "skipped"` if `resp` is None/blank else
`"answered"`; `is_correct = engine.score.is_correct(item, resp)` (a skipped item is not
correct); for MCQ, `*_text` come from `item.options.get(letter, "")`, for numeric the text
equals the value; `feedback = item.distractor_feedback.get(resp, "")` only when the answer is
wrong (empty otherwise). `correct_count` counts `is_correct` per point. Uses only existing
engine functions; adds no dependency.

### Freeze at save — `engine/store.py`
`save_attempt` adds `snapshot["review"] = build_review(curriculum, clean)` (the same
blank-dropped `clean` responses it already computes) and sets `snapshot["version"] = 2`. New
attempts carry the full frozen review. `responses_json`, `parent_view`, and `student_plan` are
unchanged.

### Legacy fallback + web route — `engine/web.py`
`GET /attempts/<int:attempt_id>/review`:
1. `a = store.get_attempt(attempt_id)`; `abort(404)` if None.
2. `review = a["snapshot"].get("review")`; if absent (v1 attempt), recompute:
   `review = build_review(_load(a["course_id"]), a["responses"])`. (If `_load` fails because
   the course no longer exists, `abort(404)`.)
3. Render `templates/web/review.html` with the student, the attempt, and `review`.

### "Answer review" link on the report page — no PDF impact
`GET /attempts/<id>` (the web report) adds a small top nav with an "Answer review" link and a
"Back to student" link. Mechanism: `engine.paper.render_parent_view(view, templates_dir,
nav_html: str = "")` gains an optional `nav_html`, and `report.html.j2` renders
`{{ nav_html | safe }}` immediately inside `<body class="report">`. `store.render_attempt_html`
gains a matching pass-through `nav_html=""` param. The CLI/PDF path (`render_report_html`)
passes nothing, so **the PDF report is byte-for-byte unchanged**; only the web route supplies
nav HTML. The nav HTML is built in `engine/web.py` from trusted literal paths (no user data),
so `| safe` is safe here.

## Web page (`templates/web/review.html`)

Extends `base.html`. Top links: "← Back to report" (`/attempts/<id>`) and "← Student"
(`/students/<student_id>`). Then per strand: a heading; per point: `title` + "N of M correct";
then each question as a block showing the prompt, the student's answer (with option text for
MCQ) marked ✓ (correct) / ✗ (wrong) / "skipped", the correct answer when the student was wrong
or skipped, and the feedback line when present. Autoescaped throughout.

## Testing

- **`tests/test_review.py`** — `build_review` on a small `Curriculum` fixture with four
  diagnostic items in one point: a correct MCQ (`is_correct` true, no feedback), a wrong MCQ
  whose chosen distractor has `distractor_feedback` (wrong + that exact feedback string), a
  wrong numeric, and a blank/absent item (`status == "skipped"`, not correct). Assert grouping
  (`strand`/`points`/`title`), `correct_count`/`total`, deterministic order, and the per-entry
  fields (`student_answer_text`, `correct_answer_text`).
- **`tests/test_store.py`** — after `save_attempt`, `get_attempt(...)["snapshot"]` has
  `version == 2` and a non-empty `review` list whose first strand matches the curriculum.
- **`tests/test_paper.py`** — `render_parent_view(view, TEMPLATES, nav_html="<p>hi</p>")`
  includes `hi`; the default (`nav_html=""`) output is unchanged (existing report tests pass).
- **`tests/test_web.py`** — `GET /attempts/<id>/review` after a real attempt renders question
  prompts plus a ✓ and a ✗ marker; a **legacy** attempt (saved, then its snapshot rewritten to
  drop the `review` key and reset `version` to 1 via a direct DB update in the test) still
  renders via recompute; the report page (`GET /attempts/<id>`) contains the "Answer review"
  link; `GET /attempts/<unknown>/review` → 404.
- Run via `uv run pytest`.

## Risks / mitigations

- **Snapshot growth** — the review adds ~68 small entries (~10–15 KB JSON) per attempt; fine
  for SQLite TEXT.
- **Legacy attempts after item changes** — recompute uses the current item bank; if a
  diagnostic item was removed, that question simply won't appear (the recompute iterates
  current diagnostic items). Acceptable and documented; new attempts are frozen and immune.
- **`nav_html | safe`** — only ever built from trusted literal paths in `engine/web.py`, never
  from user input; the report/PDF path passes `""`.
