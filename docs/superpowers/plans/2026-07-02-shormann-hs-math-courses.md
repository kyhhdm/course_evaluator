# Shormann HS Math Courses Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two high-school courses — Shormann Algebra 1 and Algebra 2 (each with integrated geometry) — modeled on the Shormann Math sequence, backed by a new CCSS high-school standards band and a Shormann→CCSS alignment report.

**Architecture:** Pure content work over the existing deterministic pipeline. High-school CCSS standards are added to the existing `standards/ccss_math.yaml` catalog tagged `grade: "HS"`; because the loader stringifies `grade` and coverage is a plain equality (`std.grade == meta.grade`), the two new courses (also `grade: "HS"`) get correct coverage with **zero engine changes**. Each course is four authored YAML files under `curriculum/`. Tests are extended by parametrizing the existing content-integrity suite over all courses and pinning the new HS catalog set.

**Tech Stack:** Python ≥3.10, `uv` for all execution, `pytest`, PyYAML + jsonschema (validation happens on load). No new dependencies.

## Global Constraints

- **Run everything via `uv run`** from the repo root (e.g. `uv run pytest`). Never call `pip` or edit `pyproject.toml` deps by hand.
- **No engine code changes.** Only `curriculum/`, `standards/`, `tests/`, and `docs/` are touched. Do not modify anything under `engine/` or `schemas/`.
- **New courses use `framework: CCSS-Math`, `grade: HS`.** The framework→catalog filename convention resolves `CCSS-Math` → `standards/ccss_math.yaml`, the same file the HS standards are added to.
- **Every knowledge point needs ≥2 diagnostic AND ≥2 practice items** (the integrity suite checks both). Every item carries an explicit `role: diagnostic` or `role: practice`.
- **No MCQ distractor may be numerically equal to the keyed answer** (ambiguous-distractor guard). Text-valued options like `"90 degrees"` are treated as non-numeric and are safe.
- **`(+)` advanced CCSS standards are excluded**, and Algebra 2's calculus/conics/non-Euclidean tail is out of scope for authored content.
- **Determinism:** authored content is order-stable; do not rely on set iteration for anything that reaches output.
- The existing 26 Grade-5 + 1 Grade-4 catalog entries and all existing tests must remain green and unchanged in meaning.

---

### Task 1: Add the CCSS high-school standards band to the catalog

**Files:**
- Modify: `standards/ccss_math.yaml` (append 25 HS entries)
- Test: `tests/test_standards_catalog.py` (add HS pin test)

**Interfaces:**
- Consumes: `load_catalog(path, schema)` → `dict[str, Standard]`, `Standard.grade` is a `str`.
- Produces: 25 catalog keys tagged `grade: "HS"`, framework `CCSS-Math`, used as `standard_refs` by Tasks 3 and 4. The canonical key set is `OFFICIAL_HS_CCSS_MATH` (below).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_standards_catalog.py`:

```python
# The curated CCSS high-school Math band this project authors HS courses against.
# Pins the catalog so any added/dropped/renamed HS code fails the build.
OFFICIAL_HS_CCSS_MATH = frozenset({
    "CCSS.HSN.Q.A.1", "CCSS.HSN.RN.A.2", "CCSS.HSN.CN.A.1", "CCSS.HSN.CN.C.7",
    "CCSS.HSA.SSE.A.1", "CCSS.HSA.SSE.B.3", "CCSS.HSA.APR.A.1", "CCSS.HSA.CED.A.1",
    "CCSS.HSA.REI.B.3", "CCSS.HSA.REI.B.4", "CCSS.HSA.REI.C.6",
    "CCSS.HSF.IF.A.1", "CCSS.HSF.IF.B.4", "CCSS.HSF.BF.B.3",
    "CCSS.HSF.LE.A.1", "CCSS.HSF.LE.A.2",
    "CCSS.HSG.CO.A.1", "CCSS.HSG.CO.C.10", "CCSS.HSG.SRT.A.2", "CCSS.HSG.SRT.C.8",
    "CCSS.HSG.C.A.2", "CCSS.HSG.GMD.A.3",
    "CCSS.HSS.ID.A.1", "CCSS.HSS.ID.B.6", "CCSS.HSS.ID.C.7",
})


def test_catalog_hs_codes_match_official_set():
    cat = load_catalog(CATALOG, SCHEMA)
    hs = {c for c, s in cat.items() if s.grade == "HS"}
    missing = OFFICIAL_HS_CCSS_MATH - hs
    extra = hs - OFFICIAL_HS_CCSS_MATH
    assert not missing, f"catalog is missing official HS codes: {sorted(missing)}"
    assert not extra, f"catalog has non-official HS codes: {sorted(extra)}"


