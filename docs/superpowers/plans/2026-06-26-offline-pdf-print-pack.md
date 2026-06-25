# Offline PDF Print Pack + Round-Trip Report — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce printable PDFs (test paper, answer sheet, answer key) plus a blank fill-in responses file from the existing Grade-5 content, and render the evaluation report as a PDF, so a parent can run a diagnostic fully offline and still get the engine's mastery + learning-path report.

**Architecture:** Keep HTML rendering pure and testable (jinja2 only, already a dependency) in a new `engine/paper.py`, and confine the single PDF-conversion dependency (WeasyPrint) to a one-function seam in `engine/pdf.py`. New jinja2 HTML templates live alongside the existing markdown ones. The CLI gains additive `--paper`, `--pdf`, and `--out` flags; nothing existing changes behavior.

**Tech Stack:** Python ≥3.10, jinja2, pyyaml, jsonschema, WeasyPrint (new), pytest. Package management via `uv`.

## Global Constraints

- Python `>=3.10`. Manage all packages with `uv` — `uv add` for deps, `uv run` for commands. Never edit `pyproject.toml` deps by hand or call `pip`.
- **Determinism is mandatory.** Every list reaching output is ordered explicitly — knowledge-map order for strands/points (insertion-ordered dicts), item-bank order within a point, `sort` for option/feedback keys. No `set` iteration order may leak into output.
- WeasyPrint may be imported **only** in `engine/pdf.py`. All other modules stay PDF-dependency-free so their tests run without it.
- HTML-producing jinja2 environment uses `autoescape=True` (prompts may contain `<`, `&`). The existing markdown env in `engine/report.py` (autoescape=False) is untouched.
- The test paper must never reveal answers (no correct-option marker, no numeric answer printed).
- Each item appears exactly once in the print pack, assigned to its first knowledge point (`item.points[0]`).
- Existing CLI commands (`--responses`, `--coverage`, `--audience`) keep their current behavior and output.

## File Structure

- Create `engine/paper.py` — pure HTML/text renderers + ordering helpers + `drop_blank_responses`.
- Create `engine/pdf.py` — `html_to_pdf(html, out_path)`, the only WeasyPrint importer.
- Create `templates/print.css` — shared print stylesheet (included inline by each template).
- Create `templates/test_paper.html.j2`, `templates/answer_key.html.j2`, `templates/answer_sheet.html.j2`, `templates/report.html.j2`.
- Modify `engine/cli.py` — add `--paper`, `--pdf`, `--out` and their wiring.
- Modify `CLAUDE.md` — note WeasyPrint in the runtime-deps line.
- Modify `README.md` — document the offline workflow.
- Create tests: `tests/test_pdf.py`, `tests/test_paper.py`; extend `tests/test_cli.py`.

---

### Task 1: PDF conversion seam (`engine/pdf.py`) + WeasyPrint dependency

**Files:**
- Create: `engine/pdf.py`
- Test: `tests/test_pdf.py`
- Modify: `CLAUDE.md` (runtime-deps line)

**Interfaces:**
- Consumes: nothing.
- Produces: `html_to_pdf(html: str, out_path: str) -> None` — writes a PDF file from an HTML string.

- [ ] **Step 1: Add the dependency**

Run: `uv add weasyprint`
Expected: `pyproject.toml` gains `weasyprint` under dependencies; `uv.lock` updates; install succeeds.

- [ ] **Step 2: Write the failing test**

Create `tests/test_pdf.py`:

```python
from engine.pdf import html_to_pdf


def test_html_to_pdf_writes_nonempty_pdf(tmp_path):
    out = tmp_path / "out.pdf"
    html_to_pdf("<html><body><h1>Hello</h1></body></html>", str(out))
    assert out.exists()
    data = out.read_bytes()
    assert len(data) > 0
    assert data[:4] == b"%PDF"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_pdf.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engine.pdf'`.

- [ ] **Step 4: Write minimal implementation**

Create `engine/pdf.py`:

```python
from __future__ import annotations

from weasyprint import HTML


def html_to_pdf(html: str, out_path: str) -> None:
    """Render a self-contained HTML string to a PDF file at out_path.

    This is the ONLY module permitted to import WeasyPrint.
    """
    HTML(string=html).write_pdf(out_path)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_pdf.py -v`
Expected: PASS.

