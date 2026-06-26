# Item Pool with Diagnostic/Practice Roles — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every item an explicit `role` (`diagnostic` | `practice`), drive the printed test/scoring from diagnostic items and the learning-path practice links from a separate practice pool, and author 2 practice items for each of the 28 Grade-5 knowledge points.

**Architecture:** A `role` field threads from the JSON Schema → loader → `Item` dataclass → `Curriculum` role-aware accessors. Consumers (`score`, `path`, `paper`) select by role. Content is migrated (existing 68 items become `diagnostic`) and grown (56 new `practice` items), with role-aware integrity tests as the gate. The pipeline stays a pure, deterministic function over per-course YAML.

**Tech Stack:** Python ≥3.10, pyyaml, jsonschema, jinja2, weasyprint, pytest. Package management via `uv`.

## Global Constraints

- Python `>=3.10`. Manage all packages with `uv` (`uv add` / `uv run`); never edit deps by hand or call `pip`. Run tests with `uv run pytest`.
- **Determinism is mandatory.** No selection/sampling: the test is *all* diagnostic items, practice is *all* practice items. Ordering is explicit (item-bank order; practice sorted by `(difficulty, id)`). No `set` iteration may reach output.
- **Single `item_bank.yaml` per course** — no directory split.
- A missing `role` defaults to `"diagnostic"` (the loader applies it; JSON Schema `default` is annotation-only).
- `Item` gains `role` as the **last** dataclass field with default `"diagnostic"`, so existing positional `Item(...)` construction stays valid.
- Practice-item IDs use the point's existing diagnostic prefix with a `-P` suffix (e.g. `EQF-1` → `EQF-P1`, `EQF-P2`; `G-CS-1` → `G-CS-P1`).
- Every authored item is math-verified, schema-valid, maps to exactly one point, and (for MCQ) has no distractor numerically equal to the keyed answer.
- No changes to coverage, bands, or scoring math. Report templates change only as needed to render now-populated practice links (no template edits are required in this plan).

## File Structure

- Modify `schemas/item_bank.schema.json` — add `role` enum.
- Modify `engine/models.py` — `Item.role`; `Curriculum.items_for_point(role=...)` + `diagnostic_items_for_point` / `practice_items_for_point`.
- Modify `engine/loader.py` — read `role` with default.
- Modify `engine/score.py` — score over the diagnostic universe.
- Modify `engine/path.py` — practice links from the practice pool.
- Modify `engine/paper.py` — test surfaces include only diagnostic items.
- Modify `curriculum/grade5_math/item_bank.yaml` — migrate roles; add 56 practice items.
- Modify `curriculum/_template/item_bank.yaml` + `curriculum/_template/AUTHORING.md` — document `role`.
- Modify tests: `test_schemas.py`, `test_models.py`, `test_loader.py`, `test_score.py`, `test_path.py`, `test_paper.py`, `test_content_integrity.py`.

---

### Task 1: Add `role` to the item schema

**Files:**
- Modify: `schemas/item_bank.schema.json`
- Test: `tests/test_schemas.py`

**Interfaces:**
- Produces: item objects may carry `role` ∈ {`diagnostic`, `practice`}; absence is allowed.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_schemas.py`:

```python
def test_item_bank_schema_accepts_role_and_rejects_bad_role():
    v = _validator("item_bank.schema.json")
    good = {"items": [{"id": "i1", "points": ["a"], "difficulty": 2,
                       "type": "mcq", "prompt": "?", "answer": "A", "role": "practice"}]}
    v.validate(good)
    no_role = {"items": [{"id": "i1", "points": ["a"], "difficulty": 2,
                          "type": "mcq", "prompt": "?", "answer": "A"}]}
    v.validate(no_role)  # role is optional
    bad = {"items": [{"id": "i1", "points": ["a"], "difficulty": 2,
                      "type": "mcq", "prompt": "?", "answer": "A", "role": "warmup"}]}
    assert list(v.iter_errors(bad))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_schemas.py::test_item_bank_schema_accepts_role_and_rejects_bad_role -v`
Expected: FAIL — `role: "warmup"` currently validates because `additionalProperties: false` rejects `role` entirely, so `good`/`no_role` paths fail first (KeyError-free assertion failure on `v.validate(good)`).

- [ ] **Step 3: Add `role` to the schema**

In `schemas/item_bank.schema.json`, add to the item `properties` (after `distractor_feedback`):

```json
          "role": {"enum": ["diagnostic", "practice"]}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_schemas.py -v`
Expected: PASS (all schema tests).

- [ ] **Step 5: Commit**

```bash
git add schemas/item_bank.schema.json tests/test_schemas.py
git commit -m "feat(schema): add optional item role (diagnostic|practice)"
```

---

### Task 2: `Item.role` field + loader default

**Files:**
- Modify: `engine/models.py` (`Item`)
- Modify: `engine/loader.py` (`_build_items`)
- Test: `tests/test_loader.py`

**Interfaces:**
- Consumes: schema `role` (Task 1).
- Produces: `Item.role: str` (default `"diagnostic"`); loader sets it from YAML.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_loader.py`:

