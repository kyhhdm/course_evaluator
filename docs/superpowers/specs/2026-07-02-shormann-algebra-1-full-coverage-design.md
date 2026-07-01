# Design: Shormann Algebra 1 — full topic coverage, calibrated item bank

**Date:** 2026-07-02
**Status:** Draft design, pending user review
**Supersedes (for Algebra 1 only):** the "representative, not exhaustive" scope
decision in `2026-07-02-shormann-hs-math-courses-design.md`.

## Goal

Bring `curriculum/shormann_algebra_1` from a thin representative sample (6 knowledge
points, 24 items, 48% CCSS coverage) to a **faithful, full-coverage** course:

1. A knowledge map that mirrors Shormann Algebra 1's own Scope & Sequence and whose
   `standard_refs` collectively cover **all 25** HS standards in the CCSS-Math catalog band.
2. An item bank of diagnostic + practice questions **calibrated to the authentic
   Shormann problems** in the eTextbook, each traceable to the lesson it exercises.
3. Tests that lock both the structure and the new item-to-lesson fidelity.

## Decisions (from brainstorming)

- **"Full coverage" = faithful topics + all 25 CCSS.** Restructure to Shormann's real
  strands and choose refs so Algebra 1 alone covers the full HS band. We **accept that
  Algebra 1 and Algebra 2 now overlap** in CCSS coverage — this is faithful, because
  Shormann Algebra 1 genuinely spirals quadratics, complex numbers, similarity, and
  right-triangle trig in its own lessons. CCSS does not assign HS standards to courses,
  so overlap is expected, not a defect.
- **Authentic source problems are available.** The full eTextbooks are in
  `asset/shormann_math/` (`Shormann Algebra 1 Textbook.pdf`, 580 pp). Items are
  calibrated to real Shormann problems rather than approximated.

## Sources (all in-repo)

- `standards/reference/Shormann_Algebra1_TeacherGuide.pdf` — Scope & Sequence (pp. 19–26)
  and the titled 100-lesson Course Sequence (pp. 27–32). The topic authority.
- `asset/shormann_math/Shormann Algebra 1 Textbook.pdf` — the eTextbook, 100 lessons
  with worked examples and practice sets, text-extractable. The problem authority. A
  lesson→page index is derivable from its Table of Contents (front-matter offset ≈ 7
  PDF pages ahead of printed page numbers).

## Part 1 — Knowledge map restructure

Replace the 6 points with **8 strands / 23 knowledge points**. Every CCSS code in the
25-standard HS band is carried by exactly one point (some points carry two related
codes). Each point also lists the Shormann lessons it draws from (see Part 2 for how
that is recorded).

