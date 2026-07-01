# Task 10 Report: Wiring — sample responses, coverage lock, alignment doc

**Date:** 2026-07-02
**Commit:** 9938eaa — "test(alg1): lock 25/25 coverage; refresh sample responses and alignment doc"

---

## 1. Sample Responses Spread

Designed to cover all 23 knowledge points across 8 strands with a realistic mix:

| Point | Answers given | Strategy |
|---|---|---|
| a1-num-realnum | all 4 | all correct |
| a1-num-exprad | all 4 | all correct |
| a1-num-units | all 4 | all correct |
| a1-expr-interpret | all 4 | ~50% correct |
| a1-expr-model | all 4 | ~50% correct |
| a1-expr-linear | all 4 | ~50% correct |
| a1-poly-ops | all 4 | all correct |
| a1-poly-factor | all 4 | all correct |
| a1-quad-solve | all 4 | ~50% correct |
| a1-complex | all 4 | ~50% correct |
| a1-func-concept | all 4 | ~50% correct |
| a1-func-graph | all 4 | ~50% correct |
| a1-func-linexp | 1 only | insufficient_evidence (< 2 items) |
| a1-geo-def | all 4 | all correct |
| a1-geo-proof | all 4 | ~50% correct |
| a1-geo-circle | all 4 | all correct |
| a1-geo-sim | all 4 | ~50% correct |
| a1-geo-trig | all 4 | all correct |
| a1-geo-measure | all 4 | ~50% correct |
| a1-systems | all 4 | all correct |
| a1-data-display | all 4 | ~75% correct |
| a1-data-scatter | all 4 | ~75% correct |
| a1-data-interpret | all 4 | all correct |

### Resulting CLI output (per-strand bands)

| Strand | Band |
|---|---|
| Number, Ratio & Quantity | Secure |
| Expressions & Equations | Not yet |
| Polynomials & Quadratics | Developing |
| Functions & Modeling | Not yet (+ 1 insufficient_evidence) |
| Geometry: Reasoning & Proof | Developing |
| Geometry: Similarity, Trig & Measurement | Developing |
| Systems of Equations | Secure |
| Data, Statistics & Probability | Developing |

Requirements met:
- At least one Secure strand: Number, Ratio & Quantity and Systems of Equations
- At least one Developing strand: Polynomials, Geometry (both), Data
- At least one insufficient_evidence: a1-func-linexp (only 1 item answered)

---

## 2. Coverage-Lock Test

Added `test_shormann_alg1_full_coverage` to `tests/test_coverage.py`.
Result: PASSED immediately (25/25 coverage already in place).
CLI confirmed: 25 / 25 standards covered (100.0%).
Full suite: 125 passed in 3.93s.

---

## 3. Alignment Doc Updates (docs/shormann-ccss-alignment.md)

Changes to the "How this maps into the evaluator" section:

- Corrected false claim that "Together the two courses cover 24 of the 25 standards" — Algebra 1 alone now covers all 25 (100.0%).
- Corrected false claim that CCSS.HSN.Q.A.1 is uncovered — it is covered by a1-num-units.
- Added note that several standards are intentionally referenced by both Algebra 1 and Algebra 2 (deliberate overlap by design).
- Added one-line note that Shormann Algebra 1 teaches topics outside CCSS (history of math, intro calculus, computer/binary math, Punnett squares/gas laws) left without standard_refs.

---

## Final Polish Pass (commit 78c954b)

**Date:** 2026-07-02

### Fix 1 — New empty-standard_refs guard test
Added `test_shormann_alg1_only_foundational_point_has_no_standard` to `tests/test_content_integrity.py`. Asserts that the set of knowledge-point ids with empty `standard_refs` in `curriculum/shormann_algebra_1` is exactly `{"a1-num-realnum"}`. This re-establishes the accidental-empty guard at the content layer after the schema relaxation that allowed `standard_refs: []` for the foundational point.

### Fix 2 — A1CPLX-D2 distractor rewrite (x²+1=0, roots i and -i)
Old options: A="i and -i", B="1 and -1", C="sqrt(1) and -sqrt(1)", D="i and i"
- Problem: D="i and i" is a nonsense repeat; C="sqrt(1) and -sqrt(1)"=B="1 and -1" (value-equivalent)

New options: A="i and -i" (key), B="1 and -1", C="i and 1", D="2i and -2i"
- Distinctness check: A=±i (complex roots), B=±1 (real), C={i,1} (mixed), D=±2i (wrong magnitude)
- Only A satisfies x²+1=0: i²+1=−1+1=0 ✓, (−i)²+1=−1+1=0 ✓
- B: 1²+1=2≠0, C: i²+1=0 (i is a root, but "i and 1" has 1 which is not), actually as a set-answer "i and 1" is wrong because 1 is not a root. D: (2i)²+1=−4+1=−3≠0 ✓ all distractors are wrong

### Fix 3 — A1CPLX-P1 distractor rewrite (x²+4=0, roots 2i and -2i)
Old options: A="2i and -2i", B="4i and -4i", C="2 and -2", D="sqrt(4) and -sqrt(4)"
- Problem: C="2 and -2", D="sqrt(4) and -sqrt(4)"="2 and -2" (value-equivalent)

New options: A="2i and -2i" (key), B="4i and -4i", C="2 and -2", D="2i and 2"
- Distinctness check: A=±2i, B=±4i, C=±2 (real), D={2i, 2} (mixed)
- Only A satisfies x²+4=0: (2i)²+4=−4+4=0 ✓, (−2i)²+4=−4+4=0 ✓
- B: (4i)²+4=−16+4=−12≠0 ✓, C: 2²+4=8≠0 ✓, D: 2²+4=8≠0 (2 not a root) ✓

### Fix 4 — A1GPRF-P2: "AAAS" → "AAS"
Changed distractor D in A1GPRF-P2 from `"AAAS"` to `"AAS"` (standard geometry congruence abbreviation; still wrong for a SAS scenario).

### Fix 5 — A1FLE-P1: lesson_refs [48] → [81]
Changed `lesson_refs: [48]` to `lesson_refs: [81]` for A1FLE-P1 (linear-vs-exponential LE.A.1 item). Lesson 81 is within the allowed set {48,81} for `a1-func-linexp` and better matches the item's content about exponential growth.

### Fix 6 — test_coverage.py: remove redundant inline import
Removed `from engine.coverage import compute_coverage` from inside `test_shormann_alg1_full_coverage` — `compute_coverage` is already imported at module level (line 4). Matches the style of sibling tests.

### Test results
- `uv run pytest tests/test_content_integrity.py tests/test_coverage.py -v`: 34/34 passed
- `uv run python -m engine.cli --curriculum curriculum/shormann_algebra_1 --coverage`: 25/25 (100.0%)
- `uv run pytest` (full suite): 126/126 passed
