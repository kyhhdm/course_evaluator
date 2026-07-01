# Shormann Algebra 1 Full-Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure `curriculum/shormann_algebra_1` into 8 strands / 23 knowledge points that cover all 25 HS CCSS standards, with a diagnostic + practice item bank calibrated to the Shormann eTextbook and traceable to the lessons it draws from.

**Architecture:** Add one optional `lesson_refs` field to the item model/schema/loader, then rebuild the course's `knowledge_map.yaml` + `item_bank.yaml` incrementally — one strand per task — so the content-integrity suite stays green after every task. Items are authored (original, not copied) against specific eTextbook lessons and tagged with `lesson_refs`; a new test enforces that every item cites a lesson consistent with its knowledge point.

**Tech Stack:** Python 3.10+, `uv` for env/execution, `pytest`, `pyyaml`, `jsonschema`, `jinja2`. Content is authored YAML validated against JSON Schema at load time.

## Global Constraints

- Run everything from repo root via `uv run` (e.g. `uv run pytest`). Never call `pip`; add deps only with `uv add`.
- Determinism is mandatory: every list reaching output is `sorted()`; never let `set` iteration order leak into output.
- Scoring/report/path behavior must NOT change. `lesson_refs` is metadata only.
- Item invariants (enforced by `tests/test_content_integrity.py`): every `item.points` entry exists in the knowledge map; ≥2 items per knowledge point; every `standard_ref` exists in `standards/ccss_math.yaml`; **no MCQ distractor is numerically equal to the keyed answer**; `type` ∈ {`mcq`,`numeric`}; `difficulty` ∈ 1..3.
- Grade-5 content and `curriculum/shormann_algebra_2` are untouched. No new standards are added to the catalog (all 25 already exist).
- eTextbook problems are copyrighted: author **original** items at the same skill and difficulty as the cited lesson. Do not copy problems verbatim.
- Source PDF: `asset/shormann_math/Shormann Algebra 1 Textbook.pdf`. **PDF page = printed lesson page + 7.** Read a lesson with `pdftotext -f <start> -l <end> "<pdf>" -`.
- Prerequisite: ensure no editor holds `item_bank.yaml` open (remove any `.item_bank.yaml.swp`) before editing.

## Standard → knowledge-point map (reference for all tasks)

All 25 HS standards, each carried by exactly one point:

- `a1-num-exprad` → N.RN.A.2 · `a1-num-units` → N.Q.A.1 · `a1-complex` → N.CN.A.1, N.CN.C.7
- `a1-expr-interpret` → A.SSE.A.1 · `a1-expr-model` → A.CED.A.1 · `a1-expr-linear` → A.REI.B.3
- `a1-poly-ops` → A.APR.A.1 · `a1-poly-factor` → A.SSE.B.3 · `a1-quad-solve` → A.REI.B.4 · `a1-systems` → A.REI.C.6
- `a1-func-concept` → F.IF.A.1 · `a1-func-graph` → F.IF.B.4, F.BF.B.3 · `a1-func-linexp` → F.LE.A.1, F.LE.A.2
- `a1-geo-def` → G.CO.A.1 · `a1-geo-proof` → G.CO.C.10 · `a1-geo-circle` → G.C.A.2
- `a1-geo-sim` → G.SRT.A.2 · `a1-geo-trig` → G.SRT.C.8 · `a1-geo-measure` → G.GMD.A.3
- `a1-data-display` → S.ID.A.1 · `a1-data-scatter` → S.ID.B.6 · `a1-data-interpret` → S.ID.C.7
- `a1-num-realnum` → (no CCSS ref; foundational)

Catalog codes carry the full prefix, e.g. `CCSS.HSN.RN.A.2`, `CCSS.HSA.SSE.A.1`.

---

### Task 1: Add optional `lesson_refs` field to items

**Files:**
- Modify: `engine/models.py` (the `Item` dataclass — currently: `id, points, difficulty, type, prompt, answer, options, distractor_feedback, role`)
- Modify: `engine/loader.py` (item construction at `engine/loader.py:38`, `it["id"]: Item(...)`, inside `load_course`)
- Modify: `schemas/item_bank.schema.json`
- Test: `tests/test_models.py`, `tests/test_loader.py`

**Interfaces:**
- Produces: `Item.lesson_refs: list[int]` (default `[]`); loader reads YAML key `lesson_refs` via `it.get("lesson_refs", [])`.
- Note: items are built only inside `load_course(course_dir, schemas_dir, methodology_dir, standards_dir)`; there is no standalone item loader. `Curriculum.items` is a `dict[str, Item]`.

- [ ] **Step 1: Confirm the `Item` fields and the loader construction site**