def test_catalog_hs_entries_are_well_formed():
    cat = load_catalog(CATALOG, SCHEMA)
    for code in OFFICIAL_HS_CCSS_MATH:
        std = cat[code]
        assert std.framework == "CCSS-Math", code
        assert std.grade == "HS", code
        assert std.domain and std.description, code
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_standards_catalog.py::test_catalog_hs_codes_match_official_set -v`
Expected: FAIL — `catalog is missing official HS codes: [...]` (none exist yet).

- [ ] **Step 3: Add the HS standards to the catalog**

Append to the end of `standards/ccss_math.yaml` (keep it under the top-level `standards:` mapping — i.e. indented two spaces like the existing entries):

```yaml
  # --- High School: Number & Quantity ---
  CCSS.HSN.Q.A.1:
    framework: CCSS-Math
    grade: HS
    domain: Number & Quantity
    description: "Use units to guide the solution of problems; choose and interpret scale and the origin in graphs and data displays."
  CCSS.HSN.RN.A.2:
    framework: CCSS-Math
    grade: HS
    domain: Number & Quantity
    description: "Rewrite expressions involving radicals and rational exponents using the properties of exponents."
  CCSS.HSN.CN.A.1:
    framework: CCSS-Math
    grade: HS
    domain: Number & Quantity
    description: "Know there is a complex number i with i^2 = -1, and that every complex number has the form a + bi."
  CCSS.HSN.CN.C.7:
    framework: CCSS-Math
    grade: HS
    domain: Number & Quantity
    description: "Solve quadratic equations with real coefficients that have complex solutions."
  # --- High School: Algebra ---
  CCSS.HSA.SSE.A.1:
    framework: CCSS-Math
    grade: HS
    domain: Algebra
    description: "Interpret expressions that represent a quantity in terms of its context (terms, factors, and coefficients)."
  CCSS.HSA.SSE.B.3:
    framework: CCSS-Math
    grade: HS
    domain: Algebra
    description: "Choose and produce an equivalent form of an expression to reveal properties (factoring, completing the square)."
  CCSS.HSA.APR.A.1:
    framework: CCSS-Math
    grade: HS
    domain: Algebra
    description: "Add, subtract, and multiply polynomials; understand that polynomials form a closed system under these operations."
  CCSS.HSA.CED.A.1:
    framework: CCSS-Math
    grade: HS
    domain: Algebra
    description: "Create equations and inequalities in one variable and use them to solve problems."
  CCSS.HSA.REI.B.3:
    framework: CCSS-Math
    grade: HS
    domain: Algebra
    description: "Solve linear equations and inequalities in one variable."
  CCSS.HSA.REI.B.4:
    framework: CCSS-Math
    grade: HS
    domain: Algebra
    description: "Solve quadratic equations by inspection, completing the square, the quadratic formula, and factoring."
  CCSS.HSA.REI.C.6:
    framework: CCSS-Math
    grade: HS
    domain: Algebra
    description: "Solve systems of linear equations exactly and approximately, focusing on pairs in two variables."
  # --- High School: Functions ---
  CCSS.HSF.IF.A.1:
    framework: CCSS-Math
    grade: HS
    domain: Functions
    description: "Understand that a function assigns to each input exactly one output; use function notation."
  CCSS.HSF.IF.B.4:
    framework: CCSS-Math
    grade: HS
    domain: Functions
    description: "For a function that models a relationship, interpret key features of graphs and tables (intercepts, intervals, extrema)."
  CCSS.HSF.BF.B.3:
    framework: CCSS-Math
    grade: HS
    domain: Functions
    description: "Identify the effect on the graph of replacing f(x) by f(x)+k, k*f(x), f(kx), and f(x+k)."
  CCSS.HSF.LE.A.1:
    framework: CCSS-Math
    grade: HS
    domain: Functions
    description: "Distinguish between situations that can be modeled with linear functions and with exponential functions."
  CCSS.HSF.LE.A.2:
    framework: CCSS-Math
    grade: HS
    domain: Functions
    description: "Construct linear and exponential functions given a graph, a table, or a description of a relationship."
  # --- High School: Geometry ---
  CCSS.HSG.CO.A.1:
    framework: CCSS-Math
    grade: HS
    domain: Geometry
    description: "Know precise definitions of angle, circle, perpendicular line, parallel line, and line segment."
  CCSS.HSG.CO.C.10:
    framework: CCSS-Math
    grade: HS
    domain: Geometry
    description: "Prove theorems about triangles (e.g., angle sum, base angles of isosceles triangles, midsegment)."
  CCSS.HSG.SRT.A.2:
    framework: CCSS-Math
    grade: HS
    domain: Geometry
    description: "Use similarity transformations to decide whether triangles are similar; explain the AA similarity criterion."
  CCSS.HSG.SRT.C.8:
    framework: CCSS-Math
    grade: HS
    domain: Geometry
    description: "Use trigonometric ratios and the Pythagorean Theorem to solve right triangles in applied problems."
  CCSS.HSG.C.A.2:
    framework: CCSS-Math
    grade: HS
    domain: Geometry
    description: "Identify and describe relationships among inscribed angles, radii, and chords of a circle."
  CCSS.HSG.GMD.A.3:
    framework: CCSS-Math
    grade: HS
    domain: Geometry
    description: "Use volume formulas for cylinders, pyramids, cones, and spheres to solve problems."
  # --- High School: Statistics & Probability ---
  CCSS.HSS.ID.A.1:
    framework: CCSS-Math
    grade: HS
    domain: Statistics & Probability
    description: "Represent data with plots on the real number line (dot plots, histograms, and box plots)."
  CCSS.HSS.ID.B.6:
    framework: CCSS-Math
    grade: HS
    domain: Statistics & Probability
    description: "Represent data on two quantitative variables on a scatter plot and fit a function to the data."
  CCSS.HSS.ID.C.7:
    framework: CCSS-Math
    grade: HS
    domain: Statistics & Probability
    description: "Interpret the slope and the intercept of a linear model in the context of the data."
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_standards_catalog.py -v`
Expected: PASS — all catalog tests, including the two new HS tests and the unchanged Grade-5 tests.

- [ ] **Step 5: Commit**

```bash
git add standards/ccss_math.yaml tests/test_standards_catalog.py
git commit -m "content(standards): add CCSS high-school math band (grade HS)"
```

---

### Task 2: Parametrize the content-integrity suite over courses

This is a pure refactor: keep the suite covering only `grade5_math` (stays green), but restructure it to iterate a `COURSE_DIRS` list so later tasks can add courses.

**Files:**
- Modify: `tests/test_content_integrity.py` (full rewrite, same checks, parametrized)

**Interfaces:**
- Consumes: `load_course(dir, "schemas", "methodology", "standards")`, `load_yaml(path)`, `Curriculum.diagnostic_items_for_point`, `Curriculum.practice_items_for_point`.
- Produces: module-level `COURSE_DIRS` list (later tasks append to it) and a `curricula` fixture keyed by course dir.

- [ ] **Step 1: Rewrite the test file (behavior-preserving)**

Replace the entire contents of `tests/test_content_integrity.py` with:

```python
import pytest

