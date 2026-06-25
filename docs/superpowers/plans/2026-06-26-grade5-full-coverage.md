# Grade 5 Full Standards Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take Grade-5 Math coverage from 6/26 to 26/26, reorganized into the five CCSS domains as strands, by authoring content only (knowledge points, items, demo responses) — the engine does not change.

**Architecture:** Relabel the 8 existing knowledge points into two CCSS-domain strands, then add 20 new knowledge points (one per uncovered standard) with within-domain prerequisite chains and ~2 items each, extend the demo student to answer everything, and bump the two coverage test expectations as each domain lands. Each domain is one task; the suite is green at every commit.

**Tech Stack:** YAML content validated by JSON Schema; Python engine unchanged; pytest.

## Global Constraints

- Content only — do NOT modify `engine/`, `schemas/`, `templates/`, or `standards/ccss_math.yaml`.
- Every knowledge point needs ≥2 items; every prerequisite id must resolve; the prerequisite graph must stay acyclic; every item's `points` must exist; every `standard_refs` code must exist in the catalog (all enforced by `tests/test_content_integrity.py`).
- No MCQ distractor may be numerically equal to the keyed answer (enforced by `test_content_integrity.py::test_mcq_options_have_no_duplicate_values`).
- Item shape: `id`, `points`, `difficulty` (1–3), `type` (`mcq`|`numeric`), `prompt`, `answer`, and `options` for mcq. Knowledge-point shape: `id`, `strand`, `title`, `description`, `prerequisites`, `standard_refs`.
- Knowledge-point ids use the existing `g5-` prefix. New item ids must not collide with existing ones (`EQF/ALK/ALU/MFW/MFF/DUF/DPV/ASD-*`).
- Run tests as `python -m pytest` from the repo root.
- Final state: `python -m engine.cli --curriculum curriculum/grade5_math --coverage` prints `26 / 26 standards covered (100.0%)` with an empty Missing list.

## Files (all under `curriculum/grade5_math/`)

- `knowledge_map.yaml` — relabel 8 points' `strand`; append 20 new points
- `item_bank.yaml` — append ~44 new items
- `sample_responses.yaml` — append responses for all new items
- `tests/test_coverage.py` — bump `test_grade5_math_real_coverage` count each task
- `tests/test_cli.py` — bump the `"N / 26"` assertion each task

## Execution order & running coverage count

Geometry is authored before Operations & Algebraic Thinking because `g5-oa-patterns-graph`
(5.OA.B.3) lists `g5-coordinate-system` (5.G.A.1) as a prerequisite.

| Task | Domain | New pts | Covered after |
|------|--------|---------|---------------|
| 1 | Relabel existing strands | 0 | 6 |
| 2 | Geometry (5.G) | 4 | 10 |
| 3 | Operations & Algebraic Thinking (5.OA) | 3 | 13 |
| 4 | Number & Operations in Base Ten (5.NBT) | 5 | 18 |
| 5 | Number & Operations—Fractions (5.NF) | 3 | 21 |
| 6 | Measurement & Data (5.MD) | 5 | 26 |

---

## Task 1: Relabel existing strands to CCSS domains

**Files:**
- Modify: `curriculum/grade5_math/knowledge_map.yaml`

**Interfaces:**
- Consumes: nothing.
- Produces: the 8 existing points moved into two CCSS-domain strands. Coverage and item content are unchanged, so all existing tests stay green (the coverage test still sees 6 covered; `test_cli` asserts the substring `"Number & Operations"`, which both new strand names contain).

- [ ] **Step 1: Edit the `strand:` field of the 8 existing points.** In `knowledge_map.yaml`, set `strand:` as follows (leave every other field untouched):