- [ ] **Step 6: Update CLAUDE.md deps line**

In `CLAUDE.md`, change the runtime-deps sentence to include WeasyPrint:

```
Runtime deps: `pyyaml`, `jsonschema`, `jinja2`, `weasyprint` (PDF rendering, confined to
`engine/pdf.py`). Dev: `pytest`. Python `>=3.10`. Keep dependencies limited to these — adding
one is a deliberate decision, not a default. Add deps with `uv add <pkg>`.
```

- [ ] **Step 7: Commit**

```bash
git add engine/pdf.py tests/test_pdf.py CLAUDE.md pyproject.toml uv.lock
git commit -m "feat(pdf): add WeasyPrint html_to_pdf seam"
```

---

### Task 2: Ordering helpers + test-paper HTML (`engine/paper.py`, `test_paper.html.j2`, `print.css`)

**Files:**
- Create: `engine/paper.py`
- Create: `templates/test_paper.html.j2`
- Create: `templates/print.css`
- Test: `tests/test_paper.py`

**Interfaces:**
- Consumes: `engine.models.Curriculum`, `Item`, `KnowledgePoint`.
- Produces:
  - `ordered_groups(curriculum: Curriculum) -> list[dict]` — `[{"strand": str, "points": [{"point": KnowledgePoint, "items": [Item]}]}]`, each item once, deterministic.
  - `ordered_items(curriculum: Curriculum) -> list[Item]` — flat version in the same order.
  - `render_paper_html(curriculum: Curriculum, templates_dir: str) -> str`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_paper.py`:

```python
from engine.models import Band, Curriculum, Item, KnowledgePoint
from engine.paper import ordered_groups, ordered_items, render_paper_html

TEMPLATES = "templates"


def _curriculum():
    points = {
        "a": KnowledgePoint("a", "Fractions", "Equivalent fractions", "d", (), ()),
        "b": KnowledgePoint("b", "Fractions", "Add fractions", "d", ("a",), ()),
    }
    items = {
        "A1": Item("A1", ("a",), 1, "mcq", "Which equals 1/2?", "B", {"A": "2/3", "B": "3/6"}, {}),
        "A2": Item("A2", ("a",), 2, "numeric", "2/5 = ?/20", "42", {}, {}),
        "B1": Item("B1", ("b",), 1, "numeric", "1/5 + 2/5 = ?/5", "3", {}, {}),
    }
    bands = (Band("Secure", 0.8), Band("Developing", 0.5), Band("Not yet", 0.0))
    return Curriculum(points=points, items=items, bands=bands, standards={})


def test_ordered_groups_groups_by_strand_each_item_once():
    groups = ordered_groups(_curriculum())
    assert [g["strand"] for g in groups] == ["Fractions"]
    flat = [it.id for it in ordered_items(_curriculum())]
    assert flat == ["A1", "A2", "B1"]


def test_paper_html_shows_prompts_and_options_but_no_answers():
    html = render_paper_html(_curriculum(), TEMPLATES)
    assert "Which equals 1/2?" in html      # prompt present
    assert "3/6" in html                      # mcq option text present
    assert "42" not in html                   # numeric answer NOT leaked
    assert "correct" not in html.lower()      # no correct-answer marker
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_paper.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engine.paper'`.

- [ ] **Step 3: Create the shared stylesheet**

Create `templates/print.css`:

```css
@page { size: A4; margin: 18mm 16mm; }
body { font-family: "DejaVu Sans", Arial, sans-serif; font-size: 12pt; color: #111; }
h1 { font-size: 18pt; margin: 0 0 12pt; }
h2 { font-size: 14pt; margin: 16pt 0 6pt; border-bottom: 1px solid #999; }
h3 { font-size: 12pt; margin: 10pt 0 4pt; color: #444; }
.item { margin: 0 0 10pt; page-break-inside: avoid; }
.prompt { margin: 0 0 4pt; }
.qid { font-weight: bold; }
.options { list-style: none; padding-left: 18pt; margin: 0; }
.options li { margin: 2pt 0; }
.answer-blank { margin: 4pt 0 0; color: #333; }
.answer { color: #064; }
.feedback { font-size: 10pt; color: #555; padding-left: 18pt; }
.answer-grid { width: 100%; border-collapse: collapse; }
.answer-grid th, .answer-grid td { border: 1px solid #999; padding: 6pt 8pt; text-align: left; }
.answer-grid td.blank { height: 18pt; }
```

