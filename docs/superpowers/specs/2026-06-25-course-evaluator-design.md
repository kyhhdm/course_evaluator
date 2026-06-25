# Course Evaluator — Design Spec

**Date:** 2026-06-25
**Status:** Approved (design), pending implementation plan

## Goal

Build an effective evaluation system for K12 courses that:

1. Tells students and parents the student's current learning **status**.
2. Verifiably **covers the core learning goals** of the relevant curriculum.
3. Gives concrete **direction on where to improve** as a result of the evaluation.

The deliverable is **content + methodology**: structured data files describing the
curriculum and assessment, plus a thin supporting engine that turns student responses
into status reports and improvement guidance. It is content-heavy and code-light.

## Scope

"All K12 courses" is too large for one spec. We prove the methodology end-to-end on a
single concrete slice, then replicate the *content* (not the engineering) for other
strands, grades, and subjects.

**First slice:** Grade 6 Math, one strand fully worked end-to-end —
**Number & Operations (fractions / ratios)** — chosen because its prerequisite chains
most clearly demonstrate the prioritized learning path. Roughly 8–12 knowledge points,
~30 items, the full engine, both report types, and the full test suite.

The methodology is **curriculum-agnostic**. A specific standard (US Common Core, China
MoE) is a pluggable mapping layer, not baked into the engine. Grade 6 Math is the first
concrete instantiation of that mapping.

## Status model — two layers

- **Strands** (e.g. Number & Operations, Algebra, Geometry, Data) — the headline a
  parent/student sees. ~5–10 per grade.
- **Knowledge points** under each strand (e.g. "divide fractions", "ratio tables") — the
  actionable detail and the unit the "where to improve" output operates on.

## Evidence source

An **authored, tagged diagnostic test**. We control the item bank; each item maps to one
or more knowledge points and carries a difficulty rating. The same bank doubles as the
practice source for the improvement path. (No reliance on external exam data in v1.)

## Repository structure

```
course_evaluator/
  curriculum/
    grade6_math/
      knowledge_map.yaml      # strands -> knowledge points + prerequisite links
      standard_mapping.yaml   # knowledge point -> CCSS / China MoE codes
      item_bank.yaml          # diagnostic + practice items, tagged & difficulty-rated
      bands.yaml              # mastery band definitions + thresholds
  engine/
    score.py                  # responses -> per-point mastery -> strand bands
    path.py                   # weak points -> prioritized learning path (uses prereqs)
    report.py                 # renders student + parent reports from results
  templates/
    report_student.md.j2
    report_parent.md.j2
  schemas/                    # JSON Schema for each YAML file (content quality gate)
  tests/
  docs/superpowers/specs/
```

Content is **YAML** (human-authorable, diff-friendly, reviewable by non-coders). Engine
is **thin Python**. Reports render via Jinja2 templates.

## Data shapes

**Knowledge point**
- `id`
- `strand`
- `title`
- `description`
- `prerequisites: [point_ids]`  — drives learning-path sequencing
- `standard_refs: [codes]`      — into standard_mapping.yaml

**Item**
- `id`
- `points: [point_ids]`
- `difficulty: 1-3`
- `type`: `mcq` | `numeric`
- `answer`
- `distractor_feedback` (optional) — per-wrong-answer explanation

**Band** (`bands.yaml`)
- name + threshold on the difficulty-weighted score, e.g.
  - Secure ≥ 0.8
  - Developing 0.5–0.8
  - Not yet < 0.5

## Scoring methodology (`score.py`)

Deterministic, transparent, explainable to a parent in one sentence. No calibration data
required. (Chosen over IRT, which needs hundreds of responses we don't have yet, and over
AI-judging, which is non-deterministic and overkill for auto-scorable items. The data
model is unchanged if we later graduate to IRT.)

1. **Per knowledge point:**
   `mastery = Σ(difficulty × correct) / Σ(difficulty)` over items tagging that point.
   Harder items contribute more. A point needs a **minimum of 2 items** to receive a
   score; with fewer it is reported as **"insufficient evidence"** rather than a false
   read — honesty over false precision.
2. **Map to band** via `bands.yaml` thresholds → Not yet / Developing / Secure.
3. **Strand band:** roll up its points by **average**, with the **weakest point flagged**,
   so parents get a one-line headline without losing the worst signal.

## Learning path (`path.py`)

1. Collect all non-Secure knowledge points.
2. **Topologically sort by prerequisites** so foundational gaps come first
   (e.g. "fix fraction division before ratios").
3. Break ties by **impact** = number of downstream points depending on this one.
4. Each step links to **practice items** from the same bank, filtered by point +
   difficulty, excluding items already used diagnostically.

Output: an ordered list of steps, each with a target point and its practice items.

## Reports (`report.py` + templates)

- **Parent report:** strand headline bands, a plain-language 2–3 sentence summary, and the
  top 3 "focus next" items. No jargon.
- **Student report:** the full prioritized path framed as actionable steps with linked
  practice; slightly more detail than the parent view.

## Data flow

```
responses.yaml ─► score.py ─► results (point mastery + strand bands)
                                   │
                                   ├─► report.py ─► parent.md + student.md
                                   └─► path.py ─► ordered learning path ─► (into reports)
```

## Testing strategy

- **Schema validation** on every YAML file (catches authoring errors at the source).
- **Content integrity tests:**
  - every prerequisite id exists (no dangling references)
  - no prerequisite cycles
  - every knowledge point has ≥ 2 items
  - every item's referenced points exist
  - every knowledge point maps to ≥ 1 standard code
- **Engine unit tests:** scoring math, band boundaries, topological sort, and
  "insufficient evidence" handling — hand-built fixtures with known expected output.
- **Golden report test:** a sample student's responses → expected rendered report, so any
  report change is intentional and reviewed.

## What "done" means for the first slice

Number & Operations strand for Grade 6 Math, fully authored and validated; the engine
produces correct per-point mastery, strand bands, and a prioritized learning path with
linked practice; both parent and student reports render; all tests pass. At that point the
remaining strands, grades, and subjects are content replication against a proven pattern.

## Future (explicitly out of scope for v1)

- Importing existing exam/homework results to enrich the diagnosis.
- IRT / psychometric scoring once response data exists.
- Additional strands, grades, and subjects.
- Any interactive application/UI (current deliverable is content + methodology + engine).