| Point id | New `strand` value |
|----------|--------------------|
| `g5-equiv-fractions` | `Number & Operations—Fractions` |
| `g5-add-like` | `Number & Operations—Fractions` |
| `g5-add-unlike` | `Number & Operations—Fractions` |
| `g5-mult-fraction-whole` | `Number & Operations—Fractions` |
| `g5-mult-fraction-fraction` | `Number & Operations—Fractions` |
| `g5-divide-unit-fraction` | `Number & Operations—Fractions` |
| `g5-decimal-place-value` | `Number & Operations in Base Ten` |
| `g5-add-subtract-decimals` | `Number & Operations in Base Ten` |

- [ ] **Step 2: Run the full suite**

Run: `python -m pytest -q`
Expected: all pass (no coverage or item change; the `Number & Operations` substring still appears in both new strand names).

- [ ] **Step 3: Verify coverage is still 6/26**

Run: `python -m engine.cli --curriculum curriculum/grade5_math --coverage`
Expected: `6 / 26 standards covered (23.1%)`.

- [ ] **Step 4: Commit**

```bash
git add curriculum/grade5_math/knowledge_map.yaml
git commit -m "refactor(content): relabel Grade-5 points into CCSS-domain strands"
```

---

## Task 2: Geometry (5.G) — 4 points

**Files:**
- Modify: `curriculum/grade5_math/knowledge_map.yaml`, `item_bank.yaml`, `sample_responses.yaml`
- Modify: `tests/test_coverage.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: nothing from later tasks.
- Produces: `g5-coordinate-system` (used as a prerequisite by Task 3's `g5-oa-patterns-graph`).

- [ ] **Step 1: Append 4 points to `knowledge_map.yaml`** (under `points:`):

```yaml
  - id: g5-coordinate-system
    strand: Geometry
    title: Coordinate system
    description: Understand axes, the origin, and how an ordered pair locates a point.
    prerequisites: []
    standard_refs: [CCSS.5.G.A.1]
  - id: g5-graph-points
    strand: Geometry
    title: Graph points in the first quadrant
    description: Plot and interpret points given as ordered pairs in the first quadrant.
    prerequisites: [g5-coordinate-system]
    standard_refs: [CCSS.5.G.A.2]
  - id: g5-figure-hierarchy
    strand: Geometry
    title: Hierarchy of two-dimensional figures
    description: Attributes of a category of 2-D figures belong to all its subcategories.
    prerequisites: []
    standard_refs: [CCSS.5.G.B.3]
  - id: g5-classify-figures
    strand: Geometry
    title: Classify two-dimensional figures
    description: Classify 2-D figures in a hierarchy based on their properties.
    prerequisites: [g5-figure-hierarchy]
    standard_refs: [CCSS.5.G.B.4]
```

- [ ] **Step 2: Append 8 items to `item_bank.yaml`** (under `items:`):

```yaml
  - id: G-CS-1
    points: [g5-coordinate-system]
    difficulty: 1
    type: mcq
    prompt: "In the coordinate (x, y), which axis does the first number measure along?"
    options: {A: "the x-axis", B: "the y-axis", C: "neither axis", D: "both axes"}
    answer: "A"
  - id: G-CS-2
    points: [g5-coordinate-system]
    difficulty: 2
    type: mcq
    prompt: "Where do the x-axis and y-axis meet?"
    options: {A: "at the origin (0, 0)", B: "at (1, 1)", C: "at the top", D: "they never meet"}
    answer: "A"
  - id: G-GP-1
    points: [g5-graph-points]
    difficulty: 1
    type: numeric
    prompt: "To plot the point (3, 2), you move right 3 from the origin, then up how many?"
    answer: "2"
  - id: G-GP-2
    points: [g5-graph-points]
    difficulty: 2
    type: mcq
    prompt: "A point is 4 right and 0 up from the origin. Its coordinates are?"
    options: {A: "(4, 0)", B: "(0, 4)", C: "(4, 4)", D: "(0, 0)"}
    answer: "A"
  - id: G-FH-1
    points: [g5-figure-hierarchy]
    difficulty: 1
    type: mcq
    prompt: "Every square is also a..."
    options: {A: "rectangle", B: "triangle", C: "circle", D: "pentagon"}
    answer: "A"
  - id: G-FH-2
    points: [g5-figure-hierarchy]
    difficulty: 2
    type: mcq
    prompt: "Which statement is true?"
    options: {A: "All rectangles are squares", B: "All squares are rectangles", C: "No square is a rectangle", D: "All rectangles are triangles"}
    answer: "B"
  - id: G-CF-1
    points: [g5-classify-figures]
    difficulty: 1
    type: mcq
    prompt: "A quadrilateral with exactly one pair of parallel sides is a..."
    options: {A: "trapezoid", B: "square", C: "triangle", D: "pentagon"}
    answer: "A"
  - id: G-CF-2
    points: [g5-classify-figures]
    difficulty: 2
    type: mcq
    prompt: "Which figure is always a parallelogram?"
    options: {A: "rectangle", B: "trapezoid", C: "triangle", D: "pentagon"}
    answer: "A"