- [ ] **Step 4: Create the test-paper template**

Create `templates/test_paper.html.j2` (note: NO point titles and NO answers, to avoid hinting):

```html
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Test Paper</title>
<style>
{% include "print.css" %}
</style>
</head>
<body>
<h1>{% if course %}{{ course.name }}{% else %}Diagnostic Test{% endif %} — Test Paper</h1>
<p>Name: ____________________________  Date: ______________</p>
{% for g in groups %}
<section class="strand">
<h2>{{ g.strand }}</h2>
{% for pg in g.points %}
{% for item in pg.items %}
<div class="item">
<p class="prompt"><span class="qid">{{ item.id }}.</span> {{ item.prompt }}</p>
{% if item.type == "mcq" %}
<ul class="options">
{% for key in item.options | sort %}
<li><strong>{{ key }}.</strong> {{ item.options[key] }}</li>
{% endfor %}
</ul>
{% else %}
<p class="answer-blank">Answer: ______________________</p>
{% endif %}
</div>
{% endfor %}
{% endfor %}
</section>
{% endfor %}
</body>
</html>
```

- [ ] **Step 5: Write the implementation**

Create `engine/paper.py`:

```python
from __future__ import annotations

from jinja2 import Environment, FileSystemLoader

from engine.models import Curriculum, EvaluationResult, Item, PathStep


def _env(templates_dir: str) -> Environment:
    return Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def ordered_groups(curriculum: Curriculum) -> list[dict]:
    """Group each item under its first knowledge point.

    Strands in knowledge-map order, points in knowledge-map order within a
    strand, items in item-bank order within a point. Each item appears once.
    """
    buckets: dict[str, list[Item]] = {pid: [] for pid in curriculum.points}
    for item in curriculum.items.values():  # item-bank (insertion) order
        if not item.points:
            continue
        primary = item.points[0]
        if primary in buckets:
            buckets[primary].append(item)
    groups: list[dict] = []
    for strand in curriculum.strands():
        point_groups = []
        for point in curriculum.points_in_strand(strand):
            if buckets[point.id]:
                point_groups.append({"point": point, "items": buckets[point.id]})
        if point_groups:
            groups.append({"strand": strand, "points": point_groups})
    return groups


def ordered_items(curriculum: Curriculum) -> list[Item]:
    items: list[Item] = []
    for g in ordered_groups(curriculum):
        for pg in g["points"]:
            items.extend(pg["items"])
    return items


def render_paper_html(curriculum: Curriculum, templates_dir: str) -> str:
    tmpl = _env(templates_dir).get_template("test_paper.html.j2")
    return tmpl.render(groups=ordered_groups(curriculum), course=curriculum.meta)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_paper.py -v`
Expected: PASS (both tests).

- [ ] **Step 7: Commit**

```bash
git add engine/paper.py templates/test_paper.html.j2 templates/print.css tests/test_paper.py
git commit -m "feat(paper): ordering helpers and test-paper HTML renderer"
```

---

### Task 3: Answer-key HTML (`render_answer_key_html`, `answer_key.html.j2`)

**Files:**
- Modify: `engine/paper.py`
- Create: `templates/answer_key.html.j2`
- Test: `tests/test_paper.py`

