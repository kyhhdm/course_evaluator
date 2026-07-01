# Design: Shormann-modeled high-school math courses + CCSS alignment

**Date:** 2026-07-02
**Status:** Approved design, pending spec review

## Goal

Add high-school math courses to the evaluator, modeled on the Shormann Math
(DIVE into Math) sequence, and produce a report on how Shormann's high-school
credits align to the Common Core State Standards for Mathematics (CCSS-Math).

Deliverables, in order:
1. A CCSS alignment report (research/analysis) — first.
2. Two new authored courses in the repo — **Shormann Algebra 1 with Integrated
   Geometry** and **Shormann Algebra 2 with Integrated Geometry**.

## Background / findings

- Shormann's high-school lineup: Algebra 1 with Integrated Geometry, Algebra 2
  with Integrated Geometry, Precalculus with Trigonometry, Calculus 1, Calculus 2.
- Credit structure: the two Algebra courses fold geometry in (there is no
  standalone Geometry course). Finishing both Algebra 1 and Algebra 2 yields one
  credit each of Algebra 1, Algebra 2, and Geometry.
- Shormann markets itself as **not Common Core** — it is organized around the
  concepts on the PSAT/SAT/ACT/CLEP/AP exams. There is therefore no official
  vendor CCSS crosswalk; any CCSS alignment is one we construct.
- CCSS high-school math is **not grade-numbered**. It is organized by conceptual
  category: Number & Quantity (`N-*`), Algebra (`A-*`), Functions (`F-*`),
  Geometry (`G-*`), Statistics & Probability (`S-*`), plus Modeling. Codes look
  like `CCSS.HSA.SSE.A.1`. Some standards are marked `(+)` (advanced, beyond the
  college-prep core) and fall largely into Precalculus — out of scope here.

### Engine fit (no code changes required)

- `compute_coverage` filters the catalog by `std.framework == meta.framework and
  std.grade == meta.grade`, a plain equality.
- The loader coerces grade to a string (`grade=str(...)`) for both standards and
  course manifests, and both the course schema and standards-catalog schema
  already allow `grade` to be a string.
- Therefore high-school standards and courses can use `grade: "HS"` and the
  existing coverage math works unchanged. **No changes to `engine/` are needed.**

## Scope decisions

- **Build scope:** Algebra 1 + Algebra 2 only (Precalculus/Calculus deferred;
  Calculus is beyond CCSS entirely).
- **Content depth:** *Representative*. Each strand gets a few well-chosen
  knowledge points with 2–3 items each — enough to exercise the pipeline and show
  real CCSS coverage, easy to expand later. Not exhaustive.
- **Coverage scope:** *Shared "HS" band*. Both courses are tagged `grade: "HS"`
  and draw their coverage denominator from the same set of HS standards in the
  catalog. Each course covers its slice; together they approach the full set.
  This is faithful to CCSS, which does not assign HS standards to specific
  courses.

## Part A — Alignment report

A markdown document at `docs/shormann-ccss-alignment.md` containing:

- The Shormann course→credit structure and the integrated-geometry model.
- A crosswalk table: each CCSS HS conceptual category / cluster → which Shormann
  course(s) teach it (Algebra 1, Algebra 2, or "Precalculus (out of scope)").
- Honest caveats: Shormann is not Common Core; it interleaves geometry rather
  than isolating it; `(+)` advanced standards map mostly to Precalculus.
- Sources cited (diveintomath scope-and-sequence docs, teacher guides).

Built from Shormann's published Scope & Sequence documents, fetched during
implementation.

## Part B — Catalog additions

Extend `standards/ccss_math.yaml` with the CCSS high-school math standards that
Algebra 1 and Algebra 2 (with integrated geometry) cover. Each entry:

- `framework: CCSS-Math`
- `grade: "HS"`
- `domain:` the CCSS conceptual category (e.g. "Algebra", "Functions",
  "Geometry", "Number & Quantity", "Statistics & Probability")
- `description:` the standard text (paraphrased/condensed, consistent with the
  existing grade-5 entries' style)

Keys keep the CCSS high-school prefix, e.g. `CCSS.HSA.SSE.A.1`, `CCSS.HSF.IF.A.1`,
`CCSS.HSG.CO.A.1`. `(+)` standards are excluded (out of scope for these courses).

The existing 26 grade-5 + 1 grade-4 entries are untouched.

## Part C — Two new courses

`curriculum/shormann_algebra_1/` and `curriculum/shormann_algebra_2/`, each with
the standard four files, following `curriculum/_template/AUTHORING.md`:

- `course.yaml` — manifest. `framework: CCSS-Math`, `grade: "HS"`, distinct
  `id`/`name` per course.
- `knowledge_map.yaml` — strands → knowledge points, each with `prerequisites`
  and `standard_refs` into the new HS catalog entries.
- `item_bank.yaml` — ≥2 items per knowledge point; MCQ items must have no
  distractor numerically equal to the keyed answer (the ambiguous-distractor
  guard).
- `sample_responses.yaml` — a sample response set so the CLI can evaluate.

Representative strand structure:

- **Algebra 1 (with integrated geometry):** expressions & equations; linear
  functions & graphing; systems of equations; exponents & polynomials;
  integrated geometry (segments/angles/coordinate geometry basics); data &
  probability.
- **Algebra 2 (with integrated geometry):** quadratic functions; polynomial &
  rational expressions; exponential & logarithmic functions; radicals & complex
  numbers; integrated geometry (similarity/right-triangle trig/circles);
  statistics & inference.

Exact points/items chosen so that between the two courses the authored
`standard_refs` collectively touch a good spread of the HS catalog band.

## Part D — Tests

- Extend content-integrity checks to the two new courses (parametrize or add
  cases alongside the existing grade-5 checks): prerequisites resolve, no cycles,
  ≥2 items per point, every `standard_ref` exists in the catalog, and no MCQ
  distractor equals the keyed answer.
- Add a catalog test that locks the HS standard set (count and that all carry
  `grade: "HS"` / `framework: CCSS-Math`), mirroring the existing grade-5 catalog
  tests.
- The existing grade-5 tests must continue to pass unchanged.

## Verification

- `uv run pytest` — full suite green, including the new content-integrity and
  catalog tests.
- `uv run python -m engine.cli --curriculum curriculum/shormann_algebra_1 --coverage`
  and the Algebra 2 equivalent — produce sensible HS coverage reports.
- `uv run python -m engine.cli --curriculum curriculum/shormann_algebra_1
  --responses curriculum/shormann_algebra_1/sample_responses.yaml --name Sam`
  — produces a status report and learning path.

## Out of scope

- Precalculus and Calculus courses.
- A standalone Geometry course (geometry is integrated into the algebra courses,
  matching Shormann).
- Any change to `engine/` code, schemas, or the web app.
- `(+)` advanced CCSS high-school standards.
