# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A K-12 course-evaluation system. It turns a tagged diagnostic test into a status report
(strands → knowledge points) and a prioritized, practice-linked learning path for students
and parents, and reports how much of a curriculum's standards a course covers. It is
**content + methodology, code-light**: most of the value lives in authored YAML; the engine
is a thin deterministic pipeline over it.

## Commands

Run everything from the repo root (the `pyproject.toml` sets `pythonpath = ["."]` and
`testpaths = ["tests"]`, which is what makes `engine` importable without installation).

```bash
python -m pytest                              # full suite
python -m pytest tests/test_score.py -v       # one file
python -m pytest tests/test_score.py::test_difficulty_weighted_mastery -v   # one test

# Evaluate a student (parent is the default audience):
python -m engine.cli --curriculum curriculum/grade5_math \
  --responses curriculum/grade5_math/sample_responses.yaml --name Sam --audience student

# Standards-coverage report for a course (no responses needed):
python -m engine.cli --curriculum curriculum/grade5_math --coverage
```

Runtime deps: `pyyaml`, `jsonschema`, `jinja2`. Dev: `pytest`. Python `>=3.10`. Keep
dependencies limited to these — adding one is a deliberate decision, not a default.

## Architecture

The data flow is a one-way pipeline, each stage a pure function over dataclasses:

```
YAML content ──(loader + JSON Schema)──> Curriculum ──> evaluate ──> EvaluationResult
                                                │                         │
                                                │                         ├─> build_path ─> [PathStep]
                                                │                         └─> render_parent/student ─> markdown
                                                └─> compute_coverage ─> CoverageReport
```

- **`engine/models.py`** — all dataclasses (`KnowledgePoint`, `Item`, `Band`, `Standard`,
  `CourseMeta`, `Curriculum`, `EvaluationResult`, `PathStep`, `CoverageReport`). No logic
  beyond small `Curriculum` accessors. `score.py`/`path.py`/`report.py` build `Curriculum`
  directly in tests, so model changes ripple widely — keep it backward-compatible.
- **`engine/loader.py`** — `load_course(course_dir, schemas_dir, methodology_dir, standards_dir)`
  is the entry point. It validates every YAML against its schema, then wires the course
  manifest + knowledge map + item bank + bands + standards catalog into a `Curriculum`.
  `load_catalog`/`load_bands` are the sub-loaders.
- **`engine/score.py`** — `evaluate()` computes per-knowledge-point mastery, rolls up to
  strands. **`engine/path.py`** — prerequisite-sequenced learning path. **`engine/report.py`**
  — Jinja2 rendering. **`engine/coverage.py`** — standards-coverage math. **`engine/cli.py`**
  — argument wiring; the only place that orchestrates the stages.

### Shared-vs-course separation (the core design)

Per-course material and global principles live in separate trees. Respect this boundary —
it is the whole point of the layout:

- `curriculum/<course>/` — **only** course-specific content: `course.yaml` (manifest),
  `knowledge_map.yaml`, `item_bank.yaml`, `sample_responses.yaml`. A course may add its own
  `bands.yaml` to override the default.
- `methodology/` — shared principles: `bands.yaml` (default mastery thresholds) and
  `METHODOLOGY.md`. **Read `METHODOLOGY.md` first** — it explains the two-layer model,
  scoring philosophy, and band meanings that the rest of the system assumes.
- `standards/` — shared standards catalogs, one file per framework (e.g. `ccss_math.yaml`).
- `schemas/` — JSON Schemas; loading validates against them, so they are the content gate.
- `curriculum/_template/` — copy-and-fill skeleton for a new course (see its `AUTHORING.md`).
  It is a skeleton, **not** a loadable course; no test runs `load_course` on it.

### Conventions that are easy to get wrong

- **Determinism is a hard requirement.** Every list that reaches output is `sorted()`, and
  ordering relies on insertion-ordered dicts and stable sorts. Never let `set` iteration
  order leak into printed output.
- **Two-layer status model:** strands are the parent/student headline; knowledge points are
  the actionable detail. Mastery is reported per point and rolled up per strand.
- **Scoring** is transparent difficulty-weighted thresholds:
  `mastery = sum(difficulty * correct) / sum(difficulty)` over answered items. A point with
  `< MIN_ITEMS` (= 2) answered items is `insufficient_evidence`, never given a false score.
  Bands, highest-first: `Secure ≥ 0.8`, `Developing ≥ 0.5`, `Not yet ≥ 0.0`. No IRT, no LLM judging.
- **Bands resolution:** the shared `methodology/bands.yaml` is the default; a course-level
  `bands.yaml` overrides it **only if that file exists**.
- **Coverage** is informational only — it never fails a test or blocks. The denominator is the
  catalog entries whose `framework` and `grade` match the course's `course.yaml`; referenced
  codes outside that slice (e.g. grade-4 prerequisites) are `out_of_scope`, not counted.
- **Catalog filename convention:** derived from the framework as
  `framework.lower().replace("-", "_") + ".yaml"` (e.g. `CCSS-Math` → `ccss_math.yaml`).
- Standard codes keep their framework prefix as the catalog key (`CCSS.5.NF.A.1`); a
  standard's grade comes from its explicit `grade` field, never parsed from the code.

## Testing

Tests are the quality gate for both code and content:

- `test_content_integrity.py` validates the authored Grade-5 content: prerequisites resolve,
  no cycles, ≥2 items per point, standard refs exist in the catalog, and **no MCQ distractor
  is numerically equal to the keyed answer** (an ambiguous-distractor guard — two real content
  bugs were caught this way). If one fails, the bug is in the YAML, not the test.
- `test_standards_catalog.py` / `test_coverage.py` lock the catalog shape and coverage math.
- Engine unit tests build `Curriculum`/models directly with small fixtures.

## Adding a course

Copy `curriculum/_template/` to `curriculum/<id>/`, follow its `AUTHORING.md`, add any new
standard codes to `standards/<framework>.yaml` (not into the course), then verify with
`python -m pytest` and `python -m engine.cli --curriculum curriculum/<id> --coverage`.

## Design records

Specs and implementation plans live in `docs/superpowers/specs/` and `docs/superpowers/plans/`.
They are point-in-time design records of how the system was built and why — useful background,
not current API documentation.