**Interfaces:**
- Consumes: `ordered_groups` (Task 2).
- Produces: `render_answer_key_html(curriculum: Curriculum, templates_dir: str) -> str`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_paper.py`:

```python
def test_answer_key_html_shows_answers_and_feedback():
    from engine.paper import render_answer_key_html
    c = _curriculum()
    c.items["A1"].distractor_feedback = {"A": "Scale numerator and denominator together."}
    html = render_answer_key_html(c, TEMPLATES)
    assert "Equivalent fractions" in html          # point title shown on the key
    assert "42" in html                             # numeric answer shown
    assert "Scale numerator" in html                # distractor feedback shown
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_paper.py::test_answer_key_html_shows_answers_and_feedback -v`
Expected: FAIL with `ImportError: cannot import name 'render_answer_key_html'`.

- [ ] **Step 3: Create the answer-key template**

Create `templates/answer_key.html.j2`:

```html
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Answer Key</title>
<style>
{% include "print.css" %}
</style>
</head>
<body>
<h1>{% if course %}{{ course.name }}{% else %}Diagnostic Test{% endif %} — Answer Key</h1>
{% for g in groups %}
<section class="strand">
<h2>{{ g.strand }}</h2>
{% for pg in g.points %}
<h3>{{ pg.point.title }}</h3>
{% for item in pg.items %}
<div class="item">
<p class="prompt"><span class="qid">{{ item.id }}.</span> {{ item.prompt }}</p>
<p class="answer"><strong>Answer:</strong> {{ item.answer }}{% if item.type == "mcq" and item.answer in item.options %} — {{ item.options[item.answer] }}{% endif %}</p>
{% if item.distractor_feedback %}
<ul class="feedback">
{% for key in item.distractor_feedback | sort %}
<li><strong>{{ key }}:</strong> {{ item.distractor_feedback[key] }}</li>
{% endfor %}
</ul>
{% endif %}
</div>
{% endfor %}
{% endfor %}
</section>
{% endfor %}
</body>
</html>
```

- [ ] **Step 4: Write the implementation**

Append to `engine/paper.py`:

```python
def render_answer_key_html(curriculum: Curriculum, templates_dir: str) -> str:
    tmpl = _env(templates_dir).get_template("answer_key.html.j2")
    return tmpl.render(groups=ordered_groups(curriculum), course=curriculum.meta)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_paper.py -v`
Expected: PASS (all tests).

- [ ] **Step 6: Commit**

```bash
git add engine/paper.py templates/answer_key.html.j2 tests/test_paper.py
git commit -m "feat(paper): answer-key HTML renderer"
```

---

### Task 4: Answer-sheet HTML (`render_answer_sheet_html`, `answer_sheet.html.j2`)

**Files:**
- Modify: `engine/paper.py`
- Create: `templates/answer_sheet.html.j2`
- Test: `tests/test_paper.py`

**Interfaces:**
- Consumes: `ordered_items` (Task 2).
- Produces: `render_answer_sheet_html(curriculum: Curriculum, templates_dir: str) -> str`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_paper.py`:

```python
def test_answer_sheet_html_lists_every_item_id():
    from engine.paper import render_answer_sheet_html
    html = render_answer_sheet_html(_curriculum(), TEMPLATES)
    for item_id in ("A1", "A2", "B1"):
        assert item_id in html
    assert "42" not in html      # the sheet is blank — no answers
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_paper.py::test_answer_sheet_html_lists_every_item_id -v`
Expected: FAIL with `ImportError: cannot import name 'render_answer_sheet_html'`.

- [ ] **Step 3: Create the answer-sheet template**

Create `templates/answer_sheet.html.j2`:

```html
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Answer Sheet</title>
<style>
{% include "print.css" %}
</style>
</head>
<body>
<h1>{% if course %}{{ course.name }}{% else %}Diagnostic Test{% endif %} — Answer Sheet</h1>
<p>Name: ____________________________  Date: ______________</p>
<p>Write the child's final answer for each question below.</p>
<table class="answer-grid">
<thead><tr><th>Question</th><th>Child's answer</th></tr></thead>
<tbody>
{% for item in items %}
<tr><td>{{ item.id }}</td><td class="blank"></td></tr>
{% endfor %}
</tbody>
</table>
</body>
</html>
```

- [ ] **Step 4: Write the implementation**

Append to `engine/paper.py`:

```python
def render_answer_sheet_html(curriculum: Curriculum, templates_dir: str) -> str:
    tmpl = _env(templates_dir).get_template("answer_sheet.html.j2")
    return tmpl.render(items=ordered_items(curriculum), course=curriculum.meta)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_paper.py -v`
Expected: PASS (all tests).

- [ ] **Step 6: Commit**

```bash
git add engine/paper.py templates/answer_sheet.html.j2 tests/test_paper.py
git commit -m "feat(paper): blank answer-sheet HTML renderer"
```

---

### Task 5: Blank fill-in YAML + blank-response filter (`render_answer_sheet_template`, `drop_blank_responses`)

**Files:**
- Modify: `engine/paper.py`
- Test: `tests/test_paper.py`