from engine.loader import load_course, load_yaml

SCHEMAS_DIR = "schemas"
METHODOLOGY_DIR = "methodology"
STANDARDS_DIR = "standards"

# Courses covered by the content-integrity gate. Later courses are appended here.
COURSE_DIRS = [
    "curriculum/grade5_math",
]


@pytest.fixture(scope="module")
def curricula():
    return {
        d: load_course(d, SCHEMAS_DIR, METHODOLOGY_DIR, STANDARDS_DIR)
        for d in COURSE_DIRS
    }


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_prerequisites_reference_existing_points(course_dir, curricula):
    curriculum = curricula[course_dir]
    ids = set(curriculum.points)
    for p in curriculum.points.values():
        for pre in p.prerequisites:
            assert pre in ids, f"{course_dir}: {p.id} has unknown prerequisite {pre}"


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_no_prerequisite_cycles(course_dir, curricula):
    points = curricula[course_dir].points
    WHITE, GREY, BLACK = 0, 1, 2
    color = {pid: WHITE for pid in points}

    def visit(pid):
        color[pid] = GREY
        for pre in points[pid].prerequisites:
            if color[pre] == GREY:
                raise AssertionError(f"{course_dir}: cycle through {pid} -> {pre}")
            if color[pre] == WHITE:
                visit(pre)
        color[pid] = BLACK

    for pid in points:
        if color[pid] == WHITE:
            visit(pid)


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_every_point_has_at_least_two_diagnostic_items(course_dir, curricula):
    curriculum = curricula[course_dir]
    for pid in curriculum.points:
        assert len(curriculum.diagnostic_items_for_point(pid)) >= 2, \
            f"{course_dir}: {pid} has < 2 diagnostic items"


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_every_point_has_at_least_two_practice_items(course_dir, curricula):
    curriculum = curricula[course_dir]
    for pid in curriculum.points:
        assert len(curriculum.practice_items_for_point(pid)) >= 2, \
            f"{course_dir}: {pid} has < 2 practice items"


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_every_item_has_explicit_role(course_dir):
    raw = load_yaml(f"{course_dir}/item_bank.yaml")["items"]
    for it in raw:
        assert it.get("role") in ("diagnostic", "practice"), \
            f"{course_dir}: item {it['id']} is missing an explicit role"


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_every_item_references_existing_points(course_dir, curricula):
    curriculum = curricula[course_dir]
    ids = set(curriculum.points)
    for it in curriculum.items.values():
        for pid in it.points:
            assert pid in ids, f"{course_dir}: item {it.id} references unknown point {pid}"


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_every_standard_ref_exists_in_mapping(course_dir, curricula):
    curriculum = curricula[course_dir]
    codes = set(curriculum.standards)
    for p in curriculum.points.values():
        for ref in p.standard_refs:
            assert ref in codes, f"{course_dir}: {p.id} references unknown standard {ref}"


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_sample_responses_only_reference_real_items(course_dir, curricula):
    curriculum = curricula[course_dir]
    responses = load_yaml(f"{course_dir}/sample_responses.yaml")["responses"]
    for item_id in responses:
        assert item_id in curriculum.items, \
            f"{course_dir}: response references unknown item {item_id}"


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_mcq_options_have_no_duplicate_values(course_dir, curricula):
    def parse_option(s):
        s = str(s).strip()
        if "/" in s:
            parts = s.split("/")
            if len(parts) == 2:
                try:
                    return float(parts[0]) / float(parts[1])
                except (ValueError, ZeroDivisionError):
                    return None
        try:
            return float(s)
        except ValueError:
            return None

    for item in curricula[course_dir].items.values():
        if item.type != "mcq":
            continue
        option_pairs = []
        for key, val in item.options.items():
            numeric = parse_option(val)
            if numeric is not None:
                option_pairs.append((key, numeric, val))
        answer_key = getattr(item, "answer", None)
        answer_numeric = None
        if answer_key and answer_key in item.options:
            answer_numeric = parse_option(item.options[answer_key])
        if answer_numeric is not None:
            for key, val, raw in option_pairs:
                if key == answer_key:
                    continue
                assert abs(val - answer_numeric) >= 1e-9, (
                    f"{course_dir}: item {item.id}: distractor {key}='{raw}' is "
                    f"numerically equal to keyed answer {answer_key}="
                    f"'{item.options[answer_key]}'"
                )
