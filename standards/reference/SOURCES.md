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
