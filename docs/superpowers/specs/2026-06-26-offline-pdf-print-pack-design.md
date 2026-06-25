# Offline PDF Print Pack + Round-Trip Report — Design

**Date:** 2026-06-26
**Status:** Approved, pending implementation plan
**Scope:** First of two planned sub-projects for "using" the Grade-5 Math content offline.
A separate, later sub-project will add an online testing web app; it is explicitly out of
scope here.

## Goal

Let a parent run a diagnostic test fully offline, then get the engine's real evaluation
(difficulty-weighted mastery bands + prioritized learning path) by re-entering the child's
answers. Concretely: produce printable PDFs of the test and supporting sheets, plus a blank
answer file the parent fills in and feeds to the existing evaluation pipeline.

## Non-goals

- No web server, sessions, accounts, persistence, or OCR/scan-based answer capture.
- No change to scoring, path-building, coverage, or the existing markdown reports.
- No new item types; current `mcq` and `numeric` only.

## Workflow

1. Parent runs the print-pack command → gets `test_paper.pdf`, `answer_sheet.pdf`,
   `answer_key.pdf`, and `answers_blank.yaml` (no responses needed).
2. Child completes `test_paper.pdf`, recording final answers on `answer_sheet.pdf`.
3. Parent transcribes the answer sheet into `answers_blank.yaml` (saving as e.g.
   `answers_filled.yaml`).
4. Parent runs the evaluation command with `--pdf` → gets `report.pdf` (mastery + learning
   path). The markdown report remains available as before.

## Architecture

Keep **HTML rendering** (pure, testable, only jinja2 — already a dependency) strictly
separate from **PDF conversion** (the one thin seam that touches WeasyPrint).

```
Curriculum ──> render_paper_html()         ┐
           ──> render_answer_key_html()     ├─(HTML strings, pure)─> html_to_pdf() ─> .pdf
           ──> render_answer_sheet_html()   │                         (WeasyPrint)
EvaluationResult ──> render_report_html()  ┘
Curriculum ──> render_answer_sheet_template() ─> answers_blank.yaml (blank, to fill in)
```

### New modules

- **`engine/paper.py`** — pure functions returning HTML strings:
  - `render_paper_html(curriculum, templates_dir) -> str`
  - `render_answer_key_html(curriculum, templates_dir) -> str`
  - `render_answer_sheet_html(curriculum, templates_dir) -> str`
  - `render_report_html(curriculum, result, path, templates_dir, student_name) -> str`
  - `render_answer_sheet_template(curriculum) -> str` (YAML text, not HTML)

  No WeasyPrint import here. All content logic lives behind these functions so it is testable
  without the PDF dependency.

- **`engine/pdf.py`** — a single `html_to_pdf(html: str, out_path: str) -> None` wrapper.
  The **only** file in the codebase that imports WeasyPrint, so the new dependency is one
  deliberate, mockable seam.

### New templates (in `templates/`)

- `test_paper.html.j2` — items in deterministic order, grouped by strand. MCQ renders the
  options; numeric renders a labeled blank. **No answers.**
- `answer_sheet.html.j2` — compact grid, one row per item: item ID → blank answer box.
- `answer_key.html.j2` — items + correct answers, plus `distractor_feedback` where present.
- `report.html.j2` — HTML form of the existing parent report content (mastery bands + focus
  path).
- `print.css` — shared print stylesheet (page size, margins, strand grouping, page breaks).

Existing markdown templates (`report_parent.md.j2`, `report_student.md.j2`) are untouched.

## Deliverables

| Output | Contents | Guard |
|---|---|---|
| `test_paper.pdf` | All items, deterministic order, grouped by strand; MCQ options shown; numeric blank. No answers. | Test asserts no keyed answer string appears in the paper HTML. |
| `answer_sheet.pdf` | One-page grid: every item ID with a blank answer box. | Test asserts every item ID is present. |
| `answer_key.pdf` | Items + correct answers + distractor feedback where present. | Test asserts answers are present. |
| `answers_blank.yaml` | `responses:` map: every item ID with an empty value; each item's prompt as a trailing comment. | Round-trips: loads via the loader and is accepted by `evaluate()`. |
| `report.pdf` | Mastery bands + learning path, from `report.html.j2`. Markdown report still available. | — |

## CLI surface (additive)

New flags layered onto the existing `argparse`; nothing existing changes behavior.

```bash
# Print pack + blank fill-in file (no responses needed):
uv run python -m engine.cli --curriculum curriculum/grade5_math --paper --out build/

# Evaluation, now also as PDF:
uv run python -m engine.cli --curriculum curriculum/grade5_math \
  --responses build/answers_filled.yaml --pdf --out build/
```

- `--paper` — write the four print-pack outputs (`test_paper.pdf`, `answer_sheet.pdf`,
  `answer_key.pdf`, `answers_blank.yaml`) into `--out`. Requires `--out`. Ignores
  `--responses`.
- `--pdf` — in the normal evaluation flow, additionally write `report.pdf` into `--out`.
  Requires `--responses` and `--out`.
- `--out <dir>` — output directory (created if absent). Filenames are fixed as above.

The CLI remains the only orchestration point: it calls `engine.paper` for HTML, then
`engine.pdf.html_to_pdf` for the PDF conversion, and writes the blank YAML directly.

## Determinism

All document ordering is explicit and stable, consistent with the project's hard determinism
rule: items grouped by strand → knowledge point in knowledge-map order, items within a point
in item-bank order (or `sorted()` by id where no natural order exists). No `set` iteration
order may reach output. Tests assert stable ordering.

## Dependency

- Add WeasyPrint with `uv add weasyprint` (per the project's uv rule — no hand-edit of
  `pyproject.toml`, no `pip`).
- Confine the import to `engine/pdf.py`.
- Document the addition in CLAUDE.md's runtime-deps line as a deliberate choice (it brings
  system-library requirements at install time; `uv sync` provisions it).

## Testing

- **Pure HTML tests (no WeasyPrint):**
  - `test_paper` HTML contains every item prompt and **no** keyed answer string.
  - `answer_key` HTML contains the correct answers.
  - `answer_sheet` HTML lists every item ID.
  - `answers_blank.yaml` lists every item ID and **round-trips** through the loader and
    `evaluate()` without error.
  - Document order is asserted stable/deterministic.
- **PDF seam:** one test that `html_to_pdf` writes a non-empty `.pdf`; elsewhere the seam is
  mocked so the suite stays fast and mostly dependency-free.
- Run via `uv run pytest`.

## Risks / mitigations

- **WeasyPrint system libs / install weight** — isolated to `engine/pdf.py`; HTML logic is
  fully testable without it; `uv sync` handles provisioning.
- **Answer leakage into the test paper** — explicit guard test, analogous to the existing
  ambiguous-distractor guard.
- **Transcription errors during re-entry** — mitigated by the dedicated one-page answer sheet
  that consolidates answers for easy, line-by-line transcription; out of scope to eliminate
  fully (a later web app removes the step entirely).