**Interfaces:**
- Consumes: `ordered_items` (Task 2); `engine.score.evaluate`.
- Produces:
  - `render_answer_sheet_template(curriculum: Curriculum) -> str` — YAML text for the parent to fill in.
  - `drop_blank_responses(raw: dict) -> dict` — removes keys with `None`/empty-string values so unanswered items are not scored as wrong.

**Why this matters:** `evaluate()` treats any *present key* as answered (`it.id in responses`). A blank template loaded as-is would map every id to `None` and score every point as 0 instead of `insufficient_evidence`. `drop_blank_responses` restores the correct "unanswered" semantics; the CLI (Task 7) applies it on the `--responses` path.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_paper.py`:

```python
import yaml

from engine.score import evaluate


def test_answer_sheet_template_round_trips_through_evaluate():
    from engine.paper import drop_blank_responses, render_answer_sheet_template
    c = _curriculum()
    text = render_answer_sheet_template(c)
    parsed = yaml.safe_load(text)

    # every item id is present as a key in the responses map
    assert set(parsed["responses"].keys()) == {"A1", "A2", "B1"}

    # blank template -> all values empty -> filtered to nothing -> no scoring, no error
    blank = drop_blank_responses(parsed["responses"])
    assert blank == {}
    result = evaluate(c, blank)
    assert result.point_results["a"].status == "insufficient_evidence"

    # a filled-in pair scores the point (both A-items correct -> Secure)
    filled = drop_blank_responses({"A1": "B", "A2": "8", "B1": ""})
    assert filled == {"A1": "B", "A2": "8"}
```

(Note: `A2`'s answer is `"42"` in the fixture, so `"8"` is deliberately wrong — the assertion only checks the filter drops the blank `B1`, not the score.)

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_paper.py::test_answer_sheet_template_round_trips_through_evaluate -v`
Expected: FAIL with `ImportError: cannot import name 'drop_blank_responses'`.

- [ ] **Step 3: Write the implementation**

Append to `engine/paper.py`:

```python
def render_answer_sheet_template(curriculum: Curriculum) -> str:
    """Emit a YAML responses skeleton: one blank entry per item, prompt as a comment."""
    lines = ["responses:"]
    for item in ordered_items(curriculum):
        prompt = item.prompt.replace("\n", " ")
        lines.append(f"  {item.id}:   # {prompt}")
    return "\n".join(lines) + "\n"


def drop_blank_responses(raw: dict) -> dict:
    """Drop keys whose value is None or blank so unanswered items are not scored."""
    return {k: v for k, v in raw.items() if v is not None and str(v).strip() != ""}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_paper.py -v`
Expected: PASS (all tests).

- [ ] **Step 5: Commit**

```bash
git add engine/paper.py tests/test_paper.py
git commit -m "feat(paper): blank fill-in YAML template and blank-response filter"
```

---

### Task 6: Report HTML (`render_report_html`, `report.html.j2`)

**Files:**
- Modify: `engine/paper.py`
- Create: `templates/report.html.j2`
- Test: `tests/test_paper.py`

**Interfaces:**
- Consumes: `engine.models.EvaluationResult`, `PathStep`.
- Produces: `render_report_html(curriculum: Curriculum, result: EvaluationResult, path: list[PathStep], templates_dir: str, student_name: str = "Student") -> str`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_paper.py`:

```python
from engine.models import EvaluationResult, PathStep, PointResult, StrandResult


