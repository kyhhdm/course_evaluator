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

## Adding a course

Copy `curriculum/_template/` and follow `curriculum/_template/AUTHORING.md`.