```python
def test_items_get_role_with_default_diagnostic():
    from engine.loader import load_course
    c = load_course("curriculum/grade5_math", "schemas", "methodology", "standards")
    # every loaded item exposes a role; current content has none yet -> default
    assert all(it.role in ("diagnostic", "practice") for it in c.items.values())
    assert any(it.role == "diagnostic" for it in c.items.values())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_loader.py::test_items_get_role_with_default_diagnostic -v`
Expected: FAIL with `AttributeError: 'Item' object has no attribute 'role'`.

- [ ] **Step 3: Add the field and loader wiring**

In `engine/models.py`, add `role` as the **last** field of `Item`:

```python
@dataclass
class Item:
    id: str
    points: tuple[str, ...]
    difficulty: int
    type: str
    prompt: str
    answer: str
    options: dict[str, str] = field(default_factory=dict)
    distractor_feedback: dict[str, str] = field(default_factory=dict)
    role: str = "diagnostic"
```

In `engine/loader.py`, `_build_items`, add the `role` kwarg to the `Item(...)` construction:

```python
            distractor_feedback=it.get("distractor_feedback", {}),
            role=it.get("role", "diagnostic"),
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_loader.py tests/test_models.py -v`
Expected: PASS (default `role` does not disturb existing positional `Item(...)` construction).

- [ ] **Step 5: Commit**

```bash
git add engine/models.py engine/loader.py tests/test_loader.py
git commit -m "feat(model): Item.role with loader default 'diagnostic'"
```

---

### Task 3: Role-aware `Curriculum` accessors