def test_report_html_shows_name_band_and_focus():
    from engine.paper import render_report_html
    c = _curriculum()
    pa = PointResult("a", 0.9, "Secure", "scored", 2)
    pb = PointResult("b", 0.4, "Not yet", "scored", 2)
    strand = StrandResult("Fractions", "Developing", 0.65, "b", [pa, pb])
    result = EvaluationResult([strand], {"a": pa, "b": pb}, {"A1"})
    path = [PathStep("b", "Add fractions", ["B1"])]
    html = render_report_html(c, result, path, TEMPLATES, "Sam")
    assert "Sam" in html
    assert "Fractions" in html
    assert "Developing" in html
    assert "Add fractions" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_paper.py::test_report_html_shows_name_band_and_focus -v`
Expected: FAIL with `ImportError: cannot import name 'render_report_html'`.

- [ ] **Step 3: Create the report template**

Create `templates/report.html.j2` (HTML form of the parent report):

```html
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Learning Report</title>
<style>
{% include "print.css" %}
</style>
</head>
<body>
<h1>Learning Report for {{ name }}</h1>
<h2>Where {{ name }} stands</h2>
<ul>
{% for s in strands %}
<li><strong>{{ s.strand }}:</strong> {{ s.band or "Not enough evidence yet" }}</li>
{% endfor %}
</ul>
<h2>What this means</h2>
<p>{{ name }} is Secure in {{ secure_count }} of {{ strands | length }} area(s).
{% if focus %}The most useful next focus is <strong>{{ focus[0].title }}</strong>.{% else %}No specific gaps were found right now.{% endif %}</p>
<h2>Focus next</h2>
{% if focus %}
<ol>
{% for step in focus %}
<li><strong>{{ step.title }}</strong></li>
{% endfor %}
</ol>
{% else %}
<p>Nothing specific to fix right now — keep practicing to stay sharp.</p>
{% endif %}
</body>
</html>
```

- [ ] **Step 4: Write the implementation**

Append to `engine/paper.py`:

```python
def render_report_html(
    curriculum: Curriculum,
    result: EvaluationResult,
    path: list[PathStep],
    templates_dir: str,
    student_name: str = "Student",
) -> str:
    secure_count = sum(1 for s in result.strands if s.band == curriculum.bands[0].name)
    tmpl = _env(templates_dir).get_template("report.html.j2")
    return tmpl.render(
        name=student_name,
        strands=result.strands,
        focus=path[:3],
        secure_count=secure_count,
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_paper.py -v`
Expected: PASS (all tests).

- [ ] **Step 6: Commit**

```bash
git add engine/paper.py templates/report.html.j2 tests/test_paper.py
git commit -m "feat(paper): report HTML renderer"
```

---

### Task 7: CLI wiring (`--paper`, `--pdf`, `--out`) + README

**Files:**
- Modify: `engine/cli.py`
- Modify: `README.md`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `render_paper_html`, `render_answer_sheet_html`, `render_answer_key_html`, `render_answer_sheet_template`, `drop_blank_responses`, `render_report_html` (paper.py); `html_to_pdf` (pdf.py).
- Produces: CLI behavior — `--paper --out DIR` writes `test_paper.pdf`, `answer_sheet.pdf`, `answer_key.pdf`, `answers_blank.yaml`; `--responses ... --pdf --out DIR` writes `report.pdf`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cli.py`:

```python
def test_cli_paper_writes_print_pack(tmp_path):
    out = tmp_path / "pack"
    code = main([
        "--curriculum", "curriculum/grade5_math",
        "--paper", "--out", str(out),
    ])
    assert code == 0
    for fname in ("test_paper.pdf", "answer_sheet.pdf", "answer_key.pdf"):
        p = out / fname
        assert p.exists() and p.read_bytes()[:4] == b"%PDF"
    blank = (out / "answers_blank.yaml").read_text()
    assert "responses:" in blank
    assert "EQF-1:" in blank


def test_cli_paper_requires_out():
    import pytest
    with pytest.raises(SystemExit):
        main(["--curriculum", "curriculum/grade5_math", "--paper"])


def test_cli_pdf_report_writes_pdf(tmp_path):
    out = tmp_path / "rep"
    code = main(BASE + ["--pdf", "--out", str(out)])
    assert code == 0
    p = out / "report.pdf"
    assert p.exists() and p.read_bytes()[:4] == b"%PDF"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL — `--paper`/`--pdf`/`--out` are unrecognized arguments (SystemExit) for the new tests.

- [ ] **Step 3: Write the implementation**

Edit `engine/cli.py`. Add `import os` at the top with the other imports, and add the new arguments after the existing `--coverage` argument:

```python
    parser.add_argument("--paper", action="store_true",
                        help="Write the offline print pack (paper, answer sheet, answer key, "
                             "blank responses file) into --out and exit.")
    parser.add_argument("--pdf", action="store_true",
                        help="Also write the evaluation report as report.pdf into --out.")
    parser.add_argument("--out", help="Output directory for --paper / --pdf.")
```

Then, immediately after the `if args.coverage:` block returns, insert the `--paper` branch:

```python
    if args.paper:
        if not args.out:
            parser.error("--paper requires --out")
        os.makedirs(args.out, exist_ok=True)
        from engine.paper import (
            render_answer_key_html,
            render_answer_sheet_html,
            render_answer_sheet_template,
            render_paper_html,
        )
        from engine.pdf import html_to_pdf

        html_to_pdf(render_paper_html(curriculum, args.templates),
                    os.path.join(args.out, "test_paper.pdf"))
        html_to_pdf(render_answer_sheet_html(curriculum, args.templates),
                    os.path.join(args.out, "answer_sheet.pdf"))
        html_to_pdf(render_answer_key_html(curriculum, args.templates),
                    os.path.join(args.out, "answer_key.pdf"))
        with open(os.path.join(args.out, "answers_blank.yaml"), "w") as fh:
            fh.write(render_answer_sheet_template(curriculum))
        print(f"Wrote print pack to {args.out}")
        return 0
```

Update the responses-loading line to filter blanks. Replace:

```python
    responses = load_yaml(args.responses)["responses"]
```

with:

```python
    from engine.paper import drop_blank_responses
    responses = drop_blank_responses(load_yaml(args.responses)["responses"])
```

Then, after `path = build_path(curriculum, result)` and before the `if args.audience == "parent":` block, insert the `--pdf` branch:

```python
    if args.pdf:
        if not args.out:
            parser.error("--pdf requires --out")
        os.makedirs(args.out, exist_ok=True)
        from engine.paper import render_report_html
        from engine.pdf import html_to_pdf

        out_path = os.path.join(args.out, "report.pdf")
        html_to_pdf(render_report_html(curriculum, result, path, args.templates, args.name),
                    out_path)
        print(f"Wrote report to {out_path}")
        return 0
```

Also update the `--responses` required-error message to mention `--paper`. Replace:

```python
        parser.error("--responses is required unless --coverage is given")
```

with:

```python
        parser.error("--responses is required unless --coverage or --paper is given")
```

- [ ] **Step 4: Run the full suite to verify it passes**

Run: `uv run pytest -v`
Expected: PASS — all existing tests plus the three new CLI tests.

- [ ] **Step 5: Document the workflow in README.md**

Add an "Offline diagnostic (PDF)" section to `README.md`:

````markdown
## Offline diagnostic (PDF)

Generate a printable print pack (no responses needed):

```bash
uv run python -m engine.cli --curriculum curriculum/grade5_math --paper --out build/
```

This writes `test_paper.pdf`, `answer_sheet.pdf`, `answer_key.pdf`, and
`answers_blank.yaml` into `build/`. The child completes the paper and records final
answers on the answer sheet; the parent transcribes those answers into a copy of
`answers_blank.yaml`, then generates the report:

```bash
uv run python -m engine.cli --curriculum curriculum/grade5_math \
  --responses build/answers_filled.yaml --pdf --out build/
```

`report.pdf` contains the mastery bands and learning path. Blank lines in the answer
file are treated as unanswered.
````

- [ ] **Step 6: Commit**

```bash
git add engine/cli.py README.md tests/test_cli.py
git commit -m "feat(cli): --paper/--pdf/--out for offline PDF workflow"
```

---

## Self-Review

**Spec coverage:**
- Architecture (HTML-pure / PDF-thin split) → Tasks 1, 2.
- `test_paper.pdf` (no answers) → Task 2 + Task 7. ✓ (guard test in Task 2)
- `answer_sheet.pdf` → Task 4 + Task 7. ✓
- `answer_key.pdf` (answers + distractor feedback) → Task 3 + Task 7. ✓
- `answers_blank.yaml` (round-trips) → Task 5 + Task 7. ✓ (round-trip test in Task 5)
- `report.pdf` → Task 6 + Task 7. ✓
- CLI `--paper`/`--pdf`/`--out`, additive → Task 7. ✓
- Determinism (explicit ordering, sorted keys) → Task 2 helper + templates. ✓
- WeasyPrint added via `uv add`, confined to `engine/pdf.py` → Task 1. ✓
- CLAUDE.md deps note → Task 1; README workflow → Task 7. ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases"; every code and test step shows full code. ✓

**Type consistency:** `ordered_groups`/`ordered_items` returns and the `{"strand","points":[{"point","items"}]}` shape are used identically in Tasks 2–4 templates. `render_report_html` signature matches its call in Task 7. `drop_blank_responses` defined in Task 5 and consumed in Task 7 with the same name. `html_to_pdf(html, out_path)` defined in Task 1 and called in Task 7 consistently. ✓