Run: `uv run python -c "import inspect, engine.models as m; print(inspect.getsource(m.Item))"`
Run: `sed -n '36,55p' engine/loader.py`
Expected: `Item` fields as listed above; the `Item(...)` call keyed by `it["id"]` reading from dict `it`.

- [ ] **Step 2: Write the failing model test**

Add to `tests/test_models.py`:

```python
def test_item_lesson_refs_field():
    """Item accepts lesson_refs; defaults to empty list."""
    from engine.models import Item
    base = dict(id="X", points=("p",), difficulty=1, type="numeric", prompt="q", answer="1")
    assert Item(**base).lesson_refs == []
    assert Item(**base, lesson_refs=[43, 80]).lesson_refs == [43, 80]
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `uv run pytest tests/test_models.py::test_item_lesson_refs_field -v`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'lesson_refs'`.

- [ ] **Step 4: Add the field to the `Item` dataclass**

In `engine/models.py`, add to `Item` as the **last** field (after `role`, so the ordering of existing fields is unchanged):

```python
    lesson_refs: list[int] = field(default_factory=list)
```

`field` is already imported in this module (used by `options`/`distractor_feedback`).

- [ ] **Step 5: Populate it in the loader**

In `engine/loader.py`, in the `Item(...)` call at line ~38 (dict variable is `it`), add the argument:

```python
            lesson_refs=it.get("lesson_refs", []),
```

- [ ] **Step 6: Add a loader regression test (existing content defaults to `[]`)**

Add to `tests/test_loader.py`:

```python
def test_existing_items_default_empty_lesson_refs():
    """Courses without lesson_refs load with an empty list (no breakage)."""
    from engine.loader import load_course
    c = load_course("curriculum/grade5_math", "schemas", "methodology", "standards")
    assert all(it.lesson_refs == [] for it in c.items.values())
```