```

- [ ] **Step 3: Append Geometry responses to `sample_responses.yaml`** (under `responses:`) — the demo student is strong in Geometry (all correct):

```yaml
  G-CS-1: "A"
  G-CS-2: "A"
  G-GP-1: "2"
  G-GP-2: "A"
  G-FH-1: "A"
  G-FH-2: "B"
  G-CF-1: "A"
  G-CF-2: "A"
```

- [ ] **Step 4: Bump the coverage test.** Replace `test_grade5_math_real_coverage` in `tests/test_coverage.py` with:

```python
def test_grade5_math_real_coverage():
    from engine.loader import load_course
    c = load_course("curriculum/grade5_math", "schemas", "methodology", "standards")
    r = compute_coverage(c)
    assert r.total == 26
    assert "CCSS.5.NF.A.1" in r.covered
    assert "CCSS.5.G.A.1" in r.covered
    assert "CCSS.4.NF.A.1" in r.out_of_scope
    assert "CCSS.4.NF.A.1" not in r.missing
    assert len(r.covered) == 10
    assert len(r.missing) == 16
    assert r.percentage == pytest.approx(10 / 26)
```

- [ ] **Step 5: Bump the CLI test.** In `tests/test_cli.py`, in `test_cli_coverage_report`, change `assert "6 / 26" in out` to `assert "10 / 26" in out`.

- [ ] **Step 6: Run the suite**

Run: `python -m pytest -q`
Expected: all pass. If an integrity test fails, fix the YAML.

- [ ] **Step 7: Commit**

```bash
git add curriculum/grade5_math tests/test_coverage.py tests/test_cli.py
git commit -m "feat(content): add Grade-5 Geometry (5.G) coverage"
```

---

## Task 3: Operations & Algebraic Thinking (5.OA) — 3 points

**Files:** same content files + the two test files.

**Interfaces:**
- Consumes: `g5-coordinate-system` (Task 2) as a prerequisite for `g5-oa-patterns-graph`.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Append 3 points to `knowledge_map.yaml`**:

```yaml
  - id: g5-oa-eval-expressions
    strand: Operations & Algebraic Thinking
    title: Evaluate numerical expressions
    description: Use parentheses, brackets, or braces and evaluate expressions with them.
    prerequisites: []
    standard_refs: [CCSS.5.OA.A.1]
  - id: g5-oa-write-expressions
    strand: Operations & Algebraic Thinking
    title: Write and interpret expressions
    description: Write simple expressions and interpret them without evaluating.
    prerequisites: [g5-oa-eval-expressions]
    standard_refs: [CCSS.5.OA.A.2]
  - id: g5-oa-patterns-graph
    strand: Operations & Algebraic Thinking
    title: Generate and graph patterns
    description: Generate two numerical patterns from rules and graph the ordered pairs.
    prerequisites: [g5-coordinate-system]
    standard_refs: [CCSS.5.OA.B.3]
