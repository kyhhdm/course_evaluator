# Richer Parent Report + Focused Student Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the parent report a per-knowledge-point breakdown (grouped by band, including "Not assessed"), a strengths section, and an unassessed-skills note, and cap the student plan to its top 5 steps — all from a single shared view builder so the markdown and PDF renderers don't duplicate logic.

**Architecture:** A new pure builder `engine/report_view.py` derives a `ParentReportView` from the existing `Curriculum`/`EvaluationResult`/path. Both `render_parent` (markdown) and `render_report_html` (PDF) consume it, so their templates become dumb presenters. The student renderer slices the path to a named cap and passes a remainder count.

**Tech Stack:** Python ≥3.10, jinja2, pyyaml, jsonschema, weasyprint, pytest. Package management via `uv`.

## Global Constraints

- Python `>=3.10`. Manage all packages with `uv`; run tests with `uv run pytest`. No new dependencies.
- **Determinism is mandatory.** All point lists are in knowledge-map order (the order `StrandResult.point_results` already arrives in); strand order is `result.strands` order. No `set` iteration may reach output.
- The top band ("Secure") is always referenced via `curriculum.bands[0].name`, never a hard-coded string. The builder targets the default three-band model and asserts the three default band names; a custom band set is a documented known limitation.
- No change to scoring, bands, path-ordering, coverage, or the item bank. `build_path` keeps returning the full ordered path.
- Audience split: per-point detail + strengths + unassessed go to the **parent** report (markdown + PDF); the **student** report gets only the plan cap.
- A per-strand band group line renders only when its list is non-empty.
- Markdown env (`engine/report.py` `_env`) stays `autoescape=False`; HTML env (`engine/paper.py` `_env`) stays `autoescape=True`. Do not change either.

## File Structure

- Create `engine/report_view.py` — `ParentReportView`/`StrandGroup`/`Strengths` dataclasses + `build_parent_view`.
- Modify `engine/report.py` — `render_parent` consumes the view; `render_student` caps the plan.
- Modify `engine/paper.py` — `render_report_html` consumes the view.
- Modify `templates/report_parent.md.j2`, `templates/report.html.j2`, `templates/report_student.md.j2`.
- Create `tests/test_report_view.py`; extend `tests/test_report.py`, `tests/test_paper.py`.

---

### Task 1: `engine/report_view.py` — the shared view builder

**Files:**
- Create: `engine/report_view.py`
- Test: `tests/test_report_view.py`

**Interfaces:**
- Consumes: `engine.models` (`Curriculum`, `EvaluationResult`, `StrandResult`, `PointResult`, `PathStep`).
- Produces:
  - `StrandGroup(strand: str, band: str | None, secure: list[str], developing: list[str], not_yet: list[str], not_assessed: list[str])`
  - `Strengths(strong_strands: list[str], highlight_points: list[str])`
  - `ParentReportView(student_name: str, strand_groups: list[StrandGroup], strengths: Strengths, secure_skill_count: int, assessed_skill_count: int, unassessed_skill_count: int, secure_strand_count: int, total_strand_count: int, focus: list[PathStep])`
  - `build_parent_view(curriculum: Curriculum, result: EvaluationResult, path: list[PathStep], student_name: str = "Student") -> ParentReportView`

- [ ] **Step 1: Write the failing test**

Create `tests/test_report_view.py`:

```python
from engine.models import (
    Band, Curriculum, EvaluationResult, KnowledgePoint, PointResult, StrandResult,
)
from engine.report_view import build_parent_view


def _curriculum():
    points = {
        "p1": KnowledgePoint("p1", "Fractions", "Equivalent fractions", "d", (), ()),
        "p2": KnowledgePoint("p2", "Fractions", "Add unlike", "d", (), ()),
        "p3": KnowledgePoint("p3", "Fractions", "Divide fractions", "d", (), ()),
        "p4": KnowledgePoint("p4", "Geometry", "Coordinate system", "d", (), ()),
        "p5": KnowledgePoint("p5", "Geometry", "Classify figures", "d", (), ()),
    }
    bands = (Band("Secure", 0.8), Band("Developing", 0.5), Band("Not yet", 0.0))
    return Curriculum(points=points, items={}, bands=bands, standards={})


def _result():
    pr1 = PointResult("p1", 0.9, "Secure", "scored", 2)
    pr2 = PointResult("p2", 0.6, "Developing", "scored", 2)
    pr3 = PointResult("p3", 0.3, "Not yet", "scored", 2)
    pr4 = PointResult("p4", 0.95, "Secure", "scored", 2)
    pr5 = PointResult("p5", None, None, "insufficient_evidence", 1)
    frac = StrandResult("Fractions", "Developing", 0.6, "p3", [pr1, pr2, pr3])
    geo = StrandResult("Geometry", "Secure", 0.95, "p4", [pr4, pr5])
    return EvaluationResult(
        [frac, geo], {"p1": pr1, "p2": pr2, "p3": pr3, "p4": pr4, "p5": pr5}, set()
    )


def test_groups_points_by_band_and_marks_unassessed():
    view = build_parent_view(_curriculum(), _result(), [], "Maya")
    frac = view.strand_groups[0]
    assert frac.strand == "Fractions"
    assert frac.secure == ["Equivalent fractions"]
    assert frac.developing == ["Add unlike"]
    assert frac.not_yet == ["Divide fractions"]
    assert frac.not_assessed == []
    geo = view.strand_groups[1]
    assert geo.secure == ["Coordinate system"]
    assert geo.not_assessed == ["Classify figures"]


def test_counts_and_strengths():
    view = build_parent_view(_curriculum(), _result(), [], "Maya")
    assert view.secure_skill_count == 2          # p1, p4
    assert view.assessed_skill_count == 4        # p1..p4
    assert view.unassessed_skill_count == 1      # p5
    assert view.secure_strand_count == 1         # Geometry (band Secure)
    assert view.total_strand_count == 2
    # strong strands are those whose band == top band name, in result order
    assert view.strengths.strong_strands == ["Geometry"]
    # highlights are up to 3 secure point titles in knowledge-map order
    assert view.strengths.highlight_points == ["Equivalent fractions", "Coordinate system"]


def test_focus_is_first_three_path_steps():
    from engine.models import PathStep
    path = [PathStep(f"x{i}", f"Step {i}", []) for i in range(5)]
    view = build_parent_view(_curriculum(), _result(), path, "Maya")
    assert [s.title for s in view.focus] == ["Step 0", "Step 1", "Step 2"]
    assert view.student_name == "Maya"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_report_view.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engine.report_view'`.

- [ ] **Step 3: Write the implementation**

Create `engine/report_view.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field

from engine.models import Curriculum, EvaluationResult, PathStep


@dataclass
class StrandGroup:
    strand: str
    band: str | None
    secure: list[str] = field(default_factory=list)
    developing: list[str] = field(default_factory=list)
    not_yet: list[str] = field(default_factory=list)
    not_assessed: list[str] = field(default_factory=list)


@dataclass
class Strengths:
    strong_strands: list[str] = field(default_factory=list)
    highlight_points: list[str] = field(default_factory=list)


@dataclass
class ParentReportView:
    student_name: str
    strand_groups: list[StrandGroup]
    strengths: Strengths
    secure_skill_count: int
    assessed_skill_count: int
    unassessed_skill_count: int
    secure_strand_count: int
    total_strand_count: int
    focus: list[PathStep]


def build_parent_view(
    curriculum: Curriculum,
    result: EvaluationResult,
    path: list[PathStep],
    student_name: str = "Student",
) -> ParentReportView:
    bands = curriculum.bands
    assert len(bands) == 3, "report_view targets the default three-band model"
    secure_name, developing_name, not_yet_name = (bands[0].name, bands[1].name, bands[2].name)

    strand_groups: list[StrandGroup] = []
    secure_skill_count = assessed_skill_count = unassessed_skill_count = 0
    highlight_points: list[str] = []

    for sr in result.strands:
        group = StrandGroup(strand=sr.strand, band=sr.band)
        for pr in sr.point_results:
            title = curriculum.points[pr.point_id].title
            if pr.status == "insufficient_evidence":
                group.not_assessed.append(title)
                unassessed_skill_count += 1
                continue
            assessed_skill_count += 1
            if pr.band == secure_name:
                group.secure.append(title)
                secure_skill_count += 1
                highlight_points.append(title)
            elif pr.band == developing_name:
                group.developing.append(title)
            else:
                group.not_yet.append(title)
        strand_groups.append(group)

    strong_strands = [sr.strand for sr in result.strands if sr.band == secure_name]
    strengths = Strengths(strong_strands=strong_strands, highlight_points=highlight_points[:3])

    return ParentReportView(
        student_name=student_name,
        strand_groups=strand_groups,
        strengths=strengths,
        secure_skill_count=secure_skill_count,
        assessed_skill_count=assessed_skill_count,
        unassessed_skill_count=unassessed_skill_count,
        secure_strand_count=len(strong_strands),
        total_strand_count=len(result.strands),
        focus=path[:3],
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_report_view.py -v`
Expected: PASS (all four tests).