```

- [ ] **Step 2: Run the suite to verify it still passes**

Run: `uv run pytest tests/test_content_integrity.py -v`
Expected: PASS — same checks as before, now shown as parametrized `[curriculum/grade5_math]` cases.

- [ ] **Step 3: Commit**

```bash
git add tests/test_content_integrity.py
git commit -m "test(content): parametrize content-integrity suite over courses"
```

---

### Task 3: Author Shormann Algebra 1 with Integrated Geometry

**Files:**
- Create: `curriculum/shormann_algebra_1/course.yaml`
- Create: `curriculum/shormann_algebra_1/knowledge_map.yaml`
- Create: `curriculum/shormann_algebra_1/item_bank.yaml`
- Create: `curriculum/shormann_algebra_1/sample_responses.yaml`
- Modify: `tests/test_content_integrity.py` (add course to `COURSE_DIRS`)

**Interfaces:**
- Consumes: HS catalog keys from Task 1; the parametrized suite from Task 2.
- Produces: course id `shormann_algebra_1`, points `a1-expr`, `a1-linear`, `a1-systems`, `a1-poly`, `a1-geometry`, `a1-data`; 24 items; sample responses covering all 24.

- [ ] **Step 1: Add the course to the test list (make it fail first)**

In `tests/test_content_integrity.py`, extend `COURSE_DIRS`:

```python
COURSE_DIRS = [
    "curriculum/grade5_math",
    "curriculum/shormann_algebra_1",
]
```

- [ ] **Step 2: Run the suite to verify it fails**

Run: `uv run pytest tests/test_content_integrity.py -v`
Expected: FAIL/ERROR — `load_course` can't find `curriculum/shormann_algebra_1/course.yaml`.

- [ ] **Step 3: Create the course manifest**

`curriculum/shormann_algebra_1/course.yaml`:

```yaml
id: shormann_algebra_1
name: Shormann Algebra 1 with Integrated Geometry
framework: CCSS-Math
grade: HS
```

- [ ] **Step 4: Create the knowledge map**

`curriculum/shormann_algebra_1/knowledge_map.yaml`:

```yaml
points:
  - id: a1-expr
    strand: Expressions & Equations
    title: Expressions and linear equations
    description: Interpret algebraic expressions and solve one-variable linear equations.
    prerequisites: []
    standard_refs: [CCSS.HSA.SSE.A.1, CCSS.HSA.CED.A.1, CCSS.HSA.REI.B.3]
  - id: a1-linear
    strand: Linear Functions & Graphing
    title: Linear functions and their graphs
    description: Use function notation and interpret slope and intercepts of linear functions.
    prerequisites: [a1-expr]
    standard_refs: [CCSS.HSF.IF.A.1, CCSS.HSF.IF.B.4, CCSS.HSF.LE.A.2]
  - id: a1-systems
    strand: Systems of Equations
    title: Systems of linear equations
    description: Solve pairs of linear equations in two variables.
    prerequisites: [a1-linear]
    standard_refs: [CCSS.HSA.REI.C.6]
  - id: a1-poly
    strand: Exponents & Polynomials
    title: Exponents and polynomial operations
    description: Apply exponent rules and add, subtract, and multiply polynomials.
    prerequisites: [a1-expr]
    standard_refs: [CCSS.HSA.APR.A.1, CCSS.HSN.RN.A.2]
  - id: a1-geometry
    strand: Integrated Geometry
    title: Geometry foundations and measurement
    description: Use precise definitions and compute perimeter, area, and volume.
    prerequisites: []
    standard_refs: [CCSS.HSG.CO.A.1, CCSS.HSG.GMD.A.3]
  - id: a1-data
    strand: Data & Probability
    title: Describing data
    description: Represent and summarize single-variable numeric data.
    prerequisites: []
    standard_refs: [CCSS.HSS.ID.A.1]