```

- [ ] **Step 2: Append 7 items to `item_bank.yaml`**:

```yaml
  - id: OA-EV-1
    points: [g5-oa-eval-expressions]
    difficulty: 1
    type: numeric
    prompt: "Evaluate: 2 x (3 + 4)"
    answer: "14"
  - id: OA-EV-2
    points: [g5-oa-eval-expressions]
    difficulty: 2
    type: numeric
    prompt: "Evaluate: 3 + 4 x 2"
    answer: "11"
  - id: OA-EV-3
    points: [g5-oa-eval-expressions]
    difficulty: 3
    type: numeric
    prompt: "Evaluate: (8 - 3) x (2 + 1)"
    answer: "15"
  - id: OA-WR-1
    points: [g5-oa-write-expressions]
    difficulty: 1
    type: mcq
    prompt: "Which expression means 'add 6 and 4, then multiply by 2'?"
    options: {A: "2 x (6 + 4)", B: "2 x 6 + 4", C: "6 + 4 x 2", D: "6 + 4 + 2"}
    answer: "A"
  - id: OA-WR-2
    points: [g5-oa-write-expressions]
    difficulty: 2
    type: mcq
    prompt: "Without computing, 3 x (245 + 18) is ___ (245 + 18)."
    options: {A: "3 times as large as", B: "equal to", C: "smaller than", D: "3 less than"}
    answer: "A"
  - id: OA-PG-1
    points: [g5-oa-patterns-graph]
    difficulty: 2
    type: numeric
    prompt: "Rule A 'add 2' from 0 gives 0,2,4,6. Rule B 'add 4' from 0 gives 0,4,8,12. The 4th B term divided by the 4th A term is?"
    answer: "2"
  - id: OA-PG-2
    points: [g5-oa-patterns-graph]
    difficulty: 2
    type: mcq
    prompt: "Pattern X adds 3 (0,3,6,9); pattern Y adds 6 (0,6,12,18). Each Y term is the ___ of the matching X term."
    options: {A: "double", B: "half", C: "same", D: "triple"}
    answer: "A"
```

- [ ] **Step 3: Append OA responses to `sample_responses.yaml`** — demo student is mixed (evaluate + patterns secure, writing weak):

```yaml
  OA-EV-1: "14"
  OA-EV-2: "11"
  OA-EV-3: "15"
  OA-WR-1: "B"
  OA-WR-2: "B"
  OA-PG-1: "2"
  OA-PG-2: "A"
```

- [ ] **Step 4: Bump the coverage test** — in `tests/test_coverage.py`, change the last three assertions of `test_grade5_math_real_coverage` to:

```python
    assert len(r.covered) == 13
    assert len(r.missing) == 13
    assert r.percentage == pytest.approx(13 / 26)
```

- [ ] **Step 5: Bump the CLI test** — change `assert "10 / 26" in out` to `assert "13 / 26" in out`.

- [ ] **Step 6: Run the suite**

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add curriculum/grade5_math tests/test_coverage.py tests/test_cli.py
git commit -m "feat(content): add Grade-5 Operations & Algebraic Thinking (5.OA) coverage"
```

---

## Task 4: Number & Operations in Base Ten (5.NBT) — 5 points

**Files:** same content files + the two test files.

**Interfaces:**
- Consumes: `g5-decimal-place-value` (existing) as a prerequisite for `g5-nbt-round-decimals`.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Append 5 points to `knowledge_map.yaml`**:

```yaml
  - id: g5-nbt-place-value
    strand: Number & Operations in Base Ten
    title: Place value (10x relationship)
    description: A digit represents 10 times the place to its right and 1/10 the place to its left.
    prerequisites: []
    standard_refs: [CCSS.5.NBT.A.1]
  - id: g5-nbt-powers-of-ten
    strand: Number & Operations in Base Ten
    title: Powers of ten
    description: Patterns when multiplying or dividing by powers of 10; whole-number exponents.
    prerequisites: [g5-nbt-place-value]
    standard_refs: [CCSS.5.NBT.A.2]
  - id: g5-nbt-round-decimals
    strand: Number & Operations in Base Ten
    title: Round decimals
    description: Use place value understanding to round decimals to any place.
    prerequisites: [g5-decimal-place-value]
    standard_refs: [CCSS.5.NBT.A.4]
  - id: g5-nbt-mult-multidigit
    strand: Number & Operations in Base Ten
    title: Multiply multi-digit whole numbers
    description: Fluently multiply multi-digit whole numbers using the standard algorithm.
    prerequisites: []
    standard_refs: [CCSS.5.NBT.B.5]
  - id: g5-nbt-divide-multidigit
    strand: Number & Operations in Base Ten
    title: Divide multi-digit whole numbers
    description: Find whole-number quotients with up to four-digit dividends and two-digit divisors.
    prerequisites: [g5-nbt-mult-multidigit]
    standard_refs: [CCSS.5.NBT.B.6]
```

- [ ] **Step 2: Append 12 items to `item_bank.yaml`**:

```yaml
  - id: NBT-PV-1
    points: [g5-nbt-place-value]
    difficulty: 1
    type: mcq
    prompt: "In 4,400 the left 4 is worth how many times the right 4?"
    options: {A: "10", B: "100", C: "1000", D: "2"}
    answer: "A"
  - id: NBT-PV-2
    points: [g5-nbt-place-value]
    difficulty: 2
    type: mcq
    prompt: "The 7 in 7,000 is how many times the 7 in 700?"
    options: {A: "10", B: "100", C: "1/10", D: "1000"}
    answer: "A"
  - id: NBT-PT-1
    points: [g5-nbt-powers-of-ten]
    difficulty: 1
    type: numeric
    prompt: "How many zeros are in the product 6 x 1000?"
    answer: "3"
  - id: NBT-PT-2
    points: [g5-nbt-powers-of-ten]
    difficulty: 2
    type: mcq
    prompt: "What is 10 to the power 3 (10^3)?"
    options: {A: "1000", B: "30", C: "100", D: "300"}
    answer: "A"
  - id: NBT-PT-3
    points: [g5-nbt-powers-of-ten]
    difficulty: 2
    type: numeric
    prompt: "3.5 x 100 = ?"
    answer: "350"
  - id: NBT-RD-1
    points: [g5-nbt-round-decimals]
    difficulty: 1
    type: numeric
    prompt: "Round 2.7 to the nearest whole number."
    answer: "3"
  - id: NBT-RD-2
    points: [g5-nbt-round-decimals]
    difficulty: 2
    type: numeric
    prompt: "Round 4.56 to the nearest tenth."
    answer: "4.6"
  - id: NBT-MM-1
    points: [g5-nbt-mult-multidigit]
    difficulty: 1
    type: numeric
    prompt: "23 x 4 = ?"
    answer: "92"
  - id: NBT-MM-2
    points: [g5-nbt-mult-multidigit]
    difficulty: 2
    type: numeric
    prompt: "34 x 12 = ?"
    answer: "408"
  - id: NBT-MM-3
    points: [g5-nbt-mult-multidigit]
    difficulty: 3
    type: numeric
    prompt: "125 x 16 = ?"
    answer: "2000"
  - id: NBT-DM-1
    points: [g5-nbt-divide-multidigit]
    difficulty: 1
    type: numeric
    prompt: "84 / 4 = ?"
    answer: "21"
  - id: NBT-DM-2
    points: [g5-nbt-divide-multidigit]
    difficulty: 2
    type: numeric
    prompt: "432 / 12 = ?"
    answer: "36"
```

- [ ] **Step 3: Append NBT responses to `sample_responses.yaml`** — demo student is strong in Base Ten (all correct):