| Strand | Point id | Title / focus | `standard_refs` | Lessons | Prereqs |
|---|---|---|---|---|---|
| **Number, Ratio & Quantity** | `a1-num-realnum` | Real numbers, absolute value, order | — | 2–3 | — |
| | `a1-num-exprad` | Exponents, radicals, scientific notation | N.RN.A.2 | 3, 30–33, 58 | `a1-num-realnum` |
| | `a1-num-units` | Units, measurement conversion, proportion | N.Q.A.1 | 5–6, 44–45 | `a1-num-realnum` |
| **Expressions & Equations** | `a1-expr-interpret` | Interpret & simplify expressions | A.SSE.A.1 | 8, 35–38 | `a1-num-realnum` |
| | `a1-expr-model` | Model situations with equations | A.CED.A.1 | 7–8, 48 | `a1-expr-interpret` |
| | `a1-expr-linear` | Solve linear equations | A.REI.B.3 | 7, 46 | `a1-expr-interpret` |
| **Polynomials & Quadratics** | `a1-poly-ops` | Polynomial operations | A.APR.A.1 | 37–38 | `a1-expr-interpret`, `a1-num-exprad` |
| | `a1-poly-factor` | Factoring & equivalent forms | A.SSE.B.3 | 51, 75, 91 | `a1-poly-ops` |
| | `a1-quad-solve` | Solve quadratic equations | A.REI.B.4 | 75–76, 91–92 | `a1-poly-factor`, `a1-expr-linear` |
| | `a1-complex` | Complex numbers & complex solutions | N.CN.A.1, N.CN.C.7 | 92, 95 | `a1-quad-solve` |
| **Functions & Modeling** | `a1-func-concept` | Function concept, notation, domain/range | F.IF.A.1 | 15, 52–53 | `a1-expr-linear` |
| | `a1-func-graph` | Graph key features & transformations | F.IF.B.4, F.BF.B.3 | 16, 55–57 | `a1-func-concept` |
| | `a1-func-linexp` | Linear vs. exponential; construct models | F.LE.A.1, F.LE.A.2 | 48, 81 | `a1-func-concept` |
| **Systems of Equations** | `a1-systems` | Solve systems (graph/substitution/elimination) | A.REI.C.6 | 17, 61, 64, 70 | `a1-expr-linear`, `a1-func-graph` |
| **Geometry: Reasoning & Proof** | `a1-geo-def` | Precise geometric definitions | G.CO.A.1 | 9–11 | — |
| | `a1-geo-proof` | Triangle theorems, deductive/inductive proof | G.CO.C.10 | 10, 66–68 | `a1-geo-def` |
| | `a1-geo-circle` | Circle angle relationships | G.C.A.2 | 40, 66 | `a1-geo-def` |
| **Geometry: Similarity, Trig & Measurement** | `a1-geo-sim` | Similarity & scaling | G.SRT.A.2 | 6, 9 | `a1-geo-def` |
| | `a1-geo-trig` | Right-triangle trig & Pythagorean | G.SRT.C.8 | 12, 19, 43, 80 | `a1-geo-sim` |
| | `a1-geo-measure` | Perimeter, area, surface area, volume | G.GMD.A.3 | 13, 41–42 | `a1-geo-def`, `a1-num-units` |
| **Data, Statistics & Probability** | `a1-data-display` | Data displays & summary statistics | S.ID.A.1 | 23 | — |
| | `a1-data-scatter` | Scatter plots & line of best fit | S.ID.B.6 | 24, 94 | `a1-data-display` |
| | `a1-data-interpret` | Interpret slope & intercept of a linear model | S.ID.C.7 | 24, 94 | `a1-data-scatter`, `a1-func-graph` |

**Coverage result:** 25 / 25 (100%) of the HS band, up from 12 / 25.

**Honest scope note (added to the alignment doc, not the map):** Shormann Algebra 1
also teaches material with no CCSS-catalog equivalent — history of mathematics, intro
calculus (L20–22), computer/binary math (L25), and cross-disciplinary applications
(Punnett squares, gas laws). These are deliberately left without `standard_refs`; the
knowledge map represents only the CCSS-mappable topics, and the alignment doc records
the rest as "taught but outside the catalog."

## Part 2 — Item-to-lesson traceability (`lesson_refs`)

Add an **optional** `lesson_refs` field to items: a list of integers naming the
Shormann lesson(s) an item exercises. This is the machine-checkable fidelity anchor —
it ties each authored item to a specific lesson in the eTextbook, so an item can be
audited against the real problems it was calibrated from.

Changes (small, backward-compatible — grade-5 content is untouched and needs no field):

- **`schemas/item_bank.schema.json`** — add
  `"lesson_refs": {"type": "array", "items": {"type": "integer", "minimum": 1}}`
  to the item `properties` (still `additionalProperties: false`).
- **`engine/models.py`** — add `lesson_refs: list[int] = field(default_factory=list)`
  to `Item`. Optional with a default → existing constructors keep working.
- **`engine/loader.py`** — read `lesson_refs` from YAML into the `Item` (default `[]`).

No scoring/report/path behavior changes — `lesson_refs` is metadata, consumed only by
tests and human review.