- [ ] **Step 5: Commit**

```bash
git add engine/report_view.py tests/test_report_view.py
git commit -m "feat(report): shared ParentReportView builder"
```

---

### Task 2: Parent markdown report consumes the view

**Files:**
- Modify: `engine/report.py` (`render_parent`)
- Modify: `templates/report_parent.md.j2`
- Test: `tests/test_report.py`

**Interfaces:**
- Consumes: `build_parent_view` (Task 1).
- Produces: `render_parent` renders the new layout (per-point groups, strengths, unassessed note, top-3 focus).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_report.py` (the existing `_setup()` builds a "Number" strand with `pa` Secure "Equivalent fractions" and `pb` "Not yet" "Add fractions"):

```python
def test_parent_report_shows_per_point_groups_and_strengths():
    curriculum, result, path = _setup()
    out = render_parent(curriculum, result, path, TEMPLATES, "Sam")
    assert "Secure:" in out and "Equivalent fractions" in out   # per-point group
    assert "Not yet:" in out and "Add fractions" in out
    assert "Strengths" in out
    assert "assessed skills are secure" in out                  # strengths sentence
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_report.py::test_parent_report_shows_per_point_groups_and_strengths -v`
Expected: FAIL — current template has no "Secure:" group line or "Strengths" section.

- [ ] **Step 3: Rewrite the template**

Replace the entire contents of `templates/report_parent.md.j2` with:

```jinja
# Learning Report for {{ view.student_name }}

## Where {{ view.student_name }} stands

{% for g in view.strand_groups %}
**{{ g.strand }}**: {{ g.band or "Not enough evidence yet" }}
{% if g.secure %}
- Secure: {{ g.secure | join("; ") }}
{% endif %}
{% if g.developing %}
- Developing: {{ g.developing | join("; ") }}
{% endif %}
{% if g.not_yet %}
- Not yet: {{ g.not_yet | join("; ") }}
{% endif %}
{% if g.not_assessed %}
- Not assessed: {{ g.not_assessed | join("; ") }} (too few answers)
{% endif %}
{% endfor %}

## What this means

{{ view.student_name }} is Secure in {{ view.secure_strand_count }} of {{ view.total_strand_count }} area(s).
{% if view.unassessed_skill_count %}{{ view.unassessed_skill_count }} skill(s) couldn't be assessed — too few answers there.{% endif %}

## Strengths

{% if view.strengths.strong_strands %}Strongest in {{ view.strengths.strong_strands | join(" and ") }}. {% endif %}{{ view.secure_skill_count }} of {{ view.assessed_skill_count }} assessed skills are secure{% if view.strengths.highlight_points %}, including {{ view.strengths.highlight_points | join(", ") }}{% endif %}.

## Focus next