```yaml
  NBT-PV-1: "A"
  NBT-PV-2: "A"
  NBT-PT-1: "3"
  NBT-PT-2: "A"
  NBT-PT-3: "350"
  NBT-RD-1: "3"
  NBT-RD-2: "4.6"
  NBT-MM-1: "92"
  NBT-MM-2: "408"
  NBT-MM-3: "2000"
  NBT-DM-1: "21"
  NBT-DM-2: "36"
```

- [ ] **Step 4: Bump the coverage test** — change the last three assertions to:

```python
    assert len(r.covered) == 18
    assert len(r.missing) == 8
    assert r.percentage == pytest.approx(18 / 26)
```

- [ ] **Step 5: Bump the CLI test** — change `assert "13 / 26" in out` to `assert "18 / 26" in out`.

- [ ] **Step 6: Run the suite**

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add curriculum/grade5_math tests/test_coverage.py tests/test_cli.py
git commit -m "feat(content): add Grade-5 Number & Operations in Base Ten (5.NBT) coverage"
```

---

## Task 5: Number & Operations—Fractions (5.NF) — 3 points

**Files:** same content files + the two test files.

**Interfaces:**
- Consumes: `g5-mult-fraction-fraction` (existing) as a prerequisite for `g5-nf-scaling`.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Append 3 points to `knowledge_map.yaml`**:

```yaml
  - id: g5-nf-fraction-as-division
    strand: Number & Operations—Fractions
    title: Fraction as division
    description: Interpret a fraction a/b as a divided by b.
    prerequisites: []
    standard_refs: [CCSS.5.NF.B.3]
  - id: g5-nf-scaling
    strand: Number & Operations—Fractions
    title: Multiplication as scaling
    description: Interpret multiplication as resizing without computing.
    prerequisites: [g5-mult-fraction-fraction]
    standard_refs: [CCSS.5.NF.B.5]
  - id: g5-nf-mult-realworld
    strand: Number & Operations—Fractions
    title: Real-world fraction multiplication
    description: Solve real-world problems multiplying fractions and mixed numbers.
    prerequisites: [g5-nf-scaling]
    standard_refs: [CCSS.5.NF.B.6]
```

- [ ] **Step 2: Append 6 items to `item_bank.yaml`**:

```yaml
  - id: NF-FD-1
    points: [g5-nf-fraction-as-division]
    difficulty: 1
    type: mcq
    prompt: "3/4 means the same as which division?"
    options: {A: "3 / 4", B: "4 / 3", C: "3 x 4", D: "4 - 3"}
    answer: "A"
  - id: NF-FD-2
    points: [g5-nf-fraction-as-division]
    difficulty: 2
    type: numeric
    prompt: "3 pizzas shared equally by 4 people: each person gets ?/4 of a pizza (enter the numerator)."
    answer: "3"
  - id: NF-SC-1
    points: [g5-nf-scaling]
    difficulty: 1
    type: mcq
    prompt: "Multiplying 8 by 1/2 gives a result that is..."
    options: {A: "smaller than 8", B: "larger than 8", C: "equal to 8", D: "zero"}
    answer: "A"
  - id: NF-SC-2
    points: [g5-nf-scaling]
    difficulty: 2
    type: mcq
    prompt: "5 x 3/2 is ___ 5."
    options: {A: "greater than", B: "less than", C: "equal to", D: "half of"}
    answer: "A"
  - id: NF-MR-1
    points: [g5-nf-mult-realworld]
    difficulty: 2
    type: numeric
    prompt: "A recipe needs 3/4 cup of sugar. For half a recipe you need ?/8 cup (enter the numerator)."
    answer: "3"
  - id: NF-MR-2
    points: [g5-nf-mult-realworld]
    difficulty: 2
    type: mcq
    prompt: "How long is 2/3 of a 9-foot rope?"
    options: {A: "6 feet", B: "3 feet", C: "9 feet", D: "18 feet"}
    answer: "A"
```

- [ ] **Step 3: Append NF responses to `sample_responses.yaml`** — demo student is weak in the new fraction points (all wrong):

```yaml
  NF-FD-1: "B"
  NF-FD-2: "4"
  NF-SC-1: "B"
  NF-SC-2: "B"
  NF-MR-1: "4"
  NF-MR-2: "B"
