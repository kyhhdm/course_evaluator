# Standards sources

Authoritative source documents that `standards/*.yaml` is derived from and verified against.

## CCSS-Math (`../ccss_math.yaml`)

- **`CCSS_Math_Standards_full.pdf`** — *Common Core State Standards for Mathematics*, the
  complete K-12 standards document. Primary source.
  Retrieved 2026-06-26 from
  <https://www.thecorestandards.org/wp-content/uploads/Math_Standards1.pdf>
- **`CCSS_Math_Grade5_Oregon_ODE.pdf`** — Oregon Department of Education's verbatim
  reproduction of the CCSS Mathematics standards, Grade 5 (the focused copy used to
  verify the Grade-5 entries line by line).
  Retrieved 2026-06-26 from
  <https://www.oregon.gov/ode/educator-resources/standards/mathematics/Documents/ccssm5.pdf>

The CCSS mathematics standards were adopted in 2010 and have not been revised since, so
these are the current, stable text. © NGA Center for Best Practices & CCSSO; reproduced
for reference under the CCSS public license (attribution required, which this note provides).

## Shormann Math — high-school course scope

Source documents for the **Shormann Algebra 1 & 2 courses** (`../../curriculum/shormann_algebra_1`,
`../../curriculum/shormann_algebra_2`) and the crosswalk in
`../../docs/shormann-ccss-alignment.md`. These describe the vendor's course scope; they are
*not* a CCSS source (Shormann is not Common Core) and were used only to model the courses'
strands/knowledge points, not to verify `ccss_math.yaml`.

- **`Shormann_Algebra1_TeacherGuide.pdf`** — *Teacher Guide for Shormann Algebra 1 with
  Integrated Geometry*. Course-level scope, credits (1 Algebra 1 + ½ Geometry), and schedule.
  Retrieved 2026-07-02 from
  <https://diveintomath.com/content/Teacher's%20Guides/Teacher%20Guide%20for%20Shormann%20Algebra%201.pdf>
- **`Shormann_Algebra2_TeacherGuide.pdf`** — *Teacher Guide for Shormann Algebra 2 with
  Integrated Geometry*. Contains the full **100-lesson Course Sequence table** (the
  authoritative lesson-level scope) plus credits (1 Algebra 2 + ½ Geometry).
  Retrieved 2026-07-02 from
  <https://diveintomath.com/content/Teacher's%20Guides/Teacher%20Guide%20for%20Shormann%20Algebra%202.pdf>
- **`Shormann_Algebra2_ScopeAndSequence.pdf`** — DIVE's published *Scope and Sequence for
  Shormann Algebra 2 with Integrated Geometry*: a granular topic outline (Arithmetic →
  Whole Numbers → Fractions → …). Complements the Teacher Guide's lesson table.
  Retrieved 2026-07-02 from diveintomath.com's Scope & Sequence resources.

The Algebra 1 lesson-by-lesson scope is coarser than Algebra 2's because Algebra 1's Teacher
Guide carries a course-level description rather than a lesson table, and DIVE's online
Algebra 1 Scope & Sequence article blocks automated retrieval (HTTP 403). © Digital
Interactive Video Education (DIVE / diveintomath.com); reproduced here for reference.

## Verification

`standards/ccss_math.yaml` was cross-checked against the documents above: all 26 Grade-5
codes are present with correct domain/cluster letters and faithful descriptions, plus the
grade-4 prerequisite `CCSS.4.NF.A.1`. The exact canonical code set is pinned by
`tests/test_standards_catalog.py::test_catalog_grade5_codes_match_official_set`, which fails
if any code is added, dropped, or renamed. To re-verify descriptions after an edit, compare
against the PDFs here.

### Code notation

Catalog keys use the cluster-letter dot form (`CCSS.5.NF.A.1`). The same standards appear
elsewhere as plain numbering (`5.NF.1`, e.g. in the Oregon PDF) or fully-qualified
(`CCSS.MATH.CONTENT.5.NF.A.1`). All denote the same standard; confirm the expected form
before integrating with another system.
