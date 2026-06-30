# course_evaluator

An evaluation system for K-12 courses. It turns a tagged diagnostic into a status
report (strands → knowledge points) and a prioritized, practice-linked learning path
for students and parents, and reports how much of a curriculum's standards a course
covers.

## Layout

- `methodology/` — shared principles (`METHODOLOGY.md`) and default mastery `bands.yaml`.
- `standards/` — shared standards catalogs per framework (e.g. `ccss_math.yaml`).
- `curriculum/<course>/` — per-course material: `course.yaml`, `knowledge_map.yaml`,
  `item_bank.yaml`, `sample_responses.yaml`. `_template/` is the skeleton for new courses.
- `engine/` — the evaluation engine (loader, scoring, learning path, reports, coverage, CLI).
- `schemas/` — JSON Schemas validating all content.
- `templates/` — Jinja2 report templates.

## Usage

Run from the repo root.

Evaluate a student (parent or student report):
```
python -m engine.cli --curriculum curriculum/grade5_math \
  --responses curriculum/grade5_math/sample_responses.yaml \
  --name Sam --audience student
```

Standards coverage for a course:
```
python -m engine.cli --curriculum curriculum/grade5_math --coverage
```

Run the tests:
```
python -m pytest
```

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

PDF rendering uses [WeasyPrint](https://weasyprint.org/), which `uv sync` installs.
WeasyPrint also needs system libraries (Pango, cairo, GDK-PixBuf); on Debian/Ubuntu:
`sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0`.
The non-PDF commands above (evaluation, `--coverage`) do not require it.

## Online testing web app

Run the web app (self-hosted, dev server):

```bash
uv add flask          # first time only
uv run python -m engine.web
```

Then open http://127.0.0.1:5000 — add a student, take a test one question at a time,
and view the auto-scored report and past results. Data is stored in
`var/course_evaluator.db` (override with `COURSE_EVAL_DB`). This uses Flask's development
server; for anything beyond single-family self-hosting, put a production WSGI server
(e.g. gunicorn) in front.

## Adding a course

Copy `curriculum/_template/` and follow `curriculum/_template/AUTHORING.md`.