```

- [ ] **Step 5: Create the item bank**

`curriculum/shormann_algebra_1/item_bank.yaml`:

```yaml
items:
  # --- a1-expr ---
  - id: A1EXPR-D1
    role: diagnostic
    points: [a1-expr]
    difficulty: 1
    type: mcq
    prompt: "In the expression 3x + 7, what is the coefficient of x?"
    options: {A: "3", B: "7", C: "x", D: "10"}
    answer: "A"
    distractor_feedback: {B: "7 is the constant term, not the coefficient of x."}
  - id: A1EXPR-D2
    role: diagnostic
    points: [a1-expr]
    difficulty: 2
    type: numeric
    prompt: "Solve for x: 2x + 5 = 17. Enter x."
    answer: "6"
  - id: A1EXPR-P1
    role: practice
    points: [a1-expr]
    difficulty: 1
    type: mcq
    prompt: "Which equation models 'five more than twice a number n is 19'?"
    options: {A: "2n + 5 = 19", B: "5n + 2 = 19", C: "2n - 5 = 19", D: "2(n + 5) = 19"}
    answer: "A"
  - id: A1EXPR-P2
    role: practice
    points: [a1-expr]
    difficulty: 2
    type: numeric
    prompt: "Solve for x: 3(x - 4) = 18. Enter x."
    answer: "10"
  # --- a1-linear ---
  - id: A1LIN-D1
    role: diagnostic
    points: [a1-linear]
    difficulty: 1
    type: mcq
    prompt: "What is the slope of the line y = 4x - 3?"
    options: {A: "4", B: "-3", C: "3", D: "1/4"}
    answer: "A"
  - id: A1LIN-D2
    role: diagnostic
    points: [a1-linear]
    difficulty: 2
    type: mcq
    prompt: "What is the y-intercept of the line y = 4x - 3?"
    options: {A: "-3", B: "4", C: "3", D: "0"}
    answer: "A"
  - id: A1LIN-P1
    role: practice
    points: [a1-linear]
    difficulty: 2
    type: numeric
    prompt: "For f(x) = 2x + 1, what is f(5)?"
    answer: "11"
  - id: A1LIN-P2
    role: practice
    points: [a1-linear]
    difficulty: 2
    type: mcq
    prompt: "A line passes through (0, 2) with slope 3. Which equation is it?"
    options: {A: "y = 3x + 2", B: "y = 2x + 3", C: "y = 3x - 2", D: "y = x + 3"}
    answer: "A"
  # --- a1-systems ---
  - id: A1SYS-D1
    role: diagnostic
    points: [a1-systems]
    difficulty: 2
    type: mcq
    prompt: "Solve the system y = x + 1 and y = 2x - 1. What is x?"
    options: {A: "2", B: "1", C: "3", D: "-2"}
    answer: "A"
  - id: A1SYS-D2
    role: diagnostic
    points: [a1-systems]
    difficulty: 2
    type: numeric
    prompt: "For the system x + y = 10 and x - y = 4, what is x?"
    answer: "7"
  - id: A1SYS-P1
    role: practice
    points: [a1-systems]
    difficulty: 3
    type: numeric
    prompt: "For the system x + y = 10 and x - y = 4, what is y?"
    answer: "3"
  - id: A1SYS-P2
    role: practice
    points: [a1-systems]
    difficulty: 2
    type: mcq
    prompt: "How many solutions does a system of two parallel, non-identical lines have?"
    options: {A: "None", B: "One", C: "Two", D: "Infinitely many"}
    answer: "A"
  # --- a1-poly ---
  - id: A1POLY-D1
    role: diagnostic
    points: [a1-poly]
    difficulty: 1
    type: mcq
    prompt: "Simplify x^2 * x^3."
    options: {A: "x^5", B: "x^6", C: "x^1", D: "2x^5"}
    answer: "A"
  - id: A1POLY-D2
    role: diagnostic
    points: [a1-poly]
    difficulty: 2
    type: mcq
    prompt: "Add (2x + 3) + (5x - 1)."
    options: {A: "7x + 2", B: "7x + 4", C: "10x - 3", D: "7x - 2"}
    answer: "A"
  - id: A1POLY-P1
    role: practice
    points: [a1-poly]
    difficulty: 1
    type: numeric
    prompt: "Evaluate 2^5."
    answer: "32"
  - id: A1POLY-P2
    role: practice
    points: [a1-poly]
    difficulty: 2
    type: mcq
    prompt: "Multiply (x + 2)(x + 3)."
    options: {A: "x^2 + 5x + 6", B: "x^2 + 6x + 6", C: "x^2 + 5x + 5", D: "x^2 + 6"}
    answer: "A"
  # --- a1-geometry ---
  - id: A1GEO-D1
    role: diagnostic
    points: [a1-geometry]
    difficulty: 1
    type: mcq
    prompt: "Two lines that never meet and stay the same distance apart are called:"
    options: {A: "parallel", B: "perpendicular", C: "intersecting", D: "skew"}
    answer: "A"
  - id: A1GEO-D2
    role: diagnostic
    points: [a1-geometry]
    difficulty: 2
    type: numeric
    prompt: "A rectangular box measures 2 by 3 by 4. What is its volume?"
    answer: "24"
  - id: A1GEO-P1
    role: practice
    points: [a1-geometry]
    difficulty: 1
    type: mcq
    prompt: "Perpendicular lines meet at an angle of:"
    options: {A: "90 degrees", B: "45 degrees", C: "180 degrees", D: "60 degrees"}
    answer: "A"
  - id: A1GEO-P2
    role: practice
    points: [a1-geometry]
    difficulty: 2
    type: numeric
    prompt: "A cube has side length 3. What is its volume?"
    answer: "27"
  # --- a1-data ---
  - id: A1DATA-D1
    role: diagnostic
    points: [a1-data]
    difficulty: 1
    type: numeric
    prompt: "Find the mean of 4, 6, 8, and 10."
    answer: "7"
  - id: A1DATA-D2
    role: diagnostic
    points: [a1-data]
    difficulty: 2
    type: mcq
    prompt: "Which display best shows the distribution of a single numeric variable?"
    options: {A: "histogram", B: "scatter plot", C: "pie chart of names", D: "road map"}
    answer: "A"
  - id: A1DATA-P1
    role: practice
    points: [a1-data]
    difficulty: 1
    type: numeric
    prompt: "Find the median of 3, 5, and 9."
    answer: "5"
  - id: A1DATA-P2
    role: practice
    points: [a1-data]
    difficulty: 2
    type: mcq
    prompt: "What is the range of the data set 2, 5, 9?"
    options: {A: "7", B: "9", C: "2", D: "5"}
    answer: "A"
