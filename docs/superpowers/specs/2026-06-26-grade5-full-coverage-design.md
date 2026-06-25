# Grade 5 Full Standards Coverage — Design Spec

**Date:** 2026-06-26
**Status:** Approved (design), pending implementation plan
**Builds on:** the multi-course refactor (coverage report, shared CCSS-Math catalog)

## Goal

Take Grade-5 Math standards coverage from **6/26 → 26/26 (100%)**, organized into the five
official CCSS domains as strands, so `--coverage` reports full coverage and the
parent/student reports span the whole curriculum.

## Scope

This is **pure content authoring**. The engine, loader, schemas, coverage code, and report
templates do not change. Only these change:

- `curriculum/grade5_math/knowledge_map.yaml` — relabel existing points' strands; add 20 new points
- `curriculum/grade5_math/item_bank.yaml` — add ~45 items for the new points
- `curriculum/grade5_math/sample_responses.yaml` — extend the demo student to all items
- A few **test expectations** that hard-code the old 6/26 numbers (listed below)

The shared `standards/ccss_math.yaml` catalog is **unchanged** — it already lists all 26
Grade-5 standards; this work only adds `knowledge_map` references to them.

Out of scope: new grades/subjects; changing scoring/path/report logic; sub-standard
granularity (we map one new point per uncovered standard, not per sub-part like 5.NF.B.4a).

## Strand reorganization (5 CCSS domains)

The single "Number & Operations" strand becomes the five official domains. Existing points
keep their ids, items, and prerequisites — only their `strand` field changes.

| Strand | Standards covered | Points |
|--------|-------------------|--------|
| Operations & Algebraic Thinking | 5.OA.A.1, A.2, B.3 | 3 new |
| Number & Operations in Base Ten | 5.NBT.A.1, A.2, A.3, A.4, B.5, B.6, B.7 | `decimal-place-value` (A.3) + `add-subtract-decimals` (B.7) relabeled; 5 new |
| Number & Operations—Fractions | 5.NF.A.1, A.2, B.3, B.4, B.5, B.6, B.7 | 6 existing fraction points relabeled; 3 new |
| Measurement & Data | 5.MD.A.1, B.2, C.3, C.4, C.5 | 5 new |
| Geometry | 5.G.A.1, A.2, B.3, B.4 | 4 new |

Existing points relabeled to **Number & Operations—Fractions**: `equiv-fractions`,
`add-like`, `add-unlike`, `mult-fraction-whole`, `mult-fraction-fraction`,
`divide-unit-fraction`. Relabeled to **Number & Operations in Base Ten**:
`decimal-place-value`, `add-subtract-decimals`.

## New knowledge points (20, one per uncovered standard)

Each new point references exactly its standard code and carries within-domain prerequisite
chains so the learning path sequences sensibly. Proposed ids and prerequisites:

**Operations & Algebraic Thinking**
- `oa-eval-expressions` (5.OA.A.1) — prereq: none
- `oa-write-expressions` (5.OA.A.2) — prereq: `oa-eval-expressions`
- `oa-patterns-graph` (5.OA.B.3) — prereq: `g-coordinate-system`

**Number & Operations in Base Ten**
- `nbt-place-value` (5.NBT.A.1) — prereq: none
- `nbt-powers-of-ten` (5.NBT.A.2) — prereq: `nbt-place-value`
- `nbt-round-decimals` (5.NBT.A.4) — prereq: `decimal-place-value`
- `nbt-mult-multidigit` (5.NBT.B.5) — prereq: none
- `nbt-divide-multidigit` (5.NBT.B.6) — prereq: `nbt-mult-multidigit`

**Number & Operations—Fractions**
- `nf-fraction-as-division` (5.NF.B.3) — prereq: none
- `nf-scaling` (5.NF.B.5) — prereq: `mult-fraction-fraction`
- `nf-mult-realworld` (5.NF.B.6) — prereq: `nf-scaling`

**Measurement & Data**
- `md-unit-conversion` (5.MD.A.1) — prereq: none
- `md-line-plots` (5.MD.B.2) — prereq: `add-unlike`
- `md-volume-concept` (5.MD.C.3) — prereq: none
- `md-measure-volume` (5.MD.C.4) — prereq: `md-volume-concept`
- `md-volume-formulas` (5.MD.C.5) — prereq: `md-measure-volume`

**Geometry**
- `g-coordinate-system` (5.G.A.1) — prereq: none
- `g-graph-points` (5.G.A.2) — prereq: `g-coordinate-system`
- `g-figure-hierarchy` (5.G.B.3) — prereq: none
- `g-classify-figures` (5.G.B.4) — prereq: `g-figure-hierarchy`

All prerequisite references must resolve and the graph must stay acyclic (enforced by the
existing content-integrity tests).

## Items

Each new point gets 2–3 items (≈45 new items total), `mcq` or `numeric`, difficulty 1–3,
every answer math-verified. Per the guard added in PR #2, **no MCQ distractor may be
numerically equal to the keyed answer**. Items follow the existing `item_bank.yaml` shape
(`id`, `points`, `difficulty`, `type`, `prompt`, `answer`, `options` for mcq).

## Demo student (sample_responses.yaml)

Extend the demo student to answer all items (original + new) with a believable cross-domain
profile: solid in Base Ten and Geometry, mixed in Operations & Algebraic Thinking, weak in
the harder Fractions points and in Volume (5.MD.C). This keeps the parent/student reports
and the prioritized learning path meaningful across every strand and exercises the engine on
the full breadth.

## Testing

The content-integrity suite and the MCQ-distractor guard are the authoring gate and apply
automatically to all new content (≥2 items per point, prerequisites resolve, no cycles,
item points exist, standard refs exist in the catalog, distractors distinct from answers).

**Expectations to update** (they hard-code the old 6/26 state):

- `tests/test_coverage.py::test_grade5_math_real_coverage` — change to: `total == 26`,
  `len(covered) == 26`, `missing == []`, `percentage == 1.0`, and assert `CCSS.5.G.A.1` is
  now in `covered` (it moves out of `missing`). The grade-4 prerequisite `CCSS.4.NF.A.1`
  remains in `out_of_scope`.
- `tests/test_cli.py` coverage test — assert `"26 / 26"` instead of `"6 / 26"`.

**Unchanged:** `test_standards_catalog.py` (catalog untouched), and the engine unit tests
(`test_score.py`, `test_path.py`, `test_report.py`, `test_models.py`, `test_loader.py`,
`test_schemas.py`, `test_template.py`).

## What "done" means

`python -m engine.cli --curriculum curriculum/grade5_math --coverage` prints
`26 / 26 standards covered (100.0%)` with an empty Missing list; the parent and student
reports render across all five strands; and the full test suite passes.