**Files:**
- Modify: `engine/models.py` (`Curriculum`)
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: `Item.role` (Task 2).
- Produces:
  - `Curriculum.items_for_point(point_id: str, role: str | None = None) -> list[Item]`
  - `Curriculum.diagnostic_items_for_point(point_id: str) -> list[Item]`
  - `Curriculum.practice_items_for_point(point_id: str) -> list[Item]`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_models.py`:

```python
def test_items_for_point_filters_by_role():
    points = {"a": KnowledgePoint("a", "Number", "A", "d", (), ("X",))}
    items = {
        "d1": Item("d1", ("a",), 1, "mcq", "?", "A", {}, {}),                    # default diagnostic
        "d2": Item("d2", ("a",), 2, "mcq", "?", "A", {}, {}, role="diagnostic"),
        "p1": Item("p1", ("a",), 1, "mcq", "?", "A", {}, {}, role="practice"),
    }
    c = Curriculum(points=points, items=items, bands=(Band("Secure", 0.8),), standards={})
    assert [it.id for it in c.items_for_point("a")] == ["d1", "d2", "p1"]
    assert [it.id for it in c.diagnostic_items_for_point("a")] == ["d1", "d2"]
    assert [it.id for it in c.practice_items_for_point("a")] == ["p1"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models.py::test_items_for_point_filters_by_role -v`
Expected: FAIL with `TypeError: items_for_point() got an unexpected keyword argument` (via the helpers) / `AttributeError` on missing accessors.

- [ ] **Step 3: Update the accessors**

In `engine/models.py`, replace `Curriculum.items_for_point` and add two helpers:

```python
    def items_for_point(self, point_id: str, role: str | None = None) -> list[Item]:
        return [
            it for it in self.items.values()
            if point_id in it.points and (role is None or it.role == role)
        ]

    def diagnostic_items_for_point(self, point_id: str) -> list[Item]:
        return self.items_for_point(point_id, role="diagnostic")

    def practice_items_for_point(self, point_id: str) -> list[Item]:
        return self.items_for_point(point_id, role="practice")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_models.py -v`
Expected: PASS (the existing `test_items_for_point_matches_tagged_items` still passes — default `role=None`).

- [ ] **Step 5: Commit**

```bash
git add engine/models.py tests/test_models.py
git commit -m "feat(model): role-aware items_for_point accessors"
```

---

### Task 4: Score over the diagnostic universe

**Files:**
- Modify: `engine/score.py` (`evaluate`)
- Test: `tests/test_score.py`

**Interfaces:**
- Consumes: `Curriculum.diagnostic_items_for_point` (Task 3).
- Produces: `evaluate` ignores any non-diagnostic id present in `responses`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_score.py`:

```python
def test_practice_responses_are_ignored_by_scoring():
    points = {"a": KnowledgePoint("a", "Number", "A", "d", (), ("X",))}
    items = {
        "a1": Item("a1", ("a",), 1, "numeric", "?", "1", {}, {}),
        "a2": Item("a2", ("a",), 1, "numeric", "?", "2", {}, {}),
        "ap": Item("ap", ("a",), 1, "numeric", "?", "9", {}, {}, role="practice"),
    }
    bands = (Band("Secure", 0.8), Band("Developing", 0.5), Band("Not yet", 0.0))
    c = Curriculum(points=points, items=items, bands=bands, standards={"X": {}})
    # 'ap' is a practice item; even if (wrongly) present in responses it must not be scored
    result = evaluate(c, {"a1": "1", "a2": "2", "ap": "0"})
    pa = result.point_results["a"]
    assert pa.answered_count == 2           # only the two diagnostic items
    assert pa.mastery == 1.0                # 'ap' wrong answer did not drag it down
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_score.py::test_practice_responses_are_ignored_by_scoring -v`
Expected: FAIL — current `evaluate` uses `items_for_point` (all roles), so `ap` is counted (`answered_count == 3`, `mastery < 1.0`).

- [ ] **Step 3: Update `evaluate`**

In `engine/score.py`, in `evaluate`, change the `answered` line:

```python
        answered = [it for it in curriculum.diagnostic_items_for_point(pid) if it.id in responses]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_score.py -v`
Expected: PASS (existing tests unaffected — their items default to `diagnostic`).

- [ ] **Step 5: Commit**

```bash
git add engine/score.py tests/test_score.py
git commit -m "feat(score): evaluate over diagnostic items only"
```

---

### Task 5: Practice links from the practice pool

**Files:**
- Modify: `engine/path.py` (`build_path`)
- Test: `tests/test_path.py`

**Interfaces:**
- Consumes: `Curriculum.practice_items_for_point` (Task 3).
- Produces: each `PathStep.practice_item_ids` is the point's practice items, ordered by `(difficulty, id)`, independent of which diagnostic items were answered.

- [ ] **Step 1: Update the fixture and rewrite the practice test**

In `tests/test_path.py`, add a practice item to the `_curriculum()` fixture `items` dict (so point `a` has practice content):

```python
        "d1": Item("d1", ("d",), 1, "mcq", "?", "A", {}, {}),
        "ap1": Item("ap1", ("a",), 2, "mcq", "?", "A", {}, {}, role="practice"),
        "ap2": Item("ap2", ("a",), 1, "mcq", "?", "A", {}, {}, role="practice"),
```

Replace `test_practice_items_exclude_diagnostic_items_and_sort_by_difficulty` with:

```python
def test_practice_items_come_from_practice_pool_sorted_by_difficulty():
    c = _curriculum()
    result = _weak_result({"a"})
    result.answered_item_ids.add("a1")  # answering a diagnostic item must NOT change practice
    step = build_path(c, result)[0]
    assert step.practice_item_ids == ["ap2", "ap1"]  # difficulty 1 before 2; diagnostics excluded


def test_practice_items_empty_when_no_practice_pool():
    c = _curriculum()
    result = _weak_result({"d"})  # point d has no practice items
    step = build_path(c, result)[0]
    assert step.practice_item_ids == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_path.py -v`
Expected: FAIL — current `build_path` returns diagnostic ids (`a2`, etc.), not `["ap2", "ap1"]`.

- [ ] **Step 3: Update `build_path`**

In `engine/path.py`, replace the practice computation inside the `for pid in ordered:` loop:

```python
    steps: list[PathStep] = []
    for pid in ordered:
        practice = [
            it.id
            for it in sorted(curriculum.practice_items_for_point(pid),
                             key=lambda i: (i.difficulty, i.id))
        ]
        steps.append(PathStep(pid, curriculum.points[pid].title, practice))
    return steps
```

(The `result.answered_item_ids` reference is removed from this function; `result` stays a parameter.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_path.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/path.py tests/test_path.py
git commit -m "feat(path): practice links from the practice pool"
```

---

### Task 6: Test surfaces include only diagnostic items

**Files:**
- Modify: `engine/paper.py` (`ordered_groups`)
- Test: `tests/test_paper.py`

**Interfaces:**
- Consumes: `Item.role` (Task 2).
- Produces: `ordered_groups` / `ordered_items` / the print pack / `answers_blank.yaml` contain only `role == "diagnostic"` items.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_paper.py`:

```python
def test_print_surfaces_exclude_practice_items():
    from engine.paper import ordered_items, render_paper_html, render_answer_sheet_template
    points = {"a": KnowledgePoint("a", "Fractions", "Equivalent fractions", "d", (), ())}
    items = {
        "D1": Item("D1", ("a",), 1, "numeric", "Diagnostic prompt one", "1", {}, {}),
        "D2": Item("D2", ("a",), 2, "numeric", "Diagnostic prompt two", "2", {}, {}),
        "P1": Item("P1", ("a",), 1, "numeric", "Practice prompt hidden", "9", {}, {}, role="practice"),
    }
    bands = (Band("Secure", 0.8),)
    c = Curriculum(points=points, items=items, bands=bands, standards={})
    assert [it.id for it in ordered_items(c)] == ["D1", "D2"]   # practice excluded
    html = render_paper_html(c, TEMPLATES)
    assert "Diagnostic prompt one" in html
    assert "Practice prompt hidden" not in html
    blank = render_answer_sheet_template(c)
    assert "P1" not in blank and "D1" in blank
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_paper.py::test_print_surfaces_exclude_practice_items -v`
Expected: FAIL — `ordered_items` currently returns `["D1", "D2", "P1"]` and the practice prompt leaks into the paper.

- [ ] **Step 3: Filter `ordered_groups` to diagnostic items**

In `engine/paper.py`, in `ordered_groups`, skip non-diagnostic items when filling buckets:

```python
    for item in curriculum.items.values():  # item-bank (insertion) order
        if item.role != "diagnostic":
            continue
        if not item.points:
            continue
        primary = item.points[0]
        if primary in buckets:
            buckets[primary].append(item)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_paper.py -v`
Expected: PASS (existing paper tests use default-`diagnostic` items, so they are unaffected).

- [ ] **Step 5: Commit**

```bash
git add engine/paper.py tests/test_paper.py
git commit -m "feat(paper): print surfaces use diagnostic items only"
```

---

### Task 7: Migrate the 68 existing items to `role: diagnostic`

**Files:**
- Modify: `curriculum/grade5_math/item_bank.yaml`

**Interfaces:**
- Consumes: schema/loader role support (Tasks 1–2).
- Produces: every existing item carries explicit `role: diagnostic`; behavior unchanged.

- [ ] **Step 1: Add `role: diagnostic` to every item**

In `curriculum/grade5_math/item_bank.yaml`, add a `role: diagnostic` line to each of the 68 items (one line per item, aligned with the other fields, e.g. directly under the `id:` line). Every item from `EQF-1` through `MD-VF-3` gets it.

- [ ] **Step 2: Verify the migration loads and every item is diagnostic**

Run:

```bash
uv run python -c "from engine.loader import load_course; c=load_course('curriculum/grade5_math','schemas','methodology','standards'); print('items', len(c.items)); print('all diagnostic', all(it.role=='diagnostic' for it in c.items.values()))"
```

Expected: `items 68` and `all diagnostic True`.

- [ ] **Step 3: Run the full suite**

Run: `uv run pytest -q`
Expected: PASS (no behavior change — items were already treated as diagnostic by default).

- [ ] **Step 4: Commit**

```bash
git add curriculum/grade5_math/item_bank.yaml
git commit -m "content(g5): tag existing 68 items as role: diagnostic"
```

---

### Task 8: Author practice items — Fractions (9 points, 18 items)

**Files:**
- Modify: `curriculum/grade5_math/item_bank.yaml`

**Interfaces:**
- Consumes: role-aware accessors (Task 3).
- Produces: ≥2 `role: practice` items for each Fractions point.

Author **exactly 2** practice items per point below, each `role: practice`, IDs using the listed prefix + `-P1`/`-P2`, with one easier (difficulty 1–2) and one harder (difficulty 2–3), math-verified, distinct from the diagnostic items, and (for MCQ) with no distractor equal to the answer.

Points (prefix): `g5-equiv-fractions` (EQF), `g5-add-like` (ALK), `g5-add-unlike` (ALU), `g5-mult-fraction-whole` (MFW), `g5-mult-fraction-fraction` (MFF), `g5-divide-unit-fraction` (DUF), `g5-nf-fraction-as-division` (NF-FD), `g5-nf-scaling` (NF-SC), `g5-nf-mult-realworld` (NF-MR).

- [ ] **Step 1: Add the practice items**

Append each point's two practice items in `item_bank.yaml` directly after that point's diagnostic items, under a `# --- <point> (practice) ---` comment. Worked example for `g5-equiv-fractions` (follow this exact shape for all points):

```yaml
  # --- g5-equiv-fractions (practice) ---
  - id: EQF-P1
    points: [g5-equiv-fractions]
    difficulty: 1
    type: mcq
    role: practice
    prompt: "Which fraction is equal to 3/4?"
    options: {A: "6/8", B: "3/8", C: "4/3", D: "3/5"}
    answer: "A"
  - id: EQF-P2
    points: [g5-equiv-fractions]
    difficulty: 2
    type: numeric
    role: practice
    prompt: "Fill in the blank: 3/4 = ?/12  (enter the numerator)"
    answer: "9"
```

Author the remaining points the same way. Verify the math for each (e.g. `ALK`: `2/7 + 3/7 = 5/7`; `ALU`: `1/2 + 1/3 = 5/6`; `MFW`: `5 x 2/3 = 10/3`; `MFF`: `2/3 x 1/2 = 2/6`; `DUF`: `1/4 ÷ 2 = 1/8`; `NF-FD`: `5/8` means `5 ÷ 8`; `NF-SC`: `6 x 1/2 < 6`; `NF-MR`: `1/2 of 8 cups = 4`). Use numbers different from the diagnostic items.

- [ ] **Step 2: Verify schema, distractor guard, and ≥2 practice per point**

Run: `uv run pytest tests/test_content_integrity.py -v`
Expected: PASS (schema load + the MCQ ambiguous-distractor guard now cover the new items).

Then run:

```bash
uv run python -c "
from engine.loader import load_course
c=load_course('curriculum/grade5_math','schemas','methodology','standards')
pts=['g5-equiv-fractions','g5-add-like','g5-add-unlike','g5-mult-fraction-whole','g5-mult-fraction-fraction','g5-divide-unit-fraction','g5-nf-fraction-as-division','g5-nf-scaling','g5-nf-mult-realworld']
print({p: len(c.practice_items_for_point(p)) for p in pts})
"
```

Expected: every listed point maps to `2`.

- [ ] **Step 3: Commit**

```bash
git add curriculum/grade5_math/item_bank.yaml
git commit -m "content(g5): add Fractions practice items (18)"
```

---

### Task 9: Author practice items — Base Ten (7 points, 14 items)

**Files:**
- Modify: `curriculum/grade5_math/item_bank.yaml`

**Interfaces:**
- Produces: ≥2 `role: practice` items for each Base Ten point.

Same rules as Task 8. Points (prefix): `g5-decimal-place-value` (DPV), `g5-add-subtract-decimals` (ASD), `g5-nbt-place-value` (NBT-PV), `g5-nbt-powers-of-ten` (NBT-PT), `g5-nbt-round-decimals` (NBT-RD), `g5-nbt-mult-multidigit` (NBT-MM), `g5-nbt-divide-multidigit` (NBT-DM).

- [ ] **Step 1: Add the practice items**

Worked example for `g5-decimal-place-value`:

```yaml
  # --- g5-decimal-place-value (practice) ---
  - id: DPV-P1
    points: [g5-decimal-place-value]
    difficulty: 1
    type: mcq
    role: practice
    prompt: "What is the value of the 5 in 0.356?"
    options: {A: "5 tenths", B: "5 hundredths", C: "5 thousandths", D: "5 ones"}
    answer: "B"
  - id: DPV-P2
    points: [g5-decimal-place-value]
    difficulty: 2
    type: numeric
    role: practice
    prompt: "Write 'forty-two hundredths' as a decimal."
    answer: "0.42"
```

Author the rest (verify: `ASD`: `0.5 + 0.25 = 0.75`; `NBT-PV`: the 8 in 8,800 is `10x` the right 8; `NBT-PT`: `10^4 = 10000`; `NBT-RD`: round `3.14` to nearest tenth `3.1`; `NBT-MM`: `42 x 13 = 546`; `NBT-DM`: `96 / 8 = 12`). Numbers must differ from the diagnostic items.

- [ ] **Step 2: Verify**

Run: `uv run pytest tests/test_content_integrity.py -v`  → PASS.
Then:

```bash
uv run python -c "
from engine.loader import load_course
c=load_course('curriculum/grade5_math','schemas','methodology','standards')
pts=['g5-decimal-place-value','g5-add-subtract-decimals','g5-nbt-place-value','g5-nbt-powers-of-ten','g5-nbt-round-decimals','g5-nbt-mult-multidigit','g5-nbt-divide-multidigit']
print({p: len(c.practice_items_for_point(p)) for p in pts})
"
```

Expected: every listed point maps to `2`.

- [ ] **Step 3: Commit**

```bash
git add curriculum/grade5_math/item_bank.yaml
git commit -m "content(g5): add Base Ten practice items (14)"
```

---

### Task 10: Author practice items — Geometry (4 points, 8 items)

**Files:**
- Modify: `curriculum/grade5_math/item_bank.yaml`

**Interfaces:**
- Produces: ≥2 `role: practice` items for each Geometry point.

Same rules as Task 8. Points (prefix): `g5-coordinate-system` (G-CS), `g5-graph-points` (G-GP), `g5-figure-hierarchy` (G-FH), `g5-classify-figures` (G-CF).

- [ ] **Step 1: Add the practice items**

Worked example for `g5-coordinate-system`:

```yaml
  # --- g5-coordinate-system (practice) ---
  - id: G-CS-P1
    points: [g5-coordinate-system]
    difficulty: 1
    type: mcq
    role: practice
    prompt: "In the coordinate (x, y), which number tells how far UP to move?"
    options: {A: "the second number (y)", B: "the first number (x)", C: "neither", D: "both"}
    answer: "A"
  - id: G-CS-P2
    points: [g5-coordinate-system]
    difficulty: 2
    type: mcq
    role: practice
    prompt: "The point (0, 0) is called the..."
    options: {A: "origin", B: "x-axis label", C: "y-axis label", D: "first quadrant"}
    answer: "A"
```

Author the rest (verify: `G-GP`: to plot `(5, 1)` move up `1`; `G-FH`: every square is a rhombus; `G-CF`: a parallelogram with 4 right angles is a rectangle). Distinct from the diagnostic items.

- [ ] **Step 2: Verify**

Run: `uv run pytest tests/test_content_integrity.py -v`  → PASS.
Then:

```bash
uv run python -c "
from engine.loader import load_course
c=load_course('curriculum/grade5_math','schemas','methodology','standards')
pts=['g5-coordinate-system','g5-graph-points','g5-figure-hierarchy','g5-classify-figures']
print({p: len(c.practice_items_for_point(p)) for p in pts})
"
```

Expected: every listed point maps to `2`.

- [ ] **Step 3: Commit**

```bash
git add curriculum/grade5_math/item_bank.yaml
git commit -m "content(g5): add Geometry practice items (8)"
```

---

### Task 11: Author practice items — Operations & Algebraic Thinking (3 points, 6 items)

**Files:**
- Modify: `curriculum/grade5_math/item_bank.yaml`

**Interfaces:**
- Produces: ≥2 `role: practice` items for each OA point.

Same rules as Task 8. Points (prefix): `g5-oa-eval-expressions` (OA-EV), `g5-oa-write-expressions` (OA-WR), `g5-oa-patterns-graph` (OA-PG).

- [ ] **Step 1: Add the practice items**

Worked example for `g5-oa-eval-expressions`:

```yaml
  # --- g5-oa-eval-expressions (practice) ---
  - id: OA-EV-P1
    points: [g5-oa-eval-expressions]
    difficulty: 1
    type: numeric
    role: practice
    prompt: "Evaluate: 5 x (2 + 3)"
    answer: "25"
  - id: OA-EV-P2
    points: [g5-oa-eval-expressions]
    difficulty: 2
    type: numeric
    role: practice
    prompt: "Evaluate: 10 + 6 / 2"
    answer: "13"
```

Author the rest (verify: `OA-WR`: "subtract 3 from 10, then double" → `2 x (10 - 3)`; `OA-PG`: rule "add 5" from 0 gives `0,5,10,15`, the 4th term is `15`). Distinct from the diagnostic items.

- [ ] **Step 2: Verify**

Run: `uv run pytest tests/test_content_integrity.py -v`  → PASS.
Then:

```bash
uv run python -c "
from engine.loader import load_course
c=load_course('curriculum/grade5_math','schemas','methodology','standards')
pts=['g5-oa-eval-expressions','g5-oa-write-expressions','g5-oa-patterns-graph']
print({p: len(c.practice_items_for_point(p)) for p in pts})
"
```

Expected: every listed point maps to `2`.

- [ ] **Step 3: Commit**

```bash
git add curriculum/grade5_math/item_bank.yaml
git commit -m "content(g5): add OA practice items (6)"
```

---

### Task 12: Author practice items — Measurement & Data (5 points, 10 items)

**Files:**
- Modify: `curriculum/grade5_math/item_bank.yaml`

**Interfaces:**
- Produces: ≥2 `role: practice` items for each Measurement point.

Same rules as Task 8. Points (prefix): `g5-md-unit-conversion` (MD-UC), `g5-md-line-plots` (MD-LP), `g5-md-volume-concept` (MD-VC), `g5-md-measure-volume` (MD-MV), `g5-md-volume-formulas` (MD-VF).

- [ ] **Step 1: Add the practice items**

Worked example for `g5-md-unit-conversion`:

```yaml
  # --- g5-md-unit-conversion (practice) ---
  - id: MD-UC-P1
    points: [g5-md-unit-conversion]
    difficulty: 1
    type: numeric
    role: practice
    prompt: "How many centimeters are in 5 meters?"
    answer: "500"
  - id: MD-UC-P2
    points: [g5-md-unit-conversion]
    difficulty: 2
    type: numeric
    role: practice
    prompt: "Convert 4 kilometers to meters."
    answer: "4000"
```

Author the rest (verify: `MD-LP`: `1/4 + 1/4 + 1/4 = 3/4`, enter numerator `3`; `MD-VC`: volume is measured in cubic units; `MD-MV`: 3 layers of 4 cubes = `12`; `MD-VF`: box `l=5,w=2,h=3` → `V=30`). Distinct from the diagnostic items.

- [ ] **Step 2: Verify**

Run: `uv run pytest tests/test_content_integrity.py -v`  → PASS.
Then:

```bash
uv run python -c "
from engine.loader import load_course
c=load_course('curriculum/grade5_math','schemas','methodology','standards')
pts=['g5-md-unit-conversion','g5-md-line-plots','g5-md-volume-concept','g5-md-measure-volume','g5-md-volume-formulas']
print({p: len(c.practice_items_for_point(p)) for p in pts})
"
```

Expected: every listed point maps to `2`.

- [ ] **Step 3: Commit**

```bash
git add curriculum/grade5_math/item_bank.yaml
git commit -m "content(g5): add Measurement practice items (10)"
```

---

### Task 13: Role-aware integrity gate + template docs

**Files:**
- Modify: `tests/test_content_integrity.py`
- Modify: `curriculum/_template/item_bank.yaml`
- Modify: `curriculum/_template/AUTHORING.md`

**Interfaces:**
- Consumes: the migrated + authored content (Tasks 7–12).
- Produces: integrity tests enforcing explicit role, ≥2 diagnostic and ≥2 practice per point.

- [ ] **Step 1: Write the failing tests**

In `tests/test_content_integrity.py`, replace `test_every_point_has_at_least_two_items` with role-aware checks and add an explicit-role check:

```python
def test_every_point_has_at_least_two_diagnostic_items(curriculum):
    for pid in curriculum.points:
        assert len(curriculum.diagnostic_items_for_point(pid)) >= 2, \
            f"{pid} has < 2 diagnostic items"


def test_every_point_has_at_least_two_practice_items(curriculum):
    for pid in curriculum.points:
        assert len(curriculum.practice_items_for_point(pid)) >= 2, \
            f"{pid} has < 2 practice items"


def test_every_item_has_explicit_role(curriculum):
    import yaml
    raw = yaml.safe_load(open(f"{CURRICULUM_DIR}/item_bank.yaml"))["items"]
    for it in raw:
        assert it.get("role") in ("diagnostic", "practice"), \
            f"item {it['id']} is missing an explicit role"
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/test_content_integrity.py -v`
Expected: PASS — after Tasks 7–12 every point has ≥2 diagnostic and ≥2 practice items, and every item has an explicit role. (The existing MCQ ambiguous-distractor guard already covers all items.)

- [ ] **Step 3: Document `role` in the template**

In `curriculum/_template/item_bank.yaml`, add a `role:` line to the skeleton item with a comment, e.g.:

```yaml
    role: diagnostic   # diagnostic (on the test, scored) | practice (learning-path only)
```

In `curriculum/_template/AUTHORING.md`, add a short note under the item-bank section:

> Each item has a `role`: `diagnostic` items appear on the printed test and are scored;
> `practice` items are reserved for the learning-path practice links. Author at least 2 of
> each per knowledge point. A missing `role` defaults to `diagnostic`.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -q`
Expected: PASS (full suite green with the new gate).

- [ ] **Step 5: Commit**

```bash
git add tests/test_content_integrity.py curriculum/_template/item_bank.yaml curriculum/_template/AUTHORING.md
git commit -m "test(content): enforce role + >=2 diagnostic/practice per point; document role"
```

---

## Self-Review

**Spec coverage:**
- Schema `role` enum, optional → Task 1. ✓
- Loader default + `Item.role` last field → Task 2. ✓
- `items_for_point(role=...)` + diagnostic/practice accessors → Task 3. ✓
- Score over diagnostic universe → Task 4. ✓
- Path practice from practice pool, sorted `(difficulty, id)` → Task 5. ✓
- Test surfaces diagnostic-only (paper, blank YAML) → Task 6. ✓
- Migrate 68 → `role: diagnostic` → Task 7. ✓
- Author 2 practice/point across all 28 points (56 items) → Tasks 8–12 (18+14+8+6+10). ✓
- Report wiring renders populated practice links (no template change) → exercised by Task 5 (path) + existing `report_student.md.j2`; integration verifiable via CLI after content. ✓
- Integrity: explicit role, ≥2 diagnostic, ≥2 practice, distractor guard over all → Task 13. ✓
- Schema test (accept/reject role) → Task 1. ✓
- `_template` + AUTHORING role docs → Task 13. ✓
- Determinism / single-file / no new deps → Global Constraints; honored throughout. ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases"; every engine step shows full code; content tasks give a complete worked example plus an exhaustive point list and per-point verified math. ✓

**Type consistency:** `items_for_point(point_id, role=None)`, `diagnostic_items_for_point`, `practice_items_for_point` are defined in Task 3 and consumed with identical names/signatures in Tasks 4 (score), 5 (path), 13 (integrity). `Item(..., role="practice")` keyword construction is used consistently in Tasks 3/5/6 fixtures, valid because `role` is the last defaulted field (Task 2). `PathStep.practice_item_ids` ordering `(difficulty, id)` matches between Task 5 code and its test. ✓