{% if view.focus %}
{% for step in view.focus %}
{{ loop.index }}. **{{ step.title }}**
{% endfor %}
{% else %}
Nothing specific to fix right now — keep practicing to stay sharp.
{% endif %}
```

- [ ] **Step 4: Rewrite `render_parent`**

In `engine/report.py`, replace the `render_parent` function body with:

```python
def render_parent(
    curriculum: Curriculum,
    result: EvaluationResult,
    path: list[PathStep],
    templates_dir: str,
    student_name: str = "Student",
) -> str:
    from engine.report_view import build_parent_view

    view = build_parent_view(curriculum, result, path, student_name)
    tmpl = _env(templates_dir).get_template("report_parent.md.j2")
    return tmpl.render(view=view)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_report.py tests/test_cli.py -v`
Expected: PASS — the new test plus the existing `test_parent_report_shows_strand_band_and_focus` (still finds "Sam"/"Number"/"Developing"/"Add fractions") and the CLI parent test (still finds "Learning Report for Sam" and "Number & Operations").

- [ ] **Step 6: Commit**

```bash
git add engine/report.py templates/report_parent.md.j2 tests/test_report.py
git commit -m "feat(report): parent markdown shows per-point groups, strengths, unassessed"
```

---

### Task 3: Parent PDF/HTML report consumes the view

**Files:**
- Modify: `engine/paper.py` (`render_report_html`)
- Modify: `templates/report.html.j2`
- Test: `tests/test_paper.py`

**Interfaces:**
- Consumes: `build_parent_view` (Task 1).
- Produces: `render_report_html` renders the same layout in HTML for the PDF.

- [ ] **Step 1: Write the failing test**

In `tests/test_paper.py`, find `test_report_html_shows_name_band_and_focus` and append a new test after it (reuse its inline fixture pattern — build a `Curriculum`, `EvaluationResult`, and path):

```python
def test_report_html_shows_per_point_groups_and_strengths():
    from engine.paper import render_report_html
    c = _curriculum()
    pa = PointResult("a", 0.9, "Secure", "scored", 2)
    pb = PointResult("b", 0.4, "Not yet", "scored", 2)
    strand = StrandResult("Fractions", "Developing", 0.65, "b", [pa, pb])
    result = EvaluationResult([strand], {"a": pa, "b": pb}, {"A1"})
    path = [PathStep("b", "Add fractions", ["B1"])]
    html = render_report_html(c, result, path, TEMPLATES, "Sam")
    assert "Secure:" in html and "Strengths" in html
    assert "assessed skills are secure" in html
```

Note: the existing `_curriculum()` in `tests/test_paper.py` defines point `a` titled "Equivalent fractions" and point `b` titled "Add fractions"; this test reuses those titles. If `_curriculum()` lacks a point `b`, add one: `"b": KnowledgePoint("b", "Fractions", "Add fractions", "d", (), ())` to that fixture.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_paper.py::test_report_html_shows_per_point_groups_and_strengths -v`
Expected: FAIL — current `report.html.j2` renders strand bands only, no "Secure:" group or "Strengths".

- [ ] **Step 3: Rewrite the template**