```

- [ ] **Step 4: Bump the coverage test** — change the last three assertions to:

```python
    assert len(r.covered) == 21
    assert len(r.missing) == 5
    assert r.percentage == pytest.approx(21 / 26)
```

- [ ] **Step 5: Bump the CLI test** — change `assert "18 / 26" in out` to `assert "21 / 26" in out`.

- [ ] **Step 6: Run the suite**

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add curriculum/grade5_math tests/test_coverage.py tests/test_cli.py
git commit -m "feat(content): complete Grade-5 Number & Operations—Fractions (5.NF) coverage"
```

---

## Task 6: Measurement & Data (5.MD) — 5 points (reaches 26/26)

**Files:** same content files + the two test files.

**Interfaces:**
- Consumes: `g5-add-unlike` (existing) as a prerequisite for `g5-md-line-plots`.
- Produces: full 26/26 coverage; this is the task that finalizes the coverage test to `missing == []`.

- [ ] **Step 1: Append 5 points to `knowledge_map.yaml`**:

```yaml
  - id: g5-md-unit-conversion
    strand: Measurement & Data
    title: Convert measurement units
    description: Convert among different-sized standard units within one system.
    prerequisites: []
    standard_refs: [CCSS.5.MD.A.1]
  - id: g5-md-line-plots
    strand: Measurement & Data
    title: Line plots with fractions
    description: Make and use line plots of measurements in fractions of a unit.
    prerequisites: [g5-add-unlike]
    standard_refs: [CCSS.5.MD.B.2]
  - id: g5-md-volume-concept
    strand: Measurement & Data
    title: Concept of volume
    description: Recognize volume as an attribute of solid figures, measured in cubic units.
    prerequisites: []
    standard_refs: [CCSS.5.MD.C.3]
  - id: g5-md-measure-volume
    strand: Measurement & Data
    title: Measure volume by counting cubes
    description: Measure volumes by counting unit cubes.
    prerequisites: [g5-md-volume-concept]
    standard_refs: [CCSS.5.MD.C.4]
  - id: g5-md-volume-formulas
    strand: Measurement & Data
    title: Volume formulas
    description: Relate volume to multiplication and addition; apply V = l x w x h.
    prerequisites: [g5-md-measure-volume]
    standard_refs: [CCSS.5.MD.C.5]
```

- [ ] **Step 2: Append 11 items to `item_bank.yaml`**:

```yaml
  - id: MD-UC-1
    points: [g5-md-unit-conversion]
    difficulty: 1
    type: numeric
    prompt: "How many centimeters are in 2 meters?"
    answer: "200"
  - id: MD-UC-2
    points: [g5-md-unit-conversion]
    difficulty: 2
    type: numeric
    prompt: "Convert 3 kilometers to meters."
    answer: "3000"
  - id: MD-LP-1
    points: [g5-md-line-plots]
    difficulty: 1
    type: mcq
    prompt: "A line plot displays data using marks above a..."
    options: {A: "number line", B: "circle", C: "bar", D: "table"}
    answer: "A"
  - id: MD-LP-2
    points: [g5-md-line-plots]
    difficulty: 2
    type: numeric
    prompt: "Three items measure 1/4, 1/4, and 1/2 unit. Their total is ?/4 (enter the numerator)."
    answer: "4"
  - id: MD-VC-1
    points: [g5-md-volume-concept]
    difficulty: 1
    type: mcq
    prompt: "Volume is measured in..."
    options: {A: "cubic units", B: "square units", C: "linear units", D: "degrees"}
    answer: "A"
  - id: MD-VC-2
    points: [g5-md-volume-concept]
    difficulty: 2
    type: mcq
    prompt: "A single unit cube has a volume of..."
    options: {A: "1 cubic unit", B: "4 cubic units", C: "0 cubic units", D: "6 cubic units"}
    answer: "A"
  - id: MD-MV-1
    points: [g5-md-measure-volume]
    difficulty: 1
    type: numeric
    prompt: "A box is filled with 2 layers of 6 unit cubes each. How many cubes in all?"
    answer: "12"
  - id: MD-MV-2
    points: [g5-md-measure-volume]
    difficulty: 2
    type: numeric
    prompt: "A solid is packed with unit cubes: 3 long, 2 wide, 2 high. How many cubes?"
    answer: "12"
  - id: MD-VF-1
    points: [g5-md-volume-formulas]
    difficulty: 1
    type: numeric
    prompt: "Volume of a box with l=4, w=3, h=2 (V = l x w x h)?"
    answer: "24"
  - id: MD-VF-2
    points: [g5-md-volume-formulas]
    difficulty: 2
    type: numeric
    prompt: "A prism has base area 10 and height 5. Its volume is?"
    answer: "50"
  - id: MD-VF-3
    points: [g5-md-volume-formulas]
    difficulty: 3
    type: numeric
    prompt: "Two stacked boxes have volumes 2x2x2 and 2x2x1. Their total volume is?"
    answer: "12"
```