```

- [ ] **Step 6: Create the sample responses**

`curriculum/shormann_algebra_1/sample_responses.yaml` (mostly correct, two intentional misses at A1SYS-D1 and A1DATA-P2 so the report shows a non-trivial path):

```yaml
responses:
  A1EXPR-D1: "A"
  A1EXPR-D2: "6"
  A1EXPR-P1: "A"
  A1EXPR-P2: "10"
  A1LIN-D1: "A"
  A1LIN-D2: "A"
  A1LIN-P1: "11"
  A1LIN-P2: "A"
  A1SYS-D1: "B"
  A1SYS-D2: "7"
  A1SYS-P1: "3"
  A1SYS-P2: "A"
  A1POLY-D1: "A"
  A1POLY-D2: "A"
  A1POLY-P1: "32"
  A1POLY-P2: "A"
  A1GEO-D1: "A"
  A1GEO-D2: "24"
  A1GEO-P1: "A"
  A1GEO-P2: "27"
  A1DATA-D1: "7"
  A1DATA-D2: "A"
  A1DATA-P1: "5"
  A1DATA-P2: "C"
```

- [ ] **Step 7: Run the content-integrity suite to verify it passes**

Run: `uv run pytest tests/test_content_integrity.py -v`
Expected: PASS — both `[curriculum/grade5_math]` and `[curriculum/shormann_algebra_1]` parametrized cases green.

- [ ] **Step 8: Smoke-test the CLI (coverage + evaluation)**

Run: `uv run python -m engine.cli --curriculum curriculum/shormann_algebra_1 --coverage`
Expected: a coverage report reading `Coverage: CCSS-Math grade HS`, showing 12 of 25 covered (~48%) with the uncovered HS codes listed under Missing.

Run: `uv run python -m engine.cli --curriculum curriculum/shormann_algebra_1 --responses curriculum/shormann_algebra_1/sample_responses.yaml --name Sam`
Expected: a parent status report (strands + knowledge points) and a learning path, with no errors.

- [ ] **Step 9: Commit**

```bash
git add curriculum/shormann_algebra_1 tests/test_content_integrity.py
git commit -m "content(course): add Shormann Algebra 1 with Integrated Geometry"
```

---

### Task 4: Author Shormann Algebra 2 with Integrated Geometry

**Files:**
- Create: `curriculum/shormann_algebra_2/course.yaml`
- Create: `curriculum/shormann_algebra_2/knowledge_map.yaml`
- Create: `curriculum/shormann_algebra_2/item_bank.yaml`
- Create: `curriculum/shormann_algebra_2/sample_responses.yaml`
- Modify: `tests/test_content_integrity.py` (add course to `COURSE_DIRS`)

**Interfaces:**
- Consumes: HS catalog keys from Task 1; the parametrized suite from Task 2.
- Produces: course id `shormann_algebra_2`, points `a2-quadratics`, `a2-poly-rational`, `a2-exp-log`, `a2-radicals-complex`, `a2-geometry`, `a2-stats`; 24 items; sample responses covering all 24. Drawn from Algebra 2's algebra/functions/geometry-proof/statistics lessons, not its calculus/conics tail.

- [ ] **Step 1: Add the course to the test list (make it fail first)**

In `tests/test_content_integrity.py`, extend `COURSE_DIRS`:

```python
COURSE_DIRS = [
    "curriculum/grade5_math",
    "curriculum/shormann_algebra_1",
    "curriculum/shormann_algebra_2",
]
```

- [ ] **Step 2: Run the suite to verify it fails**

Run: `uv run pytest tests/test_content_integrity.py -v`
Expected: FAIL/ERROR — `load_course` can't find `curriculum/shormann_algebra_2/course.yaml`.

- [ ] **Step 3: Create the course manifest**

`curriculum/shormann_algebra_2/course.yaml`:

```yaml
id: shormann_algebra_2
name: Shormann Algebra 2 with Integrated Geometry
framework: CCSS-Math
grade: HS
```

- [ ] **Step 4: Create the knowledge map**

`curriculum/shormann_algebra_2/knowledge_map.yaml`:

```yaml
points:
  - id: a2-quadratics
    strand: Quadratic Functions
    title: Quadratic equations and complex roots
    description: Solve quadratics by factoring and formula, including cases with complex solutions.
    prerequisites: []
    standard_refs: [CCSS.HSA.REI.B.4, CCSS.HSA.SSE.B.3, CCSS.HSN.CN.C.7]
  - id: a2-poly-rational
    strand: Polynomial & Rational Expressions
    title: Polynomial and rational expressions
    description: Multiply and factor polynomials and simplify rational expressions.
    prerequisites: [a2-quadratics]
    standard_refs: [CCSS.HSA.APR.A.1, CCSS.HSA.SSE.B.3]
  - id: a2-exp-log
    strand: Exponential & Logarithmic Functions
    title: Exponential functions and growth
    description: Distinguish and construct exponential models and transform their graphs.
    prerequisites: []
    standard_refs: [CCSS.HSF.LE.A.1, CCSS.HSF.LE.A.2, CCSS.HSF.BF.B.3]
  - id: a2-radicals-complex
    strand: Radicals & Complex Numbers
    title: Radicals and complex numbers
    description: Simplify radicals and rational exponents and work with complex numbers.
    prerequisites: []
    standard_refs: [CCSS.HSN.RN.A.2, CCSS.HSN.CN.A.1]
  - id: a2-geometry
    strand: Integrated Geometry
    title: Similarity, right-triangle trig, and circles
    description: Prove triangle theorems and use similarity, right-triangle trig, and circle relationships.
    prerequisites: []
    standard_refs: [CCSS.HSG.SRT.A.2, CCSS.HSG.SRT.C.8, CCSS.HSG.C.A.2, CCSS.HSG.CO.C.10]
  - id: a2-stats
    strand: Statistics & Inference
    title: Bivariate data and linear models
    description: Fit and interpret linear models for two-variable data.
    prerequisites: []
    standard_refs: [CCSS.HSS.ID.B.6, CCSS.HSS.ID.C.7]