## Part 3 — Item bank authoring (calibrated to the eTextbook)

**Blueprint:** each knowledge point gets **≥2 diagnostic + ≥2 practice** items,
difficulty-laddered 1→3 and spanning the point's sub-skills. Broad points (e.g.
`a1-quad-solve`, `a1-geo-trig`) get more. Target ≈ 90+ items total (up from 24).

**Calibration workflow, per point:**
1. Open the point's lessons in the eTextbook (via the lesson→page index).
2. Read the worked examples and practice set to fix the authentic style, notation,
   and difficulty for that lesson.
3. Author diagnostic/practice items modeled on those problems — **not copied**
   (the eTextbook is copyrighted; items are original, same skill and level).
4. Tag each item with `lesson_refs` and `standard_refs` consistent with its point.
5. Keep the existing guards: `type` ∈ {mcq, numeric}; MCQ has no distractor
   numerically equal to the key; numeric answers are exact strings.

**Fidelity review pass:** after authoring, a second read (human or a fresh agent)
checks each item against its cited lesson: does the item test what that lesson
teaches, at that lesson's level? Mismatches are corrected or re-tagged.

## Part 4 — Sample responses

Regenerate `curriculum/shormann_algebra_1/sample_responses.yaml` to reference the new
item ids, giving a realistic spread (some strands secure, some developing, at least
one point left with `insufficient_evidence`) so the CLI produces an illustrative
status report and learning path.

## Part 5 — Tests

- **`test_content_integrity.py`** (already parametrized over both Shormann courses):
  the new points/items must satisfy the existing invariants — prerequisites resolve,
  no cycles, ≥2 items per point, every `standard_ref` exists in the catalog, no MCQ
  distractor equals the key.
- **New check:** every Shormann item with `lesson_refs` cites lesson(s) in 1–100, and
  each point's items cite lessons consistent with the point's mapping (a small
  allow-set per point, derived from Part 1's "Lessons" column).
- **New check:** `compute_coverage` on `shormann_algebra_1` reports 25 / 25 covered
  (locks the full-coverage goal; a dropped ref will fail the suite).
- Grade-5 tests and the `test_standards_catalog.py` catalog-shape test are unchanged
  (we add no new standards — the catalog already holds all 25).

## Part 6 — Documentation updates

- **`docs/shormann-ccss-alignment.md`** — update the Algebra 1 column: it now covers
  the full HS band on its own; note the intentional Alg 1 / Alg 2 overlap and the
  "taught but outside the catalog" Shormann topics. Correct the older statement that
  `HSN.Q.A.1` is uncovered (Algebra 1's measurement/units lessons cover it).

## Sequencing

1. **Structure (no new authoring):** `lesson_refs` schema/model/loader; rewrite
   `knowledge_map.yaml` to the 23-point map. Coverage → 25/25.
2. **Items:** author the calibrated item bank point-by-point against the eTextbook,
   then run the fidelity review pass.
3. **Wiring:** regenerate `sample_responses.yaml`; extend tests; update the alignment doc.

## Verification

- `uv run pytest` — full suite green, including the new fidelity and coverage checks.
- `uv run python -m engine.cli --curriculum curriculum/shormann_algebra_1 --coverage`
  → 25 / 25 (100%).
- `uv run python -m engine.cli --curriculum curriculum/shormann_algebra_1 \
  --responses curriculum/shormann_algebra_1/sample_responses.yaml --name Sam`
  → sensible status report + learning path over the new strands.

## Out of scope

- Changes to `engine/` beyond the optional `lesson_refs` field (no scoring/report/path
  changes).
- Adding new standards to the catalog (all 25 already exist).
- `curriculum/shormann_algebra_2` restructuring (a later, separate effort; this spec
  only touches Algebra 1 and the shared item schema/model).
- Copying eTextbook problems verbatim — items are original, calibrated to the source.
