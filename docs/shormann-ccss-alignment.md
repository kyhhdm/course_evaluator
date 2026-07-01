# Shormann Math (High School) → CCSS-Math Alignment

**Date:** 2026-07-02
**Scope:** Shormann Algebra 1 and Algebra 2 (each with integrated geometry).

## Credit structure

Shormann integrates geometry into its algebra courses; there is no standalone
Geometry course.

| Shormann course | Credits earned |
| --- | --- |
| Algebra 1 with Integrated Geometry | 1 Algebra 1 + 1/2 Geometry |
| Algebra 2 with Integrated Geometry | 1 Algebra 2 + 1/2 Geometry |
| **Both, combined** | **1 Algebra 1 + 1 Algebra 2 + 1 Geometry** |

Because the geometry credit is split across the two years, no single course maps
to a single CCSS "course." The alignment below is therefore by **CCSS conceptual
category**, which is how CCSS organizes high-school math (it does not assign
high-school standards to named courses).

## Important caveat

Shormann Math is **not** a Common Core curriculum. It is organized around the
concepts tested on the PSAT, SAT, ACT, CLEP, and AP exams. The crosswalk below is
an *informational* mapping we constructed, not a vendor claim of CCSS alignment.

## Category crosswalk

| CCSS HS category | Representative clusters | Shormann Algebra 1 | Shormann Algebra 2 |
| --- | --- | --- | --- |
| Number & Quantity (N) | N-Q, N-RN, N-CN | units; intro to exponents/radicals | rational exponents, radicals, complex numbers |
| Algebra (A) | A-SSE, A-APR, A-CED, A-REI | expressions, linear equations & systems, polynomials | quadratics, factoring/rewriting, rational & polynomial operations |
| Functions (F) | F-IF, F-BF, F-LE | function notation, graph features, linear models | exponential/log models, transformations |
| Geometry (G) | G-CO, G-SRT, G-C, G-GMD | definitions, perimeter/area/volume | triangle proofs, similarity, right-triangle trig, circles |
| Statistics & Probability (S) | S-ID | single-variable data displays | scatter plots, linear models, interpretation |

## Beyond CCSS (taught by Shormann, not in the CCSS high-school core)

A substantial part of Algebra 2 sits outside CCSS high-school math and is excluded
from the authored coverage:

- Calculus: limits, derivatives, integrals (lessons 20-22, 72-74, 98)
- Conic sections (lessons 67-68, 78)
- Non-Euclidean geometry (lesson 91)
- Vectors as taught here, and applied-science lessons (gas laws, chemical
  mixtures, Hardy-Weinberg)

These correspond to CCSS `(+)` advanced standards and to precalculus/calculus
content beyond CCSS entirely.

## How this maps into the evaluator

The CCSS high-school standards for the categories above are cataloged in
`standards/ccss_math.yaml` with `grade: "HS"`. The two authored courses
(`curriculum/shormann_algebra_1`, `curriculum/shormann_algebra_2`) reference their
slice of that band; run `--coverage` on either to see the covered/missing split.
Together the two courses cover 24 of the 25 standards in the band; one standard
(`CCSS.HSN.Q.A.1`, N-Q — modeling with units) remains intentionally uncovered by
the representative content.

## Sources

- Teacher's Guide for Shormann Algebra 2 (diveintomath.com) — full 100-lesson
  Course Sequence.
- Teacher's Guide for Shormann Algebra 1 (diveintomath.com) and the Algebra 1
  product page — course-level topic list.
- Dr. Shormann, "The New Shormann Math vs. Saxon Math and Common Core"
  (drshormann.com, 2015).