```

- [ ] **Step 5: Create the item bank**

`curriculum/shormann_algebra_2/item_bank.yaml`:

```yaml
items:
  # --- a2-quadratics ---
  - id: A2QUAD-D1
    role: diagnostic
    points: [a2-quadratics]
    difficulty: 2
    type: numeric
    prompt: "Solve x^2 = 49. Enter the positive solution."
    answer: "7"
  - id: A2QUAD-D2
    role: diagnostic
    points: [a2-quadratics]
    difficulty: 2
    type: mcq
    prompt: "Factor x^2 + 5x + 6."
    options: {A: "(x + 2)(x + 3)", B: "(x + 1)(x + 6)", C: "(x + 2)(x + 4)", D: "(x - 2)(x - 3)"}
    answer: "A"
  - id: A2QUAD-P1
    role: practice
    points: [a2-quadratics]
    difficulty: 3
    type: mcq
    prompt: "Solve x^2 + 1 = 0 over the complex numbers."
    options: {A: "x = +/- i", B: "x = +/- 1", C: "x = 0", D: "no solution exists"}
    answer: "A"
  - id: A2QUAD-P2
    role: practice
    points: [a2-quadratics]
    difficulty: 2
    type: numeric
    prompt: "One root of x^2 - 7x + 12 = 0 is 3. What is the other root?"
    answer: "4"
  # --- a2-poly-rational ---
  - id: A2POLY-D1
    role: diagnostic
    points: [a2-poly-rational]
    difficulty: 2
    type: mcq
    prompt: "Multiply (x + 4)(x - 4)."
    options: {A: "x^2 - 16", B: "x^2 + 16", C: "x^2 - 8x - 16", D: "x^2 - 8"}
    answer: "A"
  - id: A2POLY-D2
    role: diagnostic
    points: [a2-poly-rational]
    difficulty: 2
    type: mcq
    prompt: "Simplify (x^2 - 9)/(x - 3) for x not equal to 3."
    options: {A: "x + 3", B: "x - 3", C: "x^2 - 3", D: "x + 9"}
    answer: "A"
  - id: A2POLY-P1
    role: practice
    points: [a2-poly-rational]
    difficulty: 2
    type: mcq
    prompt: "Factor completely: x^2 - 6x + 9."
    options: {A: "(x - 3)^2", B: "(x + 3)^2", C: "(x - 3)(x + 3)", D: "(x - 9)(x - 1)"}
    answer: "A"
  - id: A2POLY-P2
    role: practice
    points: [a2-poly-rational]
    difficulty: 2
    type: numeric
    prompt: "Evaluate the polynomial x^2 - 2x + 1 at x = 5."
    answer: "16"
  # --- a2-exp-log ---
  - id: A2EXP-D1
    role: diagnostic
    points: [a2-exp-log]
    difficulty: 2
    type: mcq
    prompt: "Which function is exponential?"
    options: {A: "y = 2^x", B: "y = 2x", C: "y = x^2", D: "y = 2x + 1"}
    answer: "A"
  - id: A2EXP-D2
    role: diagnostic
    points: [a2-exp-log]
    difficulty: 2
    type: numeric
    prompt: "Evaluate 3^4."
    answer: "81"
  - id: A2EXP-P1
    role: practice
    points: [a2-exp-log]
    difficulty: 2
    type: numeric
    prompt: "A population starts at 500 and doubles each year. What is it after 2 years?"
    answer: "2000"
  - id: A2EXP-P2
    role: practice
    points: [a2-exp-log]
    difficulty: 3
    type: mcq
    prompt: "The graph of y = 2^x + 3 is the graph of y = 2^x shifted:"
    options: {A: "up 3", B: "down 3", C: "right 3", D: "left 3"}
    answer: "A"
  # --- a2-radicals-complex ---
  - id: A2RAD-D1
    role: diagnostic
    points: [a2-radicals-complex]
    difficulty: 1
    type: numeric
    prompt: "Simplify the square root of 64."
    answer: "8"
  - id: A2RAD-D2
    role: diagnostic
    points: [a2-radicals-complex]
    difficulty: 2
    type: mcq
    prompt: "Rewrite 8^(1/3) as an integer."
    options: {A: "2", B: "4", C: "3", D: "8"}
    answer: "A"
  - id: A2RAD-P1
    role: practice
    points: [a2-radicals-complex]
    difficulty: 2
    type: mcq
    prompt: "What is i^2?"
    options: {A: "-1", B: "1", C: "i", D: "-i"}
    answer: "A"
  - id: A2RAD-P2
    role: practice
    points: [a2-radicals-complex]
    difficulty: 2
    type: numeric
    prompt: "Write the square root of 50 as k times the square root of 2. What is k?"
    answer: "5"
  # --- a2-geometry ---
  - id: A2GEO-D1
    role: diagnostic
    points: [a2-geometry]
    difficulty: 2
    type: numeric
    prompt: "A right triangle has legs 3 and 4. What is the length of the hypotenuse?"
    answer: "5"
  - id: A2GEO-D2
    role: diagnostic
    points: [a2-geometry]
    difficulty: 2
    type: mcq
    prompt: "Two triangles with two pairs of congruent angles are always:"
    options: {A: "similar", B: "congruent", C: "unrelated", D: "equilateral"}
    answer: "A"
  - id: A2GEO-P1
    role: practice
    points: [a2-geometry]
    difficulty: 2
    type: numeric
    prompt: "A right triangle has legs 6 and 8. What is the length of the hypotenuse?"
    answer: "10"
  - id: A2GEO-P2
    role: practice
    points: [a2-geometry]
    difficulty: 3
    type: mcq
    prompt: "An inscribed angle that subtends a diameter (semicircle) measures:"
    options: {A: "90 degrees", B: "45 degrees", C: "180 degrees", D: "60 degrees"}
    answer: "A"
  # --- a2-stats ---
  - id: A2STAT-D1
    role: diagnostic
    points: [a2-stats]
    difficulty: 2
    type: mcq
    prompt: "On a scatter plot, a line of best fit is used to:"
    options: {A: "model the trend between two variables", B: "list the raw data", C: "sort names alphabetically", D: "draw a circle"}
    answer: "A"
  - id: A2STAT-D2
    role: diagnostic
    points: [a2-stats]
    difficulty: 2
    type: mcq
    prompt: "In the linear model y = 3x + 5, the slope 3 represents:"
    options: {A: "the rate of change of y per unit x", B: "the starting value of y", C: "the value of y when x = 5", D: "the total of the data"}
    answer: "A"
  - id: A2STAT-P1
    role: practice
    points: [a2-stats]
    difficulty: 2
    type: numeric
    prompt: "In the linear model y = 3x + 5, what is y when x = 4?"
    answer: "17"
  - id: A2STAT-P2
    role: practice
    points: [a2-stats]
    difficulty: 2
    type: numeric
    prompt: "In the linear model y = 3x + 5, what is the y-intercept?"
    answer: "5"