- [ ] **Step 3: Append MD responses to `sample_responses.yaml`** — demo student is mixed (conversions + line plots strong, the whole volume chain weak):

```yaml
  MD-UC-1: "200"
  MD-UC-2: "3000"
  MD-LP-1: "A"
  MD-LP-2: "4"
  MD-VC-1: "B"
  MD-VC-2: "B"
  MD-MV-1: "10"
  MD-MV-2: "10"
  MD-VF-1: "20"
  MD-VF-2: "40"
  MD-VF-3: "10"
```

- [ ] **Step 4: Finalize the coverage test.** Replace `test_grade5_math_real_coverage` in `tests/test_coverage.py` with the full-coverage form:

```python
def test_grade5_math_real_coverage():
    from engine.loader import load_course
    c = load_course("curriculum/grade5_math", "schemas", "methodology", "standards")
    r = compute_coverage(c)
    assert r.total == 26
    assert len(r.covered) == 26
    assert r.missing == []
    assert r.percentage == 1.0
    assert "CCSS.5.G.A.1" in r.covered
    assert "CCSS.4.NF.A.1" in r.out_of_scope
    assert "CCSS.4.NF.A.1" not in r.covered
```

- [ ] **Step 5: Finalize the CLI test** — change `assert "21 / 26" in out` to `assert "26 / 26" in out`, and add `assert "100.0%" in out` on the next line.

- [ ] **Step 6: Run the suite**

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 7: Verify full coverage end to end**

Run: `python -m engine.cli --curriculum curriculum/grade5_math --coverage`
Expected: `26 / 26 standards covered (100.0%)` and `Missing (0): (none)`.

Run: `python -m engine.cli --curriculum curriculum/grade5_math --responses curriculum/grade5_math/sample_responses.yaml --name Sam --audience student`
Expected: a learning plan whose steps include the weak fraction and volume points, sequenced after their prerequisites.

- [ ] **Step 8: Commit**

```bash
git add curriculum/grade5_math tests/test_coverage.py tests/test_cli.py
git commit -m "feat(content): add Grade-5 Measurement & Data (5.MD), reaching 26/26 coverage"
```

---

## Notes for the implementer

- Append new points/items/responses; do not reorder or edit existing entries except the Task 1 strand relabels.
- After each task, the running coverage count must match the table at the top. If `test_grade5_math_real_coverage` fails on a count, a point's `standard_refs` is wrong or a code is duplicated — fix the content.
- Every math answer here has been worked out; if a numeric item looks off, re-derive and fix the `answer`, then re-run — do not weaken the test.
- The demo profile is intentional: strong Base Ten + Geometry, mixed OA + MD, weak new Fractions + the Volume chain. This keeps the learning path non-trivial and exercises prerequisite ordering.