Replace the entire contents of `templates/report.html.j2` with:

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Learning Report</title>
<style>
{% include "print.css" %}
</style>
</head>
<body>
<h1>Learning Report for {{ view.student_name }}</h1>
<h2>Where {{ view.student_name }} stands</h2>
{% for g in view.strand_groups %}
<div class="strand">
<p><strong>{{ g.strand }}:</strong> {{ g.band or "Not enough evidence yet" }}</p>
<ul>
{% if g.secure %}
<li><strong>Secure:</strong> {{ g.secure | join("; ") }}</li>
{% endif %}
{% if g.developing %}
<li><strong>Developing:</strong> {{ g.developing | join("; ") }}</li>
{% endif %}
{% if g.not_yet %}
<li><strong>Not yet:</strong> {{ g.not_yet | join("; ") }}</li>
{% endif %}
{% if g.not_assessed %}
<li><strong>Not assessed:</strong> {{ g.not_assessed | join("; ") }} (too few answers)</li>
{% endif %}
</ul>
</div>
{% endfor %}
<h2>What this means</h2>
<p>{{ view.student_name }} is Secure in {{ view.secure_strand_count }} of {{ view.total_strand_count }} area(s).
{% if view.unassessed_skill_count %} {{ view.unassessed_skill_count }} skill(s) couldn't be assessed — too few answers there.{% endif %}</p>
<h2>Strengths</h2>
<p>{% if view.strengths.strong_strands %}Strongest in {{ view.strengths.strong_strands | join(" and ") }}. {% endif %}{{ view.secure_skill_count }} of {{ view.assessed_skill_count }} assessed skills are secure{% if view.strengths.highlight_points %}, including {{ view.strengths.highlight_points | join(", ") }}{% endif %}.</p>
<h2>Focus next</h2>
{% if view.focus %}
<ol>
{% for step in view.focus %}
<li><strong>{{ step.title }}</strong></li>
{% endfor %}
</ol>
{% else %}
<p>Nothing specific to fix right now — keep practicing to stay sharp.</p>
{% endif %}
</body>
</html>
```

- [ ] **Step 4: Rewrite `render_report_html`**

In `engine/paper.py`, replace the `render_report_html` function body with:

```python
def render_report_html(
    curriculum: Curriculum,
    result: EvaluationResult,
    path: list[PathStep],
    templates_dir: str,
    student_name: str = "Student",
) -> str:
    from engine.report_view import build_parent_view

    view = build_parent_view(curriculum, result, path, student_name)
    tmpl = _env(templates_dir).get_template("report.html.j2")
    return tmpl.render(view=view)
```

(The `EvaluationResult` and `PathStep` imports already present in `engine/paper.py` cover the signature; keep them.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_paper.py -v`
Expected: PASS — the new test plus the existing `test_report_html_shows_name_band_and_focus` (still finds "Sam", "Fractions"/strand name, "Developing", "Add fractions").

- [ ] **Step 6: Commit**

```bash
git add engine/paper.py templates/report.html.j2 tests/test_paper.py
git commit -m "feat(report): parent PDF/HTML shows per-point groups, strengths, unassessed"
```

---

### Task 4: Student plan caps at 5 steps

**Files:**
- Modify: `engine/report.py` (`render_student`)
- Modify: `templates/report_student.md.j2`
- Test: `tests/test_report.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `render_student` shows at most `STUDENT_PLAN_STEPS` (= 5) steps and a "…and N more" note when the path is longer.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_report.py`:

```python
def test_student_plan_caps_at_five_steps_with_remainder_note():
    from engine.models import PathStep
    curriculum, result, _ = _setup()
    path = [PathStep(f"x{i}", f"Skill {i}", []) for i in range(8)]
    out = render_student(curriculum, result, path, TEMPLATES, "Sam")
    assert "Step 5" in out
    assert "Step 6" not in out                       # capped at 5
    assert "3 more" in out                           # 8 - 5 = 3 remainder note


def test_student_plan_no_remainder_note_when_within_cap():
    from engine.models import PathStep
    curriculum, result, _ = _setup()
    path = [PathStep(f"x{i}", f"Skill {i}", []) for i in range(3)]
    out = render_student(curriculum, result, path, TEMPLATES, "Sam")
    assert "Step 3" in out
    assert "more area" not in out                     # no remainder note
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_report.py::test_student_plan_caps_at_five_steps_with_remainder_note -v`
Expected: FAIL — current `render_student` renders all 8 steps (so "Step 6" is present and no remainder note exists).

- [ ] **Step 3: Update `render_student`**

In `engine/report.py`, add the module-level constant near the top (after imports):

```python
STUDENT_PLAN_STEPS = 5
```

Replace the `render_student` function body with:

```python
def render_student(
    curriculum: Curriculum,
    result: EvaluationResult,
    path: list[PathStep],
    templates_dir: str,
    student_name: str = "Student",
) -> str:
    shown = path[:STUDENT_PLAN_STEPS]
    remainder = max(0, len(path) - STUDENT_PLAN_STEPS)
    tmpl = _env(templates_dir).get_template("report_student.md.j2")
    return tmpl.render(
        name=student_name, strands=result.strands, path=shown,
        items=curriculum.items, remainder=remainder,
    )
```

- [ ] **Step 4: Add the remainder note to the template**

In `templates/report_student.md.j2`, replace the final `{% if path -%}` … `{% endif %}` block's closing so a remainder note follows the step loop. Replace the existing tail:

```jinja
{% for step in path %}
### Step {{ loop.index }}: {{ step.title }}

Practice these:
{% for item_id in step.practice_item_ids -%}
- {{ items[item_id].prompt }}
{% endfor -%}
{% if not step.practice_item_ids -%}
- (No extra practice items available yet for this skill.)
{% endif -%}
{% endfor %}
{% else -%}
Great work — no gaps to fix right now.
{% endif %}
```

with:

```jinja
{% for step in path %}
### Step {{ loop.index }}: {{ step.title }}

Practice these:
{% for item_id in step.practice_item_ids -%}
- {{ items[item_id].prompt }}
{% endfor -%}
{% if not step.practice_item_ids -%}
- (No extra practice items available yet for this skill.)
{% endif -%}
{% endfor %}
{% if remainder %}
…and {{ remainder }} more area(s) to work on after these.
{% endif %}
{% else -%}
Great work — no gaps to fix right now.
{% endif %}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_report.py tests/test_cli.py -v`
Expected: PASS — the two new tests plus existing student tests (`test_student_report_lists_steps_and_practice_prompt`, `test_reports_handle_empty_path`, and the CLI student test still find "Step 1").

- [ ] **Step 6: Run the full suite**

Run: `uv run pytest -q`
Expected: PASS (entire suite green).

- [ ] **Step 7: Commit**

```bash
git add engine/report.py templates/report_student.md.j2 tests/test_report.py
git commit -m "feat(report): cap student plan at 5 steps with remainder note"
```

---

## Self-Review

**Spec coverage:**
- `engine/report_view.py` + `build_parent_view` + dataclasses → Task 1. ✓
- Band→bucket mapping via `bands[0/1/2].name`, assert three-band model → Task 1. ✓
- Parent per-point groups (Secure/Developing/Not yet/Not assessed, non-empty only) → Tasks 2 (md) & 3 (html). ✓
- "What this means" with secure-strand count + unassessed note → Tasks 2 & 3. ✓
- Strengths sentence (strong strands + N/M secure + ≤3 highlights) → Tasks 2 & 3. ✓
- Top-3 focus unchanged → Task 1 (`focus=path[:3]`), rendered in Tasks 2 & 3. ✓
- Dedup: both renderers consume one builder → Tasks 2 & 3. ✓
- Student cap = 5 with remainder note; `build_path` unchanged → Task 4. ✓
- Determinism (knowledge-map order from `point_results`, strand order from `result.strands`) → Task 1. ✓
- No new deps; markdown/html env autoescape unchanged → honored in Tasks 2–3 (templates only; `_env` untouched). ✓

**Placeholder scan:** No TBD/TODO/vague steps; every code/test step shows full code and exact commands. ✓

**Type consistency:** `build_parent_view(curriculum, result, path, student_name="Student")` defined in Task 1 and called identically in Tasks 2 & 3. `ParentReportView`/`StrandGroup`/`Strengths` field names (`student_name`, `strand_groups`, `secure`/`developing`/`not_yet`/`not_assessed`, `strong_strands`, `highlight_points`, `secure_skill_count`, `assessed_skill_count`, `unassessed_skill_count`, `secure_strand_count`, `total_strand_count`, `focus`) match exactly between the Task 1 dataclasses, the Task 2 markdown template (`view.…`), and the Task 3 HTML template. `STUDENT_PLAN_STEPS` defined and used in Task 4. The `render_*` signatures match the existing call sites in `engine/cli.py` (unchanged). ✓