```

- [ ] **Step 6: Create the sample responses**

`curriculum/shormann_algebra_2/sample_responses.yaml` (mostly correct, one intentional miss at A2STAT-D2):

```yaml
responses:
  A2QUAD-D1: "7"
  A2QUAD-D2: "A"
  A2QUAD-P1: "A"
  A2QUAD-P2: "4"
  A2POLY-D1: "A"
  A2POLY-D2: "A"
  A2POLY-P1: "A"
  A2POLY-P2: "16"
  A2EXP-D1: "A"
  A2EXP-D2: "81"
  A2EXP-P1: "2000"
  A2EXP-P2: "A"
  A2RAD-D1: "8"
  A2RAD-D2: "A"
  A2RAD-P1: "A"
  A2RAD-P2: "5"
  A2GEO-D1: "5"
  A2GEO-D2: "A"
  A2GEO-P1: "10"
  A2GEO-P2: "A"
  A2STAT-D1: "A"
  A2STAT-D2: "B"
  A2STAT-P1: "17"
  A2STAT-P2: "5"
```

- [ ] **Step 7: Run the content-integrity suite to verify it passes**

Run: `uv run pytest tests/test_content_integrity.py -v`
Expected: PASS — all three parametrized course cases green.

- [ ] **Step 8: Smoke-test the CLI (coverage + evaluation)**

Run: `uv run python -m engine.cli --curriculum curriculum/shormann_algebra_2 --coverage`
Expected: `Coverage: CCSS-Math grade HS`, 15 of 25 covered (~60%), with the rest under Missing.

Run: `uv run python -m engine.cli --curriculum curriculum/shormann_algebra_2 --responses curriculum/shormann_algebra_2/sample_responses.yaml --name Sam`
Expected: a parent status report and learning path, no errors.

- [ ] **Step 9: Commit**

```bash
git add curriculum/shormann_algebra_2 tests/test_content_integrity.py
git commit -m "content(course): add Shormann Algebra 2 with Integrated Geometry"
```

---

### Task 5: Write the Shormann→CCSS alignment report

**Files:**
- Create: `docs/shormann-ccss-alignment.md`

**Interfaces:**
- Consumes: the scope captured in the design spec and the HS catalog from Task 1.
- Produces: the human-readable alignment deliverable (Part A of the spec).

- [ ] **Step 1: Write the report**

Create `docs/shormann-ccss-alignment.md` with exactly this content:

```markdown
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
Together the two courses cover most of the band; a few standards (e.g. `N-Q`)
remain intentionally uncovered by the representative content.

## Sources

- Teacher's Guide for Shormann Algebra 2 (diveintomath.com) — full 100-lesson
  Course Sequence.
- Teacher's Guide for Shormann Algebra 1 (diveintomath.com) and the Algebra 1
  product page — course-level topic list.
- Dr. Shormann, "The New Shormann Math vs. Saxon Math and Common Core"
  (drshormann.com, 2015).
```

- [ ] **Step 2: Verify the full test suite is green**

Run: `uv run pytest`
Expected: PASS — entire suite, including the new HS catalog and parametrized content-integrity cases.

- [ ] **Step 3: Commit**

```bash
git add docs/shormann-ccss-alignment.md
git commit -m "docs: add Shormann to CCSS high-school alignment report"
```

---

## Notes for the executor

- **Coverage counts are guidance, not asserted.** The "12 of 25" / "15 of 25"
  figures in Steps 8 are the expected result of the authored `standard_refs`;
  if you change the referenced codes, recompute rather than forcing the number.
- **If an MCQ edit introduces a numeric distractor**, re-check it against the
  keyed answer — the ambiguity guard in `test_content_integrity.py` will fail
  the build otherwise. Text options such as `"90 degrees"` are safe.
- **No `bands.yaml`** is added to either course; both correctly fall back to
  `methodology/bands.yaml`.
```
