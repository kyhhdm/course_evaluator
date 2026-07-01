# Per-Question Answer Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a per-question answer review (student's answer vs. correct, right/wrong, skill, explanation) to the web app — frozen into new attempts and recomputed for legacy ones.

**Architecture:** A pure `engine/review.py::build_review(curriculum, responses)` reuses `paper.ordered_groups` for deterministic diagnostic grouping. `store.save_attempt` freezes the review into snapshot v2; a new web route renders it (or recomputes for v1 attempts). An optional `nav_html` on the report renderer adds an "Answer review" link to the report page without touching the PDF.

**Tech Stack:** Python ≥3.10, Flask, jinja2, stdlib sqlite3, pytest. Package management via `uv`. No new dependency.

## Global Constraints

- Python `>=3.10`. Manage packages with `uv`; run tests with `uv run pytest`. No new dependency.
- `build_review` is pure/deterministic (framework-free), reusing `engine.paper.ordered_groups` (diagnostic-only, strand→point→item-bank order) and `engine.score.is_correct`. No `set` iteration in output.
- Review entry per question: `id`, `prompt`, `type`, `student_answer`, `student_answer_text`, `correct_answer`, `correct_answer_text`, `is_correct` (bool), `status` (`"answered"`|`"skipped"`), `feedback` (item's `distractor_feedback` for the *chosen wrong* option, else `""`). Per point group: `title`, `correct_count`, `total`, `questions`. Per strand: `strand`, `points`.
- Freeze at save: `snapshot["review"] = build_review(curriculum, clean)`, `snapshot["version"] = 2`. Legacy (v1) attempts recompute from `responses` + current curriculum.
- Report PDF stays byte-for-byte unchanged: `nav_html` defaults to `""`; only the web report route supplies it. `nav_html` is built from trusted literal paths in `engine/web.py` (never user input), so `| safe` is acceptable.
- No change to scoring, bands, path-ordering, coverage, the item bank, or the existing report content/layout. Templates autoescaped (except the trusted `nav_html`).

## File Structure

- Create `engine/review.py` — `build_review`.
- Modify `engine/store.py` — freeze review in `save_attempt`; `render_attempt_html` gains `nav_html` pass-through.
- Modify `engine/paper.py` (`render_parent_view`) + `templates/report.html.j2` — optional `nav_html`.
- Modify `engine/web.py` — review route + "Answer review" link on the report route.
- Create `templates/web/review.html`.
- Create `tests/test_review.py`; extend `tests/test_store.py`, `tests/test_paper.py`, `tests/test_web.py`.

---

### Task 1: `engine/review.py` — the pure review builder

**Files:**
- Create: `engine/review.py`
- Test: `tests/test_review.py`

**Interfaces:**
- Consumes: `engine.paper.ordered_groups`, `engine.score.is_correct`, `engine.models`.
- Produces: `build_review(curriculum: Curriculum, responses: dict) -> list[dict]` (shape per Global Constraints).

- [ ] **Step 1: Write the failing test**

Create `tests/test_review.py`:

```python
from engine.models import Band, Curriculum, Item, KnowledgePoint
from engine.review import build_review


def _curriculum():
    points = {"a": KnowledgePoint("a", "Fractions", "Equivalent fractions", "d", (), ())}
    items = {
        "Q1": Item("Q1", ("a",), 1, "mcq", "Which equals 1/2?", "B",
                   {"A": "one third", "B": "two quarters"}, {"A": "Halve it."}),
        "Q2": Item("Q2", ("a",), 1, "mcq", "Pick the true one", "A",
                   {"A": "right", "B": "wrong"}, {"B": "B is wrong because reasons."}),
        "Q3": Item("Q3", ("a",), 2, "numeric", "2 + 2 = ?", "4", {}, {}),
        "Q4": Item("Q4", ("a",), 1, "mcq", "Skipped one", "A", {"A": "x", "B": "y"}, {}),
    }
    return Curriculum(points=points, items=items, bands=(Band("Secure", 0.8),), standards={})


def test_build_review_groups_marks_and_explains():
    # Q1 correct; Q2 wrong (has feedback); Q3 wrong numeric; Q4 skipped (absent)
    review = build_review(_curriculum(), {"Q1": "B", "Q2": "B", "Q3": "5"})
    assert len(review) == 1 and review[0]["strand"] == "Fractions"
    pg = review[0]["points"][0]
    assert pg["title"] == "Equivalent fractions"
    assert pg["total"] == 4 and pg["correct_count"] == 1
    assert [q["id"] for q in pg["questions"]] == ["Q1", "Q2", "Q3", "Q4"]  # deterministic order
    q = {e["id"]: e for e in pg["questions"]}
    assert q["Q1"]["is_correct"] and q["Q1"]["student_answer_text"] == "two quarters"
    assert q["Q1"]["feedback"] == ""                                    # no feedback when correct
    assert not q["Q2"]["is_correct"] and q["Q2"]["feedback"] == "B is wrong because reasons."
    assert not q["Q3"]["is_correct"] and q["Q3"]["status"] == "answered"
    assert q["Q3"]["correct_answer_text"] == "4"
    assert q["Q4"]["status"] == "skipped" and not q["Q4"]["is_correct"]
    assert q["Q4"]["student_answer"] == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_review.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engine.review'`.

- [ ] **Step 3: Create `engine/review.py`**

```python
from __future__ import annotations

from engine.models import Curriculum
from engine.paper import ordered_groups
from engine.score import is_correct


def _is_blank(resp) -> bool:
    return resp is None or str(resp).strip() == ""


def build_review(curriculum: Curriculum, responses: dict) -> list[dict]:
    review: list[dict] = []
    for group in ordered_groups(curriculum):
        point_groups = []
        for pg in group["points"]:
            point = pg["point"]
            questions = []
            correct_count = 0
            for item in pg["items"]:
                resp = responses.get(item.id)
                skipped = _is_blank(resp)
                ok = is_correct(item, resp) if not skipped else False
                if ok:
                    correct_count += 1
                if item.type == "mcq":
                    student_text = "" if skipped else item.options.get(str(resp), "")
                    correct_text = item.options.get(item.answer, "")
                else:
                    student_text = "" if skipped else str(resp)
                    correct_text = item.answer
                feedback = ""
                if not ok and not skipped:
                    feedback = item.distractor_feedback.get(str(resp), "")
                questions.append({
                    "id": item.id,
                    "prompt": item.prompt,
                    "type": item.type,
                    "student_answer": "" if skipped else str(resp),
                    "student_answer_text": student_text,
                    "correct_answer": item.answer,
                    "correct_answer_text": correct_text,
                    "is_correct": ok,
                    "status": "skipped" if skipped else "answered",
                    "feedback": feedback,
                })
            point_groups.append({
                "title": point.title,
                "correct_count": correct_count,
                "total": len(questions),
                "questions": questions,
            })
        review.append({"strand": group["strand"], "points": point_groups})
    return review
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_review.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/review.py tests/test_review.py
git commit -m "feat(review): per-question answer-review builder"
```

---

### Task 2: Freeze the review into the attempt snapshot (v2)

**Files:**
- Modify: `engine/store.py` (`save_attempt`)
- Test: `tests/test_store.py`

**Interfaces:**
- Consumes: `engine.review.build_review` (Task 1).
- Produces: `save_attempt` stores `snapshot["review"]` and `snapshot["version"] == 2`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_store.py`:

```python
def test_save_attempt_freezes_review_v2(tmp_path):
    db = _db(tmp_path)
    sid = store.create_student("Maya", db_path=db)
    responses = load_yaml(f"{CURRICULUM}/sample_responses.yaml")["responses"]
    aid = store.save_attempt(sid, "grade5_math", responses, _grade5(), db_path=db)
    snap = store.get_attempt(aid, db_path=db)["snapshot"]
    assert snap["version"] == 2
    assert isinstance(snap["review"], list) and snap["review"]
    assert snap["review"][0]["strand"]
    q = snap["review"][0]["points"][0]["questions"][0]
    assert {"id", "prompt", "is_correct", "status", "correct_answer"} <= set(q)
```

- [ ] **Step 2: Update the existing version assertion**

In `tests/test_store.py`, the existing `test_save_and_get_attempt_roundtrips_with_snapshot` asserts the old version. Change line 43 from:

```python
    assert snap["version"] == 1                                 # snapshot schema version stamped
```

to:

```python
    assert snap["version"] == 2                                 # snapshot schema version stamped
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_store.py::test_save_attempt_freezes_review_v2 -v`
Expected: FAIL — `KeyError: 'review'` (snapshot has no review yet; version is still 1).

- [ ] **Step 4: Freeze the review in `save_attempt`**

In `engine/store.py`, add the lazy import alongside the others inside `save_attempt`:

```python
    from engine.review import build_review
```

and replace the `snapshot = {...}` block with:

```python
        snapshot = {
            "version": 2,  # v2 adds the frozen per-question review
            "parent_view": dataclasses.asdict(view),
            "student_plan": student_plan,
            "review": build_review(curriculum, clean),
        }
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_store.py -v`
Expected: PASS (the new freeze test plus the updated round-trip test).

- [ ] **Step 6: Commit**

```bash
git add engine/store.py tests/test_store.py
git commit -m "feat(store): freeze per-question review into snapshot v2"
```

---

### Task 3: Optional `nav_html` on the report renderer (no PDF impact)

**Files:**
- Modify: `engine/paper.py` (`render_parent_view`)
- Modify: `templates/report.html.j2`
- Modify: `engine/store.py` (`render_attempt_html`)
- Test: `tests/test_paper.py`

**Interfaces:**
- Produces: `render_parent_view(view, templates_dir, nav_html: str = "") -> str`; `render_attempt_html(attempt, templates_dir="templates", nav_html: str = "") -> str`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_paper.py`:

```python
def test_render_parent_view_injects_nav_html_and_defaults_empty():
    from engine.paper import render_parent_view
    from engine.report_view import build_parent_view
    c = _curriculum()
    pa = PointResult("a", 0.9, "Secure", "scored", 2)
    strand = StrandResult("Fractions", "Secure", 0.9, "a", [pa])
    result = EvaluationResult([strand], {"a": pa}, set())
    view = build_parent_view(c, result, [], "Sam")
    assert "NAVMARK" in render_parent_view(view, TEMPLATES, nav_html="<p>NAVMARK</p>")
    assert "NAVMARK" not in render_parent_view(view, TEMPLATES)   # default is empty
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_paper.py::test_render_parent_view_injects_nav_html_and_defaults_empty -v`
Expected: FAIL — `render_parent_view` takes no `nav_html` (TypeError) / the template doesn't render it.

- [ ] **Step 3: Add `nav_html` to the renderer and template**

In `engine/paper.py`, replace `render_parent_view`:

```python
def render_parent_view(view, templates_dir: str, nav_html: str = "") -> str:
    tmpl = _env(templates_dir).get_template("report.html.j2")
    return tmpl.render(view=view, nav_html=nav_html)
```

In `templates/report.html.j2`, immediately after the `<body class="report">` line (line 10), add:

```html
{{ nav_html | safe }}
```

In `engine/store.py`, replace `render_attempt_html`:

```python
def render_attempt_html(attempt: dict, templates_dir: str = "templates", nav_html: str = "") -> str:
    from engine.paper import render_parent_view

    return render_parent_view(attempt["snapshot"]["parent_view"], templates_dir, nav_html)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_paper.py tests/test_store.py -v`
Expected: PASS — the new nav test plus all existing report-html tests (`render_report_html` calls `render_parent_view(view, templates_dir)`, so `nav_html` defaults to `""` and output is unchanged).

- [ ] **Step 5: Commit**

```bash
git add engine/paper.py templates/report.html.j2 engine/store.py tests/test_paper.py
git commit -m "feat(report): optional nav_html injection point (web-only; PDF unchanged)"
```

---

### Task 4: Web review route + page + report-page link

**Files:**
- Modify: `engine/web.py` (add `attempt_review` route; add `nav_html` to the `attempt` route)
- Create: `templates/web/review.html`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `store.get_attempt`, `store.render_attempt_html` (with `nav_html`), `engine.review.build_review`, `_load`, `_find_student`, `list_courses`.
- Produces: route `GET /attempts/<int:attempt_id>/review`; the report route now injects an "Answer review" link.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_web.py`:

```python
def test_answer_review_page_and_report_link(client):
    from engine import store
    from engine.loader import load_course, load_yaml

    sid = store.create_student("Leo")
    c = load_course("curriculum/grade5_math", "schemas", "methodology", "standards")
    resp = load_yaml("curriculum/grade5_math/sample_responses.yaml")["responses"]
    aid = store.save_attempt(sid, "grade5_math", resp, c)

    review = client.get(f"/attempts/{aid}/review")
    assert review.status_code == 200
    assert b"Answer review" in review.data
    assert ("✓".encode() in review.data) or ("✗".encode() in review.data)  # a ✓ or ✗
    report = client.get(f"/attempts/{aid}")
    assert f"/attempts/{aid}/review".encode() in report.data                          # link on report


def test_answer_review_legacy_v1_recomputes(client):
    import json
    import os
    import sqlite3
    from engine import store
    from engine.loader import load_course, load_yaml

    sid = store.create_student("Leo")
    c = load_course("curriculum/grade5_math", "schemas", "methodology", "standards")
    resp = load_yaml("curriculum/grade5_math/sample_responses.yaml")["responses"]
    aid = store.save_attempt(sid, "grade5_math", resp, c)

    # Simulate a legacy v1 snapshot with no frozen review.
    snap = store.get_attempt(aid)["snapshot"]
    snap.pop("review", None)
    snap["version"] = 1
    conn = sqlite3.connect(os.environ["COURSE_EVAL_DB"])
    conn.execute("UPDATE attempts SET snapshot_json = ? WHERE id = ?", (json.dumps(snap), aid))
    conn.commit()
    conn.close()

    r = client.get(f"/attempts/{aid}/review")
    assert r.status_code == 200 and b"Answer review" in r.data   # rebuilt via recompute


def test_unknown_attempt_review_404(client):
    assert client.get("/attempts/999/review").status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_web.py::test_answer_review_page_and_report_link -v`
Expected: FAIL — `/attempts/<id>/review` has no route (404), so `"Answer review"` is absent.

- [ ] **Step 3: Add the review route and the report-page link**

In `engine/web.py`, inside `create_app`, replace the existing `attempt` route with the version that injects nav, and add the review route after it:

```python
    @app.get("/attempts/<int:attempt_id>")
    def attempt(attempt_id):
        a = store.get_attempt(attempt_id)
        if a is None:
            abort(404)
        nav = (
            f'<p><a href="/students/{a["student_id"]}">&larr; Student</a> &middot; '
            f'<a href="/attempts/{attempt_id}/review">Answer review</a></p>'
        )
        return store.render_attempt_html(a, nav_html=nav)

    @app.get("/attempts/<int:attempt_id>/review")
    def attempt_review(attempt_id):
        a = store.get_attempt(attempt_id)
        if a is None:
            abort(404)
        review = a["snapshot"].get("review")
        if review is None:  # legacy v1 attempt: recompute from stored responses
            if a["course_id"] not in list_courses():
                abort(404)
            from engine.review import build_review

            review = build_review(_load(a["course_id"]), a["responses"])
        student = _find_student(a["student_id"])
        return render_template("review.html", student=student, attempt=a, review=review)
```

- [ ] **Step 4: Create the review template**

`templates/web/review.html` — use the literal `✓` and `✗` characters (the tests assert their UTF-8 bytes in the response):

```html
{% extends "base.html" %}
{% block title %}Answer review{% endblock %}
{% block body %}
<p><a href="/attempts/{{ attempt.id }}">&larr; Back to report</a> &middot; <a href="/students/{{ student.id }}">{{ student.name }}</a></p>
<h1>Answer review — {{ student.name }}</h1>
{% for strand in review %}
<h2>{{ strand.strand }}</h2>
{% for pg in strand.points %}
<h3>{{ pg.title }} — {{ pg.correct_count }} of {{ pg.total }} correct</h3>
{% for q in pg.questions %}
<div class="q" style="margin: .6rem 0; padding-left: .6rem; border-left: 3px solid #ccc;">
<p><strong>{{ q.prompt }}</strong></p>
{% if q.status == "skipped" %}
<p>Skipped. Correct answer: {{ q.correct_answer }}{% if q.correct_answer_text %} ({{ q.correct_answer_text }}){% endif %}</p>
{% elif q.is_correct %}
<p>✓ Your answer: {{ q.student_answer }}{% if q.student_answer_text %} ({{ q.student_answer_text }}){% endif %}</p>
{% else %}
<p>✗ Your answer: {{ q.student_answer }}{% if q.student_answer_text %} ({{ q.student_answer_text }}){% endif %}</p>
<p>Correct answer: {{ q.correct_answer }}{% if q.correct_answer_text %} ({{ q.correct_answer_text }}){% endif %}</p>
{% if q.feedback %}<p><em>{{ q.feedback }}</em></p>{% endif %}
{% endif %}
</div>
{% endfor %}
{% endfor %}
{% endfor %}
{% endblock %}
```

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -q`
Expected: PASS (entire suite green, including the review page, the legacy recompute, and the report-page link).

- [ ] **Step 6: Commit**

```bash
git add engine/web.py templates/web/review.html tests/test_web.py
git commit -m "feat(web): per-question answer-review page + link on the report"
```

---

## Self-Review

**Spec coverage:**
- `engine/review.py::build_review` (pure, ordered_groups + is_correct, entry/group shape) → Task 1. ✓
- Freeze at save (snapshot v2 + review) → Task 2 (also updates the old version assertion). ✓
- Legacy v1 recompute → Task 4 (review route fallback). ✓
- Web page `GET /attempts/<id>/review` + `templates/web/review.html` (grouped, ✓/✗/skipped, feedback) → Task 4. ✓
- "Answer review" link on the report page via `nav_html`, PDF unchanged → Task 3 (mechanism) + Task 4 (link). ✓
- feedback only for the chosen wrong option; status skipped for blanks → Task 1. ✓
- Determinism (ordered_groups), autoescape (except trusted nav_html) → Tasks 1, 3, 4. ✓
- No new dependency; no scoring/bands/report-content change → honored. ✓

**Placeholder scan:** No TBD/TODO; every code/test/template step shows full content and exact commands. (Task 4 Step 4 explicitly resolves the ✓/✗ to literal characters to match the test bytes.) ✓

**Type consistency:** `build_review(curriculum, responses) -> list[dict]` defined in Task 1; consumed in Task 2 (`save_attempt`) and Task 4 (recompute). Entry keys (`is_correct`, `status`, `correct_answer`, `student_answer`, `feedback`, …) and group keys (`strand`, `points`, `title`, `correct_count`, `total`, `questions`) are identical between Task 1's builder, Task 2's assertions, and Task 4's template. `render_parent_view(view, templates_dir, nav_html="")` (Task 3) is called by `render_report_html` (unchanged 2-arg call) and `render_attempt_html` (Task 3, 3-arg) and the web report route (Task 4). `snapshot["version"] == 2` / `snapshot["review"]` consistent between Task 2 (write) and Task 4 (read). ✓
