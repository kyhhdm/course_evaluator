# Multi-Course Refactor & Standards Coverage — Design Spec

**Date:** 2026-06-26
**Status:** Approved (design), pending implementation plan
**Builds on:** the Grade 5 Math evaluator (branch `feat/grade5-math-evaluator`)

## Goal

Prepare the project to hold many courses by separating **shared principles** from
**course-specific material**, and make curriculum coverage (project goal #2) a
measurable, printable number per course.

Two concrete problems this fixes:

1. **Shared principles are trapped inside the course folder.** `bands.yaml` (a global
   methodology decision) and the standards mapping (shared reference data) currently live
   in `curriculum/grade5_math/`, so every new course would duplicate them and they would
   drift.
2. **Curriculum coverage is asserted but not measurable.** `standard_mapping.yaml` lists
   only the codes a course already uses, so "what's missing" cannot be computed.

## Scope

In scope: relocate shared principles, introduce a shared standards catalog, add a
per-course manifest, add a coverage report, update the loader/CLI/models/schemas/tests,
and add three documentation/skeleton extras. The evaluation engine's scoring, path, and
report behavior is unchanged.

Out of scope: new grades/subjects, non-CCSS frameworks (the catalog is structured to hold
them but only CCSS Grade-5 Math is authored now), enforcing coverage thresholds.

## Target directory layout

```
methodology/
  METHODOLOGY.md              # shared principles (two-layer model, scoring philosophy,
                              #   what bands mean, how to add a course)
  bands.yaml                  # default mastery bands (moved out of the course)
standards/
  ccss_math.yaml              # complete CCSS Grade-5 Math catalog (+ grade-4 prereqs in use)
curriculum/
  _template/                  # skeleton course for copy-and-fill
    course.yaml
    knowledge_map.yaml
    item_bank.yaml
    sample_responses.yaml
    AUTHORING.md              # checklist for authoring a new course
  grade5_math/
    course.yaml               # NEW manifest
    knowledge_map.yaml
    item_bank.yaml
    sample_responses.yaml
    # bands.yaml ONLY if this course overrides the default (absent now)
engine/
  models.py                   # + Standard, CourseMeta, CoverageReport; Curriculum.meta
  loader.py                   # load_catalog, load_bands, load_course
  coverage.py                 # NEW: compute_coverage
  score.py  path.py  report.py  cli.py
schemas/
  course.schema.json          # NEW
  standards_catalog.schema.json  # renamed from standard_mapping.schema.json
  bands.schema.json  knowledge_map.schema.json  item_bank.schema.json
templates/                    # unchanged
tests/
README.md                     # refreshed
```

## Data shapes

**CourseMeta (`course.yaml`)**
- `id` (e.g. `grade5_math`)
- `name` (e.g. `Grade 5 Mathematics`)
- `framework` (e.g. `CCSS-Math`)
- `grade` (e.g. `5`)

The `(framework, grade)` pair defines which catalog slice is the coverage denominator, so
grade-4 prerequisite references do not dilute the Grade-5 percentage.

**Standard (entry in `standards/ccss_math.yaml`, keyed by code)**
- `framework` (e.g. `CCSS-Math`)
- `grade` (e.g. `5` or `4`)
- `domain` (e.g. `5.NF` / "Number & Operations—Fractions")
- `description`

Replaces the per-course `standard_mapping.yaml`. Single source of truth; a knowledge
point's `standard_refs` MUST resolve against it.

**Band (`bands.yaml`)** — unchanged shape, relocated to `methodology/`. Loader reads the
shared default; if `curriculum/<course>/bands.yaml` exists it overrides.

**CoverageReport (computed, not stored)**
- `framework`, `grade`
- `total` (count of in-scope catalog standards)
- `covered` (sorted list of in-scope codes referenced by some knowledge point)
- `missing` (sorted list of in-scope codes referenced by no knowledge point)
- `out_of_scope` (sorted list of referenced codes outside the course's framework/grade —
  e.g. grade-4 prereqs; informational, not counted)
- `percentage` (covered/total, 0.0 if total is 0)

**Curriculum** gains `meta: CourseMeta`; its `standards` field becomes the shared catalog
(`dict[str, Standard]`) rather than a per-course bundle.

## Loader (`engine/loader.py`)

- `load_catalog(path, schema_path) -> dict[str, Standard]` — load + validate the shared
  standards catalog.
- `load_bands(default_path, course_override_path | None) -> tuple[Band, ...]` — shared
  default; course override wins when the override file exists. Sorted descending by
  `min_score` (unchanged ordering rule).
- `load_course(course_dir, schemas_dir, methodology_dir, standards_dir) -> Curriculum` —
  wires `course.yaml` + `knowledge_map.yaml` + `item_bank.yaml` + bands + catalog into a
  `Curriculum` carrying `meta`. Replaces today's `load_curriculum`.

`load_yaml` and `validate` are retained as-is.

## Coverage (`engine/coverage.py`, new)

`compute_coverage(curriculum) -> CoverageReport`:
1. `scope = {code for code, std in catalog if std.framework == meta.framework and std.grade == meta.grade}`
2. `referenced = {ref for point in points for ref in point.standard_refs}`
3. `covered = sorted(scope & referenced)`; `missing = sorted(scope - covered)`
4. `out_of_scope = sorted(referenced - scope)`
5. `percentage = len(covered) / len(scope)` (0.0 when `scope` is empty)

Pure, deterministic (sorted lists everywhere).

## CLI (`engine/cli.py`)

- New flag `--coverage`: prints the coverage report (framework, grade, percentage,
  covered list, missing list, out-of-scope list) and returns 0, instead of a
  student/parent report.
- Path flags resolve to the repo's shared dirs by default: `--methodology`, `--standards`
  (alongside existing `--curriculum`, `--schemas`, `--templates`).
- Report path (parent/student) behavior is otherwise unchanged.

## Migration steps (mechanical, behavior-preserving)

1. `git mv curriculum/grade5_math/bands.yaml methodology/bands.yaml`.
2. Author `standards/ccss_math.yaml` as the full CCSS Grade-5 Math catalog with
   `framework/grade/domain/description`, sourced from the authoritative CCSS standards
   (corestandards.org), including the grade-4 prerequisites currently referenced
   (`CCSS.4.NF.A.1`). Delete `curriculum/grade5_math/standard_mapping.yaml`.
3. Add `curriculum/grade5_math/course.yaml` (`framework: CCSS-Math`, `grade: 5`).
4. Rename `schemas/standard_mapping.schema.json → schemas/standards_catalog.schema.json`
   (now validates the catalog: `framework/grade/domain/description` required) and add
   `schemas/course.schema.json`.
5. Update `engine/models.py`, `engine/loader.py`, `engine/cli.py`, and all call sites.

## Testing

- **`tests/test_standards_catalog.py`** (new): catalog validates against its schema; every
  entry has `framework`, `grade`, `domain`, `description`.
- **`tests/test_coverage.py`** (new): on `grade5_math` — `covered` includes
  `CCSS.5.NF.A.1`; `missing` includes a known-uncovered standard (`CCSS.5.G.A.1`); the
  grade-4 prerequisite `CCSS.4.NF.A.1` appears in `out_of_scope`, not in the denominator;
  `percentage == len(covered)/len(scope)`.
- **Updated** `tests/test_content_integrity.py`: knowledge-point `standard_refs` resolve
  against the shared catalog; the new MCQ-distractor-uniqueness guard is retained.
- **Updated** `tests/test_loader.py`, `tests/test_cli.py`: new `load_course` signature,
  shared paths, and `--coverage` output.
- **Unchanged**: `tests/test_score.py`, `tests/test_path.py`, `tests/test_report.py`,
  `tests/test_models.py` (they construct `Curriculum`/models directly).

## Documentation & skeleton extras

- **`METHODOLOGY.md`**: the durable principles doc — two-layer status model, transparent
  difficulty-weighted threshold scoring, what the bands mean, the learning-path logic, and
  a step-by-step "how to add a course".
- **`curriculum/_template/`**: stub `course.yaml`, `knowledge_map.yaml`, `item_bank.yaml`,
  `sample_responses.yaml`, plus `AUTHORING.md` (the authoring checklist). The template must
  be excluded from any "load every course" logic and from the test suite's real-content
  checks (it is a skeleton, not a valid course).
- **`README.md`**: refreshed to describe the project, the directory layout, and how to run
  the CLI and the coverage report.

## What "done" means

`grade5_math` loads via `load_course` with bands from `methodology/` and standards from the
shared catalog; `course_evaluator … --coverage` prints Grade-5 coverage (~6 of ~26
standards) with the correct covered/missing/out-of-scope breakdown; all tests pass; and the
course folder contains only course-specific material. Adding a second course is then: copy
`_template/`, fill it in, reference catalog codes, run `--coverage`.