(The populated-read path is exercised by Task 2's fidelity test, which loads real Algebra 1 items carrying `lesson_refs`.)

- [ ] **Step 7: Allow the field in the schema**

In `schemas/item_bank.schema.json`, add inside the item `properties` object (keep `additionalProperties: false`):

```json
          "lesson_refs": {"type": "array", "items": {"type": "integer", "minimum": 1}}
```

- [ ] **Step 8: Run the new tests + full suite**

Run: `uv run pytest tests/test_models.py::test_item_lesson_refs_field tests/test_loader.py::test_existing_items_default_empty_lesson_refs -v`
Expected: PASS
Run: `uv run pytest`
Expected: PASS (grade-5 items have no `lesson_refs`; default keeps them valid).

- [ ] **Step 9: Commit**

```bash
git add engine/models.py engine/loader.py schemas/item_bank.schema.json tests/test_models.py tests/test_loader.py
git commit -m "feat(items): add optional lesson_refs field for eTextbook traceability"
```

---

### Task 2: Cutover to new structure — Strand 1 (Number, Ratio & Quantity) + fidelity test

This task **replaces** the old 6-point map and 24-item bank with the new structure's first strand, and adds the fidelity test that guards every strand added afterward.

**Files:**
- Overwrite: `curriculum/shormann_algebra_1/knowledge_map.yaml`
- Overwrite: `curriculum/shormann_algebra_1/item_bank.yaml`
- Overwrite: `curriculum/shormann_algebra_1/sample_responses.yaml`
- Test: `tests/test_content_integrity.py`

**Interfaces:**
- Produces knowledge points `a1-num-realnum`, `a1-num-exprad`, `a1-num-units`.
- Produces the `ALLOWED_LESSONS` fidelity test consumed (extended) by later tasks.

**Lessons to read for calibration** (`pdftotext -f S -l E "asset/shormann_math/Shormann Algebra 1 Textbook.pdf" -`):
- `a1-num-realnum`: L2 (pdf 14–24), L3 (pdf 25–30) — integers, number line, absolute value, order of operations.
- `a1-num-exprad`: L3 (pdf 25–30), L30 (pdf 219–223), L31 (pdf 224–228), L32 (pdf 229–232), L33 (pdf 233–237), L58 (pdf 345–349) — whole/fractional/variable exponents, radicals, scientific notation.
- `a1-num-units`: L5 (pdf 40–45), L6 (pdf 46–50), L44 (pdf 285–288), L45 (pdf 289–292) — fraction/decimal/percent, rate, length/area/volume conversions.

- [ ] **Step 1: Remove any editor lock**

Run: `rm -f curriculum/shormann_algebra_1/.item_bank.yaml.swp`
Expected: no output (file removed or already absent).

- [ ] **Step 2: Write the new knowledge map (Strand 1 only for now)**

Overwrite `curriculum/shormann_algebra_1/knowledge_map.yaml`:

```yaml
points:
  # --- Strand: Number, Ratio & Quantity ---
  - id: a1-num-realnum
    strand: Number, Ratio & Quantity
    title: Real numbers, absolute value, and order
    description: Classify real numbers, compare and order them, and evaluate absolute value and order of operations.
    prerequisites: []
    standard_refs: []
  - id: a1-num-exprad
    strand: Number, Ratio & Quantity
    title: Exponents, radicals, and scientific notation
    description: Apply exponent rules (whole, fractional, variable), simplify radicals, and convert scientific notation.
    prerequisites: [a1-num-realnum]
    standard_refs: [CCSS.HSN.RN.A.2]
  - id: a1-num-units
    strand: Number, Ratio & Quantity
    title: Units, measurement, and proportional reasoning
    description: Use units and unit conversions to guide solutions and reason with rates, percent, and proportion.
    prerequisites: [a1-num-realnum]
    standard_refs: [CCSS.HSN.Q.A.1]
```

- [ ] **Step 3: Write the new item bank (Strand 1 only) — worked template**

Overwrite `curriculum/shormann_algebra_1/item_bank.yaml`. Author ≥2 diagnostic + ≥2 practice per point, difficulty-laddered, calibrated to the lessons above. `a1-num-realnum` is fully worked here as the template for every later point:

```yaml
items:
  # --- a1-num-realnum (L2-3) ---
  - id: A1NUMRE-D1
    role: diagnostic
    points: [a1-num-realnum]
    difficulty: 1
    type: numeric
    prompt: "Evaluate |{-8}|."
    answer: "8"
    lesson_refs: [3]
  - id: A1NUMRE-D2
    role: diagnostic
    points: [a1-num-realnum]
    difficulty: 2
    type: mcq
    prompt: "Which list is ordered from least to greatest?"
    options: {A: "-3, -1, 0, 2", B: "0, -1, -3, 2", C: "2, 0, -1, -3", D: "-1, -3, 0, 2"}
    answer: "A"
    lesson_refs: [2]
  - id: A1NUMRE-P1
    role: practice
    points: [a1-num-realnum]
    difficulty: 2
    type: numeric
    prompt: "Evaluate 3 + 2 * 4^2 - 5."
    answer: "30"
    lesson_refs: [3]
  - id: A1NUMRE-P2
    role: practice
    points: [a1-num-realnum]
    difficulty: 1
    type: mcq
    prompt: "Which number is irrational?"
    options: {A: "sqrt(2)", B: "1/3", C: "-4", D: "0.25"}
    answer: "A"
    lesson_refs: [2]
  # --- a1-num-exprad (L3, 30-33, 58): author >=2 diagnostic + >=2 practice ---
  #   Skills: x^m * x^n, (x^m)^n, x^(1/2)=sqrt, simplify sqrt(50), a*10^n form.
  #   Tag lesson_refs from {3,30,31,32,33,58}; standard_refs implied by point (N.RN.A.2).
  # --- a1-num-units (L5-6, 44-45): author >=2 diagnostic + >=2 practice ---
  #   Skills: convert cm->m, percent of a quantity, unit rate, area/volume unit factors.
  #   Tag lesson_refs from {5,6,44,45}.
```

Replace the two comment blocks with real items following the `a1-num-realnum` pattern (unique ids like `A1NUMEX-D1`, `A1NUMUN-P2`; MCQ distractors must not numerically equal the key). Read the cited pages first to match style/difficulty.

- [ ] **Step 4: Write a minimal valid sample_responses**

Overwrite `curriculum/shormann_algebra_1/sample_responses.yaml`. The format is a **dict** under `responses:` keyed by item id → answer string (references only real Strand-1 ids; comprehensive version is Task 10):

```yaml
responses:
  A1NUMRE-D1: "8"
  A1NUMRE-D2: "A"
  A1NUMRE-P1: "30"
```

- [ ] **Step 5: Add the fidelity test with the full allowed-lesson map**

Add to `tests/test_content_integrity.py`. This file already exposes a `curricula` fixture (a dict keyed by course dir) and module constants `SCHEMAS_DIR`/`METHODOLOGY_DIR`/`STANDARDS_DIR`; use the fixture. `Curriculum.items` is a `dict[str, Item]`; `item.points` is a tuple.

```python
# Allowed Shormann lesson numbers per Algebra 1 knowledge point (from the design spec).
ALLOWED_LESSONS = {
    "a1-num-realnum": {2, 3},
    "a1-num-exprad": {3, 30, 31, 32, 33, 58},
    "a1-num-units": {5, 6, 44, 45},
    "a1-expr-interpret": {8, 35, 36, 37, 38},
    "a1-expr-model": {7, 8, 48},
    "a1-expr-linear": {7, 46},
    "a1-poly-ops": {37, 38},
    "a1-poly-factor": {51, 75, 91},
    "a1-quad-solve": {75, 76, 91, 92},
    "a1-complex": {92, 95},
    "a1-func-concept": {15, 52, 53},
    "a1-func-graph": {16, 55, 56, 57},
    "a1-func-linexp": {48, 81},
    "a1-systems": {17, 61, 64, 70},
    "a1-geo-def": {9, 10, 11},
    "a1-geo-proof": {10, 66, 67, 68},
    "a1-geo-circle": {40, 66},
    "a1-geo-sim": {6, 9},
    "a1-geo-trig": {12, 19, 43, 80},
    "a1-geo-measure": {13, 41, 42},
    "a1-data-display": {23},
    "a1-data-scatter": {24, 94},
    "a1-data-interpret": {24, 94},
}


def test_shormann_alg1_items_cite_consistent_lessons(curricula):
    """Every Algebra 1 item cites >=1 lesson in 1..100, consistent with its point."""
    course = curricula["curriculum/shormann_algebra_1"]
    for item in course.items.values():
        for pt in item.points:
            if pt in ALLOWED_LESSONS:
                assert item.lesson_refs, f"{item.id} has no lesson_refs"
                for L in item.lesson_refs:
                    assert 1 <= L <= 100, f"{item.id} lesson {L} out of range"
                    assert L in ALLOWED_LESSONS[pt], (
                        f"{item.id} cites lesson {L} not allowed for {pt}"
                    )
```

- [ ] **Step 6: Run integrity + fidelity + coverage**

Run: `uv run pytest tests/test_content_integrity.py -v`
Expected: PASS (all Strand-1 points have ≥2 items; lesson_refs valid).
Run: `uv run python -m engine.cli --curriculum curriculum/shormann_algebra_1 --coverage`
Expected: prints coverage (2/25 so far — full 25/25 arrives in Task 10). No crash.
Run: `uv run pytest`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add curriculum/shormann_algebra_1 tests/test_content_integrity.py
git commit -m "feat(alg1): restructure to Shormann strands — Number, Ratio & Quantity"
```

---

### Task 3: Strand 2 — Expressions & Equations

**Files:**
- Modify: `curriculum/shormann_algebra_1/knowledge_map.yaml` (append points)
- Modify: `curriculum/shormann_algebra_1/item_bank.yaml` (append items)

**Interfaces:**
- Consumes: `a1-num-realnum` (Task 2) as a prerequisite.
- Produces points `a1-expr-interpret`, `a1-expr-model`, `a1-expr-linear`.

**Lessons:** `a1-expr-interpret`: L8 (pdf 57–62), L35 (243–246), L36 (247–249), L37 (250–253), L38 (254–257). `a1-expr-model`: L7 (51–56), L8 (57–62), L48 (300–304). `a1-expr-linear`: L7 (51–56), L46 (293–296).

- [ ] **Step 1: Append the map points**

Append to `points:` in `knowledge_map.yaml`:

```yaml
  # --- Strand: Expressions & Equations ---
  - id: a1-expr-interpret
    strand: Expressions & Equations
    title: Interpret and simplify expressions
    description: Interpret parts of an algebraic expression and simplify using the commutative, associative, and distributive properties.
    prerequisites: [a1-num-realnum]
    standard_refs: [CCSS.HSA.SSE.A.1]
  - id: a1-expr-model
    strand: Expressions & Equations
    title: Model situations with equations
    description: Create one-variable equations from word problems and use them to solve.
    prerequisites: [a1-expr-interpret]
    standard_refs: [CCSS.HSA.CED.A.1]
  - id: a1-expr-linear
    strand: Expressions & Equations
    title: Solve linear equations
    description: Solve one-variable linear equations, including multi-step and variables on both sides.
    prerequisites: [a1-expr-interpret]
    standard_refs: [CCSS.HSA.REI.B.3]
```

- [ ] **Step 2: Author and append items**

Read the cited pages, then append ≥2 diagnostic + ≥2 practice per point to `item_bank.yaml`, following the Task 2 template (id prefixes e.g. `A1EXPRI-`, `A1EXPRM-`, `A1EXPRL-`; `lesson_refs` from that point's allowed set; MCQ distractors ≠ key). Cover: interpret coefficients/terms & distribute (`a1-expr-interpret`); translate a sentence to an equation & solve applied (`a1-expr-model`); solve `ax+b=c` and variables-both-sides (`a1-expr-linear`).

- [ ] **Step 3: Run integrity + fidelity**

Run: `uv run pytest tests/test_content_integrity.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add curriculum/shormann_algebra_1
git commit -m "feat(alg1): add Expressions & Equations strand"
```

---

### Task 4: Strand 3 — Polynomials & Quadratics

**Files:**
- Modify: `curriculum/shormann_algebra_1/knowledge_map.yaml`
- Modify: `curriculum/shormann_algebra_1/item_bank.yaml`

**Interfaces:**
- Consumes: `a1-expr-interpret`, `a1-num-exprad`, `a1-expr-linear`.
- Produces points `a1-poly-ops`, `a1-poly-factor`, `a1-quad-solve`, `a1-complex`.

**Lessons:** `a1-poly-ops`: L37 (250–253), L38 (254–257). `a1-poly-factor`: L51 (313–316), L75 (441–445), L91 (530–534). `a1-quad-solve`: L75 (441–445), L76 (446–449), L91 (530–534), L92 (535–539). `a1-complex`: L92 (535–539), L95 (552–556).

- [ ] **Step 1: Append the map points**

```yaml
  # --- Strand: Polynomials & Quadratics ---
  - id: a1-poly-ops
    strand: Polynomials & Quadratics
    title: Polynomial operations
    description: Add, subtract, and multiply polynomials and recognize closure.
    prerequisites: [a1-expr-interpret, a1-num-exprad]
    standard_refs: [CCSS.HSA.APR.A.1]
  - id: a1-poly-factor
    strand: Polynomials & Quadratics
    title: Factoring and equivalent forms
    description: Factor quadratic expressions and choose an equivalent form that reveals properties.
    prerequisites: [a1-poly-ops]
    standard_refs: [CCSS.HSA.SSE.B.3]
  - id: a1-quad-solve
    strand: Polynomials & Quadratics
    title: Solve quadratic equations
    description: Solve quadratics by factoring, completing the square, and the quadratic formula.
    prerequisites: [a1-poly-factor, a1-expr-linear]
    standard_refs: [CCSS.HSA.REI.B.4]
  - id: a1-complex
    strand: Polynomials & Quadratics
    title: Complex numbers and complex solutions
    description: Understand the imaginary unit i and find complex solutions of quadratics.
    prerequisites: [a1-quad-solve]
    standard_refs: [CCSS.HSN.CN.A.1, CCSS.HSN.CN.C.7]
```

- [ ] **Step 2: Author and append items**

Read cited pages; append ≥2 diagnostic + ≥2 practice per point (id prefixes `A1POLYO-`, `A1POLYF-`, `A1QUAD-`, `A1CPLX-`). Cover: `(2x+3)+(5x-1)` & `(x+2)(x+3)` (`a1-poly-ops`); factor `x^2+5x+6` (`a1-poly-factor`); solve `x^2-5x+6=0` by factoring and one via quadratic formula (`a1-quad-solve`); `i^2`, and roots of `x^2+1=0` (`a1-complex`). Keep numeric answers exact strings.

- [ ] **Step 3: Run integrity + fidelity**

Run: `uv run pytest tests/test_content_integrity.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add curriculum/shormann_algebra_1
git commit -m "feat(alg1): add Polynomials & Quadratics strand"
```

---

### Task 5: Strand 4 — Functions & Modeling

**Files:**
- Modify: `curriculum/shormann_algebra_1/knowledge_map.yaml`
- Modify: `curriculum/shormann_algebra_1/item_bank.yaml`

**Interfaces:**
- Consumes: `a1-expr-linear`.
- Produces points `a1-func-concept`, `a1-func-graph`, `a1-func-linexp`.

**Lessons:** `a1-func-concept`: L15 (112–119), L52 (317–321), L53 (322–326). `a1-func-graph`: L16 (120–129), L55 (331–334), L56 (335–337), L57 (338–344). `a1-func-linexp`: L48 (300–304), L81 (474–479).

- [ ] **Step 1: Append the map points**

```yaml
  # --- Strand: Functions & Modeling ---
  - id: a1-func-concept
    strand: Functions & Modeling
    title: Function concept, notation, domain and range
    description: Use function notation, evaluate functions, and identify domain and range.
    prerequisites: [a1-expr-linear]
    standard_refs: [CCSS.HSF.IF.A.1]
  - id: a1-func-graph
    strand: Functions & Modeling
    title: Graph key features and transformations
    description: Interpret intercepts, slope, and increasing/decreasing behavior, and describe the effect of shifts on a graph.
    prerequisites: [a1-func-concept]
    standard_refs: [CCSS.HSF.IF.B.4, CCSS.HSF.BF.B.3]
  - id: a1-func-linexp
    strand: Functions & Modeling
    title: Linear versus exponential; constructing models
    description: Distinguish linear from exponential situations and construct a linear or exponential model from data.
    prerequisites: [a1-func-concept]
    standard_refs: [CCSS.HSF.LE.A.1, CCSS.HSF.LE.A.2]
```

- [ ] **Step 2: Author and append items**

Read cited pages; append ≥2 diagnostic + ≥2 practice per point (id prefixes `A1FUNC-`, `A1FGRA-`, `A1FLE-`). Cover: `f(x)=2x+1, f(5)` & domain/range (`a1-func-concept`); slope & y-intercept of `y=4x-3`, effect of `f(x)+k` shift (`a1-func-graph`); identify linear-vs-exponential table & write `y=mx+b` from two points (`a1-func-linexp`).

- [ ] **Step 3: Run integrity + fidelity**

Run: `uv run pytest tests/test_content_integrity.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add curriculum/shormann_algebra_1
git commit -m "feat(alg1): add Functions & Modeling strand"
```

---

### Task 6: Strand 6 — Geometry: Reasoning & Proof

**Files:**
- Modify: `curriculum/shormann_algebra_1/knowledge_map.yaml`
- Modify: `curriculum/shormann_algebra_1/item_bank.yaml`

**Interfaces:**
- Produces points `a1-geo-def` (root), `a1-geo-proof`, `a1-geo-circle`.

**Lessons:** `a1-geo-def`: L9 (63–71), L10 (72–77), L11 (78–86). `a1-geo-proof`: L10 (72–77), L66 (391–396), L67 (397–404), L68 (405–411). `a1-geo-circle`: L40 (263–267), L66 (391–396).

- [ ] **Step 1: Append the map points**

```yaml
  # --- Strand: Geometry: Reasoning & Proof ---
  - id: a1-geo-def
    strand: Geometry: Reasoning & Proof
    title: Precise geometric definitions
    description: Know precise definitions of angle, parallel, perpendicular, and related terms.
    prerequisites: []
    standard_refs: [CCSS.HSG.CO.A.1]
  - id: a1-geo-proof
    strand: Geometry: Reasoning & Proof
    title: Triangle theorems and proof
    description: Use deductive and inductive reasoning to prove theorems about triangles (angle sum, isosceles base angles).
    prerequisites: [a1-geo-def]
    standard_refs: [CCSS.HSG.CO.C.10]
  - id: a1-geo-circle
    strand: Geometry: Reasoning & Proof
    title: Circle angle relationships
    description: Identify relationships among inscribed angles, central angles, radii, and chords.
    prerequisites: [a1-geo-def]
    standard_refs: [CCSS.HSG.C.A.2]
```

- [ ] **Step 2: Author and append items**

Read cited pages; append ≥2 diagnostic + ≥2 practice per point (id prefixes `A1GDEF-`, `A1GPRF-`, `A1GCIR-`). Cover: parallel/perpendicular definitions & angle terms (`a1-geo-def`); triangle angle-sum = 180, isosceles base angles (`a1-geo-proof`); inscribed angle = half central angle (`a1-geo-circle`).

- [ ] **Step 3: Run integrity + fidelity**

Run: `uv run pytest tests/test_content_integrity.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add curriculum/shormann_algebra_1
git commit -m "feat(alg1): add Geometry: Reasoning & Proof strand"
```

---

### Task 7: Strand 7 — Geometry: Similarity, Trig & Measurement

**Files:**
- Modify: `curriculum/shormann_algebra_1/knowledge_map.yaml`
- Modify: `curriculum/shormann_algebra_1/item_bank.yaml`

**Interfaces:**
- Consumes: `a1-geo-def`, `a1-num-units`.
- Produces points `a1-geo-sim`, `a1-geo-trig`, `a1-geo-measure`.

**Lessons:** `a1-geo-sim`: L6 (46–50), L9 (63–71). `a1-geo-trig`: L12 (87–95), L19 (150–154), L43 (280–284), L80 (469–473). `a1-geo-measure`: L13 (96–104), L41 (268–274), L42 (275–279).

- [ ] **Step 1: Append the map points**

```yaml
  # --- Strand: Geometry: Similarity, Trig & Measurement ---
  - id: a1-geo-sim
    strand: Geometry: Similarity, Trig & Measurement
    title: Similarity and scaling
    description: Use similarity to decide whether figures are similar and solve scaling problems.
    prerequisites: [a1-geo-def]
    standard_refs: [CCSS.HSG.SRT.A.2]
  - id: a1-geo-trig
    strand: Geometry: Similarity, Trig & Measurement
    title: Right-triangle trigonometry and the Pythagorean theorem
    description: Use sine, cosine, tangent, and the Pythagorean theorem to solve right triangles.
    prerequisites: [a1-geo-sim]
    standard_refs: [CCSS.HSG.SRT.C.8]
  - id: a1-geo-measure
    strand: Geometry: Similarity, Trig & Measurement
    title: Perimeter, area, surface area, and volume
    description: Compute perimeter, area, surface area, and volume of solids to solve problems.
    prerequisites: [a1-geo-def, a1-num-units]
    standard_refs: [CCSS.HSG.GMD.A.3]
```

- [ ] **Step 2: Author and append items**

Read cited pages; append ≥2 diagnostic + ≥2 practice per point (id prefixes `A1GSIM-`, `A1GTRI-`, `A1GMEA-`). Cover: similar-triangle side ratio/scale factor (`a1-geo-sim`); 3-4-5 & 45-45-90 / 30-60-90 sides, `tan`/Pythagorean solve (`a1-geo-trig`); volume of box/cube/cylinder, surface area (`a1-geo-measure`).

- [ ] **Step 3: Run integrity + fidelity**

Run: `uv run pytest tests/test_content_integrity.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add curriculum/shormann_algebra_1
git commit -m "feat(alg1): add Geometry: Similarity, Trig & Measurement strand"
```

---

### Task 8: Strand 5 — Systems of Equations

**Files:**
- Modify: `curriculum/shormann_algebra_1/knowledge_map.yaml`
- Modify: `curriculum/shormann_algebra_1/item_bank.yaml`

**Interfaces:**
- Consumes: `a1-expr-linear` (Task 3), `a1-func-graph` (Task 5).
- Produces point `a1-systems`.

**Lessons:** `a1-systems`: L17 (130–137), L61 (363–368), L64 (379–385), L70 (418–422).

- [ ] **Step 1: Append the map point**

```yaml
  # --- Strand: Systems of Equations ---
  - id: a1-systems
    strand: Systems of Equations
    title: Solve systems of linear equations
    description: Solve two-variable linear systems by graphing, substitution, and elimination.
    prerequisites: [a1-expr-linear, a1-func-graph]
    standard_refs: [CCSS.HSA.REI.C.6]
```

- [ ] **Step 2: Author and append items**

Read cited pages; append ≥2 diagnostic + ≥2 practice (id prefix `A1SYS-`). Cover: solve `y=x+1, y=2x-1`; `x+y=10, x-y=4`; count solutions of parallel non-identical lines (answer "None"); one elimination problem.

- [ ] **Step 3: Run integrity + fidelity**

Run: `uv run pytest tests/test_content_integrity.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add curriculum/shormann_algebra_1
git commit -m "feat(alg1): add Systems of Equations strand"
```

---

### Task 9: Strand 8 — Data, Statistics & Probability

**Files:**
- Modify: `curriculum/shormann_algebra_1/knowledge_map.yaml`
- Modify: `curriculum/shormann_algebra_1/item_bank.yaml`

**Interfaces:**
- Consumes: `a1-func-graph` (Task 5).
- Produces points `a1-data-display`, `a1-data-scatter`, `a1-data-interpret`.

**Lessons:** `a1-data-display`: L23 (179–185). `a1-data-scatter`: L24 (186–192), L94 (546–551). `a1-data-interpret`: L24 (186–192), L94 (546–551).

- [ ] **Step 1: Append the map points**

```yaml
  # --- Strand: Data, Statistics & Probability ---
  - id: a1-data-display
    strand: Data, Statistics & Probability
    title: Data displays and summary statistics
    description: Represent single-variable data with plots and summarize with mean, median, mode, and range.
    prerequisites: []
    standard_refs: [CCSS.HSS.ID.A.1]
  - id: a1-data-scatter
    strand: Data, Statistics & Probability
    title: Scatter plots and line of best fit
    description: Represent bivariate data on a scatter plot and fit a linear function.
    prerequisites: [a1-data-display]
    standard_refs: [CCSS.HSS.ID.B.6]
  - id: a1-data-interpret
    strand: Data, Statistics & Probability
    title: Interpret slope and intercept of a linear model
    description: Interpret the slope and intercept of a fitted linear model in context.
    prerequisites: [a1-data-scatter, a1-func-graph]
    standard_refs: [CCSS.HSS.ID.C.7]
```

- [ ] **Step 2: Author and append items**

Read cited pages; append ≥2 diagnostic + ≥2 practice per point (id prefixes `A1DDIS-`, `A1DSCA-`, `A1DINT-`). Cover: mean/median/range & best display for one variable (`a1-data-display`); which scatter shows positive association / choose fit line (`a1-data-scatter`); interpret slope & intercept of `cost = 2x + 5` in context (`a1-data-interpret`).

- [ ] **Step 3: Run integrity + fidelity + full suite**

Run: `uv run pytest tests/test_content_integrity.py -v`
Expected: PASS (all 23 points present, each with ≥2 items).

- [ ] **Step 4: Commit**

```bash
git add curriculum/shormann_algebra_1
git commit -m "feat(alg1): add Data, Statistics & Probability strand"
```

---

### Task 10: Wiring — comprehensive sample responses, coverage lock, docs

**Files:**
- Overwrite: `curriculum/shormann_algebra_1/sample_responses.yaml`
- Test: `tests/test_coverage.py`
- Modify: `docs/shormann-ccss-alignment.md`

**Interfaces:**
- Consumes: all 23 points and their item ids.

- [ ] **Step 1: Regenerate comprehensive sample responses**

List the real item ids: `grep -E '^\s+- id:' curriculum/shormann_algebra_1/item_bank.yaml`.
Overwrite `curriculum/shormann_algebra_1/sample_responses.yaml` to answer a realistic spread across strands — enough correct/incorrect answers that at least one strand is Secure, one Developing, and at least one point stays `insufficient_evidence` (answer <2 of its items). Use the dict shape under `responses:` — `<item_id>: "<answer>"` per line, e.g.:

```yaml
responses:
  A1NUMRE-D1: "8"
  A1NUMRE-D2: "A"
  A1EXPRL-D1: "wrong-on-purpose"
```

- [ ] **Step 2: Verify the status report + learning path render**

Run: `uv run python -m engine.cli --curriculum curriculum/shormann_algebra_1 --responses curriculum/shormann_algebra_1/sample_responses.yaml --name Sam`
Expected: prints a status report over the 8 strands plus a learning path, no error.

- [ ] **Step 3: Write the failing coverage-lock test**

Add to `tests/test_coverage.py` (`CoverageReport` fields are `total: int`, `covered: list[str]`, `missing: list[str]`; `load_course` takes four args as used elsewhere in this file):

```python
def test_shormann_alg1_full_coverage():
    """Algebra 1 covers all 25 HS CCSS standards."""
    from engine.loader import load_course
    from engine.coverage import compute_coverage
    course = load_course("curriculum/shormann_algebra_1", "schemas", "methodology", "standards")
    report = compute_coverage(course)
    assert report.total == 25
    assert len(report.covered) == 25
    assert report.missing == []
```

- [ ] **Step 4: Run it**

Run: `uv run pytest tests/test_coverage.py::test_shormann_alg1_full_coverage -v`
Expected: PASS (if it fails, a standard_ref is missing or misspelled — cross-check against the Standard→point map at the top of this plan).

- [ ] **Step 5: Update the alignment doc**

In `docs/shormann-ccss-alignment.md`, update the "How this maps into the evaluator" section: Algebra 1 now covers the full 25-standard HS band on its own; note the intentional Algebra 1 / Algebra 2 coverage overlap; correct the statement that `CCSS.HSN.Q.A.1` is uncovered (Algebra 1's measurement/units lessons cover it). Add a one-line note that Shormann Algebra 1 also teaches topics outside the CCSS catalog (history of math, intro calculus, computer/binary math, Punnett squares/gas laws), left without `standard_refs`.

- [ ] **Step 6: Full suite + coverage sanity**

Run: `uv run pytest`
Expected: PASS.
Run: `uv run python -m engine.cli --curriculum curriculum/shormann_algebra_1 --coverage`
Expected: `25 / 25 standards covered (100.0%)`.

- [ ] **Step 7: Commit**

```bash
git add curriculum/shormann_algebra_1/sample_responses.yaml tests/test_coverage.py docs/shormann-ccss-alignment.md
git commit -m "test(alg1): lock 25/25 coverage; refresh sample responses and alignment doc"
```

---

## Self-review notes

- **Spec coverage:** Part 1 (map) → Tasks 2–9; Part 2 (`lesson_refs`) → Task 1; Part 3 (item authoring + fidelity) → Tasks 2–9 + fidelity test in Task 2; Part 4 (sample responses) → Task 10 Step 1; Part 5 (tests) → Task 1 (loader), Task 2 (fidelity), Task 10 (coverage lock); Part 6 (docs) → Task 10 Step 5. All spec sections mapped.
- **Prerequisite ordering:** every point's prerequisites are produced in an earlier task (num→expr→poly→func→geo→systems→data); the suite is green after each task because all points present so far have ≥2 items.
- **Determinism / no behavior change:** `lesson_refs` is metadata only; no scoring/report/path code changes.
