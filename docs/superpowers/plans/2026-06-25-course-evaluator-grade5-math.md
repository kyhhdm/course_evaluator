# Course Evaluator (Grade 5 Math) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a content + methodology evaluation system that turns a Grade 5 Math diagnostic into a status report (strands → knowledge points) and a prioritized, practice-linked learning path for students and parents.

**Architecture:** YAML content (knowledge map, standard mapping, item bank, bands) validated by JSON Schema + integrity tests, loaded into immutable dataclass models, then run through a thin deterministic Python engine: `score` (responses → per-point mastery → strand bands), `path` (weak points → prerequisite-sequenced learning path), and `report` (Jinja2 → parent/student markdown). A small CLI ties it end to end.

**Tech Stack:** Python 3.12, PyYAML, jsonschema (Draft 2020-12), Jinja2, pytest.

## Global Constraints

- Python `>=3.10` (uses `X | None` runtime annotations, builtin generics).
- Dependencies limited to: `pyyaml`, `jsonschema`, `jinja2` (runtime) and `pytest` (dev). No others.
- Engine output MUST be deterministic — no randomness, no wall-clock, stable sort order everywhere.
- All authored YAML content MUST pass its JSON Schema AND the content-integrity tests.
- Scoring is transparent difficulty-weighted thresholds (no IRT, no LLM judging).
- `MIN_ITEMS = 2`: a knowledge point with fewer than 2 answered items is reported as `insufficient_evidence`, never given a false score.
- Mastery band names, highest first: `Secure` (≥0.8), `Developing` (≥0.5), `Not yet` (≥0.0).

---

## File Structure

```
course_evaluator/
  pyproject.toml                       # project metadata, deps, pytest config
  curriculum/grade5_math/
    knowledge_map.yaml                 # points: strand, title, desc, prerequisites, standard_refs
    standard_mapping.yaml              # standards: code -> {framework, description}
    item_bank.yaml                     # items: points, difficulty, type, prompt, answer, ...
    bands.yaml                         # bands: name + min_score (descending)
    sample_responses.yaml              # a demo student's answers (for the CLI/integration test)
  engine/
    __init__.py
    models.py                          # KnowledgePoint, Item, Band, Curriculum, *Result, PathStep
    loader.py                          # load_yaml, validate, load_curriculum
    score.py                           # is_correct, evaluate
    path.py                            # impact, build_path
    report.py                          # render_parent, render_student
    cli.py                             # main(argv)
  templates/
    report_parent.md.j2
    report_student.md.j2
  schemas/
    knowledge_map.schema.json
    standard_mapping.schema.json
    item_bank.schema.json
    bands.schema.json
  tests/
    test_models.py
    test_schemas.py
    test_loader.py
    test_content_integrity.py
    test_score.py
    test_path.py
    test_report.py
    test_cli.py
```

---

## Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `engine/__init__.py` (empty)
- Test: `tests/test_models.py` (placeholder smoke test, replaced in Task 2)

**Interfaces:**
- Consumes: nothing.
- Produces: an installed, importable `engine` package and a working `pytest` run.

- [ ] **Step 1: Write the failing test**

`tests/test_models.py`:
```python
def test_engine_package_importable():
    import engine
    assert engine is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine'`

- [ ] **Step 3: Create the package and project config**

`engine/__init__.py`: empty file.

`pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "course-evaluator"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["pyyaml>=6.0", "jsonschema>=4.0", "jinja2>=3.0"]

[project.optional-dependencies]
dev = ["pytest>=7.0"]

[tool.setuptools]
packages = ["engine"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml engine/__init__.py tests/test_models.py
git commit -m "chore: scaffold course-evaluator package and pytest config"
```

---

## Task 2: Data models

**Files:**
- Create: `engine/models.py`
- Test: `tests/test_models.py` (replace Task 1 placeholder)

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `KnowledgePoint(id, strand, title, description, prerequisites: tuple[str,...], standard_refs: tuple[str,...])`
  - `Item(id, points: tuple[str,...], difficulty: int, type: str, prompt: str, answer: str, options: dict[str,str], distractor_feedback: dict[str,str])`
  - `Band(name: str, min_score: float)`
  - `PointResult(point_id, mastery: float|None, band: str|None, status: str, answered_count: int)`
  - `StrandResult(strand, band: str|None, average_mastery: float|None, weakest_point_id: str|None, point_results: list[PointResult])`
  - `EvaluationResult(strands: list[StrandResult], point_results: dict[str,PointResult], answered_item_ids: set[str])`
  - `PathStep(point_id: str, title: str, practice_item_ids: list[str])`
  - `Curriculum(points, items, bands, standards)` with methods `items_for_point(pid)->list[Item]`, `points_in_strand(strand)->list[KnowledgePoint]`, `band_for(score)->Band`, `strands()->list[str]`.

- [ ] **Step 1: Write the failing test**

Replace `tests/test_models.py` with:
```python
from engine.models import (
    KnowledgePoint, Item, Band, Curriculum,
    PointResult, StrandResult, EvaluationResult, PathStep,
)


def _curriculum():
    points = {
        "a": KnowledgePoint("a", "Number", "A", "desc", (), ("X",)),
        "b": KnowledgePoint("b", "Number", "B", "desc", ("a",), ("Y",)),
    }
    items = {
        "i1": Item("i1", ("a",), 1, "mcq", "?", "A", {"A": "x"}, {}),
        "i2": Item("i2", ("a", "b"), 3, "numeric", "?", "5", {}, {}),
    }
    bands = (Band("Secure", 0.8), Band("Developing", 0.5), Band("Not yet", 0.0))
    return Curriculum(points=points, items=items, bands=bands, standards={})


def test_items_for_point_matches_tagged_items():
    c = _curriculum()
    assert [it.id for it in c.items_for_point("a")] == ["i1", "i2"]
    assert [it.id for it in c.items_for_point("b")] == ["i2"]


def test_points_in_strand_returns_all_points():
    c = _curriculum()
    assert {p.id for p in c.points_in_strand("Number")} == {"a", "b"}


def test_band_for_picks_highest_band_at_or_below_score():
    c = _curriculum()
    assert c.band_for(0.95).name == "Secure"
    assert c.band_for(0.80).name == "Secure"
    assert c.band_for(0.79).name == "Developing"
    assert c.band_for(0.50).name == "Developing"
    assert c.band_for(0.10).name == "Not yet"


def test_result_dataclasses_construct():
    pr = PointResult("a", 0.9, "Secure", "scored", 3)
    sr = StrandResult("Number", "Secure", 0.9, "a", [pr])
    er = EvaluationResult([sr], {"a": pr}, {"i1"})
    ps = PathStep("a", "A", ["i2"])
    assert er.strands[0].weakest_point_id == "a"
    assert ps.practice_item_ids == ["i2"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError` / attributes missing.

- [ ] **Step 3: Write the implementation**

`engine/models.py`:
```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class KnowledgePoint:
    id: str
    strand: str
    title: str
    description: str
    prerequisites: tuple[str, ...] = ()
    standard_refs: tuple[str, ...] = ()


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


@dataclass
class Band:
    name: str
    min_score: float


@dataclass
class PointResult:
    point_id: str
    mastery: float | None
    band: str | None
    status: str  # "scored" | "insufficient_evidence"
    answered_count: int


@dataclass
class StrandResult:
    strand: str
    band: str | None
    average_mastery: float | None
    weakest_point_id: str | None
    point_results: list[PointResult]


@dataclass
class EvaluationResult:
    strands: list[StrandResult]
    point_results: dict[str, PointResult]
    answered_item_ids: set[str]


@dataclass
class PathStep:
    point_id: str
    title: str
    practice_item_ids: list[str]


@dataclass
class Curriculum:
    points: dict[str, KnowledgePoint]
    items: dict[str, Item]
    bands: tuple[Band, ...]  # sorted descending by min_score
    standards: dict[str, dict]

    def items_for_point(self, point_id: str) -> list[Item]:
        return [it for it in self.items.values() if point_id in it.points]

    def points_in_strand(self, strand: str) -> list[KnowledgePoint]:
        return [p for p in self.points.values() if p.strand == strand]

    def strands(self) -> list[str]:
        seen: list[str] = []
        for p in self.points.values():
            if p.strand not in seen:
                seen.append(p.strand)
        return seen

    def band_for(self, score: float) -> Band:
        for band in self.bands:  # already descending by min_score
            if score >= band.min_score:
                return band
        return self.bands[-1]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_models.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add engine/models.py tests/test_models.py
git commit -m "feat: add curriculum and result data models"
```

---

## Task 3: JSON Schemas

**Files:**
- Create: `schemas/knowledge_map.schema.json`
- Create: `schemas/standard_mapping.schema.json`
- Create: `schemas/item_bank.schema.json`
- Create: `schemas/bands.schema.json`
- Test: `tests/test_schemas.py`

**Interfaces:**
- Consumes: nothing.
- Produces: four JSON Schema files used by `loader.validate` (Task 4) and content checks. Each schema validates the corresponding YAML top-level shape.

- [ ] **Step 1: Write the failing test**

`tests/test_schemas.py`:
```python
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

SCHEMAS = Path("schemas")


def _validator(name):
    schema = json.loads((SCHEMAS / name).read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_knowledge_map_schema_accepts_valid_and_rejects_missing_id():
    v = _validator("knowledge_map.schema.json")
    good = {"points": [{"id": "a", "strand": "Number", "title": "A",
                        "description": "d", "prerequisites": [], "standard_refs": ["X"]}]}
    v.validate(good)
    bad = {"points": [{"strand": "Number", "title": "A",
                       "description": "d", "standard_refs": ["X"]}]}
    assert list(v.iter_errors(bad))


def test_item_bank_schema_enforces_difficulty_range():
    v = _validator("item_bank.schema.json")
    good = {"items": [{"id": "i1", "points": ["a"], "difficulty": 2,
                       "type": "mcq", "prompt": "?", "answer": "A"}]}
    v.validate(good)
    bad = {"items": [{"id": "i1", "points": ["a"], "difficulty": 9,
                      "type": "mcq", "prompt": "?", "answer": "A"}]}
    assert list(v.iter_errors(bad))


def test_bands_schema_requires_name_and_min_score():
    v = _validator("bands.schema.json")
    v.validate({"bands": [{"name": "Secure", "min_score": 0.8}]})
    assert list(v.iter_errors({"bands": [{"name": "Secure"}]}))


def test_standard_mapping_schema_requires_framework_and_description():
    v = _validator("standard_mapping.schema.json")
    v.validate({"standards": {"X": {"framework": "CC", "description": "d"}}})
    assert list(v.iter_errors({"standards": {"X": {"framework": "CC"}}}))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_schemas.py -v`
Expected: FAIL — `FileNotFoundError` (schemas not created yet).

- [ ] **Step 3: Write the schemas**

`schemas/knowledge_map.schema.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["points"],
  "properties": {
    "points": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "strand", "title", "description", "standard_refs"],
        "properties": {
          "id": {"type": "string"},
          "strand": {"type": "string"},
          "title": {"type": "string"},
          "description": {"type": "string"},
          "prerequisites": {"type": "array", "items": {"type": "string"}},
          "standard_refs": {"type": "array", "items": {"type": "string"}, "minItems": 1}
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

`schemas/standard_mapping.schema.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["standards"],
  "properties": {
    "standards": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["framework", "description"],
        "properties": {
          "framework": {"type": "string"},
          "description": {"type": "string"}
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

`schemas/item_bank.schema.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["items"],
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "points", "difficulty", "type", "prompt", "answer"],
        "properties": {
          "id": {"type": "string"},
          "points": {"type": "array", "items": {"type": "string"}, "minItems": 1},
          "difficulty": {"type": "integer", "minimum": 1, "maximum": 3},
          "type": {"enum": ["mcq", "numeric"]},
          "prompt": {"type": "string"},
          "answer": {"type": "string"},
          "options": {"type": "object", "additionalProperties": {"type": "string"}},
          "distractor_feedback": {"type": "object", "additionalProperties": {"type": "string"}}
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

`schemas/bands.schema.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["bands"],
  "properties": {
    "bands": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["name", "min_score"],
        "properties": {
          "name": {"type": "string"},
          "min_score": {"type": "number", "minimum": 0, "maximum": 1}
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_schemas.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add schemas tests/test_schemas.py
git commit -m "feat: add JSON schemas for curriculum content"
```

---

## Task 4: Curriculum loader

**Files:**
- Create: `engine/loader.py`
- Test: `tests/test_loader.py`

**Interfaces:**
- Consumes: `engine.models` (Task 2), `schemas/*.json` (Task 3).
- Produces:
  - `load_yaml(path: str | Path) -> dict`
  - `validate(data: dict, schema_path: str | Path) -> None` (raises `jsonschema.ValidationError` on failure)
  - `load_curriculum(curriculum_dir: str | Path, schemas_dir: str | Path) -> Curriculum`

`load_curriculum` reads `knowledge_map.yaml`, `standard_mapping.yaml`, `item_bank.yaml`, `bands.yaml`, validates each against its schema, builds and returns a `Curriculum` with `bands` sorted descending by `min_score`.

- [ ] **Step 1: Write the failing test**

`tests/test_loader.py`:
```python
from pathlib import Path

import pytest

from engine.loader import load_curriculum, validate, load_yaml


def _write_mini(dirpath: Path):
    (dirpath / "knowledge_map.yaml").write_text(
        "points:\n"
        "  - id: a\n    strand: Number\n    title: A\n    description: d\n"
        "    prerequisites: []\n    standard_refs: [X]\n"
        "  - id: b\n    strand: Number\n    title: B\n    description: d\n"
        "    prerequisites: [a]\n    standard_refs: [Y]\n"
    )
    (dirpath / "standard_mapping.yaml").write_text(
        "standards:\n"
        "  X: {framework: CC, description: dx}\n"
        "  Y: {framework: CC, description: dy}\n"
    )
    (dirpath / "item_bank.yaml").write_text(
        "items:\n"
        "  - id: i1\n    points: [a]\n    difficulty: 1\n    type: mcq\n"
        "    prompt: '?'\n    answer: A\n    options: {A: x, B: y}\n"
        "  - id: i2\n    points: [a, b]\n    difficulty: 3\n    type: numeric\n"
        "    prompt: '?'\n    answer: '5'\n"
    )
    (dirpath / "bands.yaml").write_text(
        "bands:\n"
        "  - {name: Developing, min_score: 0.5}\n"
        "  - {name: Secure, min_score: 0.8}\n"
        "  - {name: Not yet, min_score: 0.0}\n"
    )


def test_load_curriculum_builds_models(tmp_path):
    _write_mini(tmp_path)
    c = load_curriculum(tmp_path, "schemas")
    assert set(c.points) == {"a", "b"}
    assert c.points["b"].prerequisites == ("a",)
    assert c.items["i1"].options == {"A": "x", "B": "y"}
    assert c.standards["X"]["description"] == "dx"


def test_load_curriculum_sorts_bands_descending(tmp_path):
    _write_mini(tmp_path)
    c = load_curriculum(tmp_path, "schemas")
    assert [b.name for b in c.bands] == ["Secure", "Developing", "Not yet"]


def test_validate_raises_on_bad_content(tmp_path):
    from jsonschema import ValidationError
    bad = {"points": [{"strand": "Number"}]}
    with pytest.raises(ValidationError):
        validate(bad, "schemas/knowledge_map.schema.json")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_loader.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.loader'`

- [ ] **Step 3: Write the implementation**

`engine/loader.py`:
```python
from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from engine.models import Band, Curriculum, Item, KnowledgePoint


def load_yaml(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate(data: dict, schema_path: str | Path) -> None:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(data)


def load_curriculum(curriculum_dir: str | Path, schemas_dir: str | Path) -> Curriculum:
    cdir, sdir = Path(curriculum_dir), Path(schemas_dir)

    km = load_yaml(cdir / "knowledge_map.yaml")
    sm = load_yaml(cdir / "standard_mapping.yaml")
    ib = load_yaml(cdir / "item_bank.yaml")
    bd = load_yaml(cdir / "bands.yaml")

    validate(km, sdir / "knowledge_map.schema.json")
    validate(sm, sdir / "standard_mapping.schema.json")
    validate(ib, sdir / "item_bank.schema.json")
    validate(bd, sdir / "bands.schema.json")

    points = {
        p["id"]: KnowledgePoint(
            id=p["id"],
            strand=p["strand"],
            title=p["title"],
            description=p["description"],
            prerequisites=tuple(p.get("prerequisites", [])),
            standard_refs=tuple(p["standard_refs"]),
        )
        for p in km["points"]
    }
    items = {
        it["id"]: Item(
            id=it["id"],
            points=tuple(it["points"]),
            difficulty=it["difficulty"],
            type=it["type"],
            prompt=it["prompt"],
            answer=str(it["answer"]),
            options=it.get("options", {}),
            distractor_feedback=it.get("distractor_feedback", {}),
        )
        for it in ib["items"]
    }
    bands = tuple(
        sorted(
            (Band(b["name"], float(b["min_score"])) for b in bd["bands"]),
            key=lambda b: b.min_score,
            reverse=True,
        )
    )
    return Curriculum(points=points, items=items, bands=bands, standards=sm["standards"])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_loader.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add engine/loader.py tests/test_loader.py
git commit -m "feat: add curriculum loader with schema validation"
```

---

## Task 5: Author Grade 5 Math content

**Files:**
- Create: `curriculum/grade5_math/knowledge_map.yaml`
- Create: `curriculum/grade5_math/standard_mapping.yaml`
- Create: `curriculum/grade5_math/item_bank.yaml`
- Create: `curriculum/grade5_math/bands.yaml`
- Create: `curriculum/grade5_math/sample_responses.yaml`
- Test: `tests/test_content_integrity.py`

**Interfaces:**
- Consumes: `engine.loader.load_curriculum` (Task 4).
- Produces: the real Grade 5 Math curriculum used by the CLI/integration test (Task 9), and integrity tests guaranteeing internal consistency.

This task authors the content first (so the file exists), then adds the integrity tests that lock it down. Both the schema (via the loader) and the integrity tests gate correctness.

- [ ] **Step 1: Author `bands.yaml`**

`curriculum/grade5_math/bands.yaml`:
```yaml
bands:
  - name: Secure
    min_score: 0.8
  - name: Developing
    min_score: 0.5
  - name: "Not yet"
    min_score: 0.0
```

- [ ] **Step 2: Author `standard_mapping.yaml`**

`curriculum/grade5_math/standard_mapping.yaml`:
```yaml
standards:
  CCSS.4.NF.A.1:
    framework: Common Core
    description: Explain why a fraction a/b equals (n*a)/(n*b); recognize equivalent fractions.
  CCSS.5.NF.A.1:
    framework: Common Core
    description: Add and subtract fractions with unlike denominators.
  CCSS.5.NF.A.2:
    framework: Common Core
    description: Solve word problems adding/subtracting fractions with like and unlike denominators.
  CCSS.5.NF.B.4:
    framework: Common Core
    description: Multiply a fraction by a whole number or by another fraction.
  CCSS.5.NF.B.7:
    framework: Common Core
    description: Divide unit fractions by whole numbers and whole numbers by unit fractions.
  CCSS.5.NBT.A.3:
    framework: Common Core
    description: Read, write, and compare decimals to thousandths.
  CCSS.5.NBT.B.7:
    framework: Common Core
    description: Add, subtract, multiply, and divide decimals to hundredths.
```

- [ ] **Step 3: Author `knowledge_map.yaml`**

`curriculum/grade5_math/knowledge_map.yaml`:
```yaml
points:
  - id: g5-equiv-fractions
    strand: Number & Operations
    title: Equivalent fractions
    description: Recognize and generate equivalent fractions by scaling numerator and denominator.
    prerequisites: []
    standard_refs: [CCSS.4.NF.A.1]
  - id: g5-add-like
    strand: Number & Operations
    title: Add and subtract fractions with like denominators
    description: Add and subtract fractions that already share a denominator.
    prerequisites: []
    standard_refs: [CCSS.5.NF.A.1]
  - id: g5-add-unlike
    strand: Number & Operations
    title: Add and subtract fractions with unlike denominators
    description: Find a common denominator, then add or subtract.
    prerequisites: [g5-equiv-fractions, g5-add-like]
    standard_refs: [CCSS.5.NF.A.1, CCSS.5.NF.A.2]
  - id: g5-mult-fraction-whole
    strand: Number & Operations
    title: Multiply a fraction by a whole number
    description: Compute a whole number times a fraction as repeated addition / scaling.
    prerequisites: [g5-add-like]
    standard_refs: [CCSS.5.NF.B.4]
  - id: g5-mult-fraction-fraction
    strand: Number & Operations
    title: Multiply a fraction by a fraction
    description: Multiply numerators and denominators; interpret as a part of a part.
    prerequisites: [g5-mult-fraction-whole]
    standard_refs: [CCSS.5.NF.B.4]
  - id: g5-divide-unit-fraction
    strand: Number & Operations
    title: Divide with unit fractions
    description: Divide a unit fraction by a whole number and a whole number by a unit fraction.
    prerequisites: [g5-mult-fraction-fraction]
    standard_refs: [CCSS.5.NF.B.7]
  - id: g5-decimal-place-value
    strand: Number & Operations
    title: Decimal place value to thousandths
    description: Read, write, and compare decimals to the thousandths place.
    prerequisites: []
    standard_refs: [CCSS.5.NBT.A.3]
  - id: g5-add-subtract-decimals
    strand: Number & Operations
    title: Add and subtract decimals
    description: Align place values to add and subtract decimals to hundredths.
    prerequisites: [g5-decimal-place-value]
    standard_refs: [CCSS.5.NBT.B.7]
```

- [ ] **Step 4: Author `item_bank.yaml`** (3 items per point, 24 total)

`curriculum/grade5_math/item_bank.yaml`:
```yaml
items:
  # --- g5-equiv-fractions ---
  - id: EQF-1
    points: [g5-equiv-fractions]
    difficulty: 1
    type: mcq
    prompt: "Which fraction is equal to 1/2?"
    options: {A: "2/3", B: "3/6", C: "1/3", D: "2/5"}
    answer: "B"
    distractor_feedback: {A: "Numerator and denominator must scale by the same factor."}
  - id: EQF-2
    points: [g5-equiv-fractions]
    difficulty: 2
    type: mcq
    prompt: "Which fraction is NOT equal to 3/4?"
    options: {A: "6/8", B: "9/12", C: "12/16", D: "4/5"}
    answer: "D"
  - id: EQF-3
    points: [g5-equiv-fractions]
    difficulty: 3
    type: numeric
    prompt: "Fill in the blank: 2/5 = ?/20"
    answer: "8"
  # --- g5-add-like ---
  - id: ALK-1
    points: [g5-add-like]
    difficulty: 1
    type: numeric
    prompt: "1/5 + 2/5 = ?/5  (enter the numerator)"
    answer: "3"
  - id: ALK-2
    points: [g5-add-like]
    difficulty: 2
    type: mcq
    prompt: "7/8 - 3/8 = ?"
    options: {A: "4/8", B: "4/0", C: "10/8", D: "4/16"}
    answer: "A"
  - id: ALK-3
    points: [g5-add-like]
    difficulty: 3
    type: numeric
    prompt: "5/6 - 1/6 - 1/6 = ?/6  (enter the numerator)"
    answer: "3"
  # --- g5-add-unlike ---
  - id: ALU-1
    points: [g5-add-unlike]
    difficulty: 1
    type: mcq
    prompt: "1/2 + 1/4 = ?"
    options: {A: "2/6", B: "3/4", C: "1/6", D: "2/4"}
    answer: "B"
  - id: ALU-2
    points: [g5-add-unlike]
    difficulty: 2
    type: mcq
    prompt: "2/3 - 1/6 = ?"
    options: {A: "1/3", B: "1/2", C: "3/6", D: "1/6"}
    answer: "B"
  - id: ALU-3
    points: [g5-add-unlike]
    difficulty: 3
    type: numeric
    prompt: "3/4 + 1/6 = ?/12  (enter the numerator)"
    answer: "11"
  # --- g5-mult-fraction-whole ---
  - id: MFW-1
    points: [g5-mult-fraction-whole]
    difficulty: 1
    type: numeric
    prompt: "3 x 1/4 = ?/4  (enter the numerator)"
    answer: "3"
  - id: MFW-2
    points: [g5-mult-fraction-whole]
    difficulty: 2
    type: mcq
    prompt: "4 x 2/5 = ?"
    options: {A: "8/5", B: "6/5", C: "8/20", D: "2/20"}
    answer: "A"
  - id: MFW-3
    points: [g5-mult-fraction-whole]
    difficulty: 3
    type: mcq
    prompt: "A recipe needs 2/3 cup of flour. How much for 3 batches?"
    options: {A: "2 cups", B: "6/3 cup but not 2", C: "2/9 cup", D: "5/3 cup"}
    answer: "A"
  # --- g5-mult-fraction-fraction ---
  - id: MFF-1
    points: [g5-mult-fraction-fraction]
    difficulty: 1
    type: mcq
    prompt: "1/2 x 1/3 = ?"
    options: {A: "1/6", B: "2/3", C: "1/5", D: "2/6"}
    answer: "A"
  - id: MFF-2
    points: [g5-mult-fraction-fraction]
    difficulty: 2
    type: numeric
    prompt: "2/3 x 3/4 = ?/12  (enter the numerator)"
    answer: "6"
  - id: MFF-3
    points: [g5-mult-fraction-fraction]
    difficulty: 3
    type: mcq
    prompt: "What is 3/5 of 2/3?"
    options: {A: "6/15", B: "5/8", C: "6/8", D: "2/5"}
    answer: "A"
  # --- g5-divide-unit-fraction ---
  - id: DUF-1
    points: [g5-divide-unit-fraction]
    difficulty: 1
    type: mcq
    prompt: "1/3 divided by 2 = ?"
    options: {A: "1/6", B: "2/3", C: "1/5", D: "3/2"}
    answer: "A"
  - id: DUF-2
    points: [g5-divide-unit-fraction]
    difficulty: 2
    type: numeric
    prompt: "6 divided by 1/2 = ?"
    answer: "12"
  - id: DUF-3
    points: [g5-divide-unit-fraction]
    difficulty: 3
    type: mcq
    prompt: "How many 1/4-cup scoops are in 3 cups?"
    options: {A: "12", B: "7", C: "3/4", D: "4"}
    answer: "A"
  # --- g5-decimal-place-value ---
  - id: DPV-1
    points: [g5-decimal-place-value]
    difficulty: 1
    type: mcq
    prompt: "What is the value of the 7 in 0.275?"
    options: {A: "7 tenths", B: "7 hundredths", C: "7 thousandths", D: "7 ones"}
    answer: "B"
  - id: DPV-2
    points: [g5-decimal-place-value]
    difficulty: 2
    type: mcq
    prompt: "Which is larger: 0.4 or 0.38?"
    options: {A: "0.4", B: "0.38", C: "they are equal", D: "cannot tell"}
    answer: "A"
  - id: DPV-3
    points: [g5-decimal-place-value]
    difficulty: 3
    type: numeric
    prompt: "Write 'three hundred twelve thousandths' as a decimal."
    answer: "0.312"
  # --- g5-add-subtract-decimals ---
  - id: ASD-1
    points: [g5-add-subtract-decimals]
    difficulty: 1
    type: numeric
    prompt: "0.3 + 0.4 = ?"
    answer: "0.7"
  - id: ASD-2
    points: [g5-add-subtract-decimals]
    difficulty: 2
    type: numeric
    prompt: "1.25 + 0.6 = ?"
    answer: "1.85"
  - id: ASD-3
    points: [g5-add-subtract-decimals]
    difficulty: 3
    type: numeric
    prompt: "5 - 2.35 = ?"
    answer: "2.65"
```

- [ ] **Step 5: Author `sample_responses.yaml`** (a demo student: strong on decimals, weak on fractions)

`curriculum/grade5_math/sample_responses.yaml`:
```yaml
responses:
  EQF-1: "B"
  EQF-2: "D"
  EQF-3: "8"
  ALK-1: "3"
  ALK-2: "A"
  ALK-3: "3"
  ALU-1: "A"
  ALU-2: "A"
  ALU-3: "10"
  MFW-1: "3"
  MFW-2: "B"
  MFW-3: "A"
  MFF-1: "B"
  MFF-2: "5"
  MFF-3: "B"
  DUF-1: "B"
  DUF-2: "10"
  DUF-3: "B"
  DPV-1: "B"
  DPV-2: "A"
  DPV-3: "0.312"
  ASD-1: "0.7"
  ASD-2: "1.85"
  ASD-3: "2.65"
```

- [ ] **Step 6: Write the content-integrity test**

`tests/test_content_integrity.py`:
```python
import pytest

from engine.loader import load_curriculum

CURRICULUM_DIR = "curriculum/grade5_math"
SCHEMAS_DIR = "schemas"


@pytest.fixture(scope="module")
def curriculum():
    return load_curriculum(CURRICULUM_DIR, SCHEMAS_DIR)


def test_prerequisites_reference_existing_points(curriculum):
    ids = set(curriculum.points)
    for p in curriculum.points.values():
        for pre in p.prerequisites:
            assert pre in ids, f"{p.id} has unknown prerequisite {pre}"


def test_no_prerequisite_cycles(curriculum):
    points = curriculum.points
    WHITE, GREY, BLACK = 0, 1, 2
    color = {pid: WHITE for pid in points}

    def visit(pid):
        color[pid] = GREY
        for pre in points[pid].prerequisites:
            if color[pre] == GREY:
                raise AssertionError(f"cycle through {pid} -> {pre}")
            if color[pre] == WHITE:
                visit(pre)
        color[pid] = BLACK

    for pid in points:
        if color[pid] == WHITE:
            visit(pid)


def test_every_point_has_at_least_two_items(curriculum):
    for pid in curriculum.points:
        assert len(curriculum.items_for_point(pid)) >= 2, f"{pid} has < 2 items"


def test_every_item_references_existing_points(curriculum):
    ids = set(curriculum.points)
    for it in curriculum.items.values():
        for pid in it.points:
            assert pid in ids, f"item {it.id} references unknown point {pid}"


def test_every_standard_ref_exists_in_mapping(curriculum):
    codes = set(curriculum.standards)
    for p in curriculum.points.values():
        for ref in p.standard_refs:
            assert ref in codes, f"{p.id} references unknown standard {ref}"


def test_sample_responses_only_reference_real_items(curriculum):
    from engine.loader import load_yaml
    responses = load_yaml(f"{CURRICULUM_DIR}/sample_responses.yaml")["responses"]
    for item_id in responses:
        assert item_id in curriculum.items, f"response references unknown item {item_id}"
```

- [ ] **Step 7: Run the integrity tests**

Run: `python -m pytest tests/test_content_integrity.py -v`
Expected: PASS (6 tests). If any fail, fix the YAML content (not the test).

- [ ] **Step 8: Commit**

```bash
git add curriculum/grade5_math tests/test_content_integrity.py
git commit -m "feat: author Grade 5 Math curriculum content with integrity tests"
```

---

## Task 6: Scoring engine

**Files:**
- Create: `engine/score.py`
- Test: `tests/test_score.py`

**Interfaces:**
- Consumes: `engine.models` (Task 2).
- Produces:
  - `is_correct(item: Item, response: str | None) -> bool`
  - `evaluate(curriculum: Curriculum, responses: dict[str, str]) -> EvaluationResult`
  - module constant `MIN_ITEMS = 2`

`evaluate` computes per-point `mastery = sum(difficulty*correct)/sum(difficulty)` over answered items; points with `< MIN_ITEMS` answered items get `status="insufficient_evidence"`, `mastery=None`, `band=None`. Strand rollup uses the average mastery of scored points, banded via `curriculum.band_for`, with `weakest_point_id` = scored point of lowest mastery (ties broken by point id).

- [ ] **Step 1: Write the failing test**

`tests/test_score.py`:
```python
import pytest

from engine.models import Band, Curriculum, Item, KnowledgePoint
from engine.score import evaluate, is_correct, MIN_ITEMS


def _curriculum():
    points = {
        "a": KnowledgePoint("a", "Number", "A", "d", (), ("X",)),
        "b": KnowledgePoint("b", "Number", "B", "d", ("a",), ("X",)),
    }
    items = {
        "a1": Item("a1", ("a",), 1, "mcq", "?", "A", {"A": "x"}, {}),
        "a2": Item("a2", ("a",), 3, "numeric", "?", "10", {}, {}),
        "b1": Item("b1", ("b",), 1, "numeric", "?", "2", {}, {}),
        "b2": Item("b2", ("b",), 1, "numeric", "?", "3", {}, {}),
    }
    bands = (Band("Secure", 0.8), Band("Developing", 0.5), Band("Not yet", 0.0))
    return Curriculum(points=points, items=items, bands=bands, standards={"X": {}})


def test_is_correct_handles_mcq_case_insensitively():
    item = Item("x", ("a",), 1, "mcq", "?", "B", {"B": "y"}, {})
    assert is_correct(item, "b") is True
    assert is_correct(item, "C") is False
    assert is_correct(item, None) is False


def test_is_correct_handles_numeric_equivalence():
    item = Item("x", ("a",), 1, "numeric", "?", "0.7", {}, {})
    assert is_correct(item, "0.70") is True
    assert is_correct(item, "0.7") is True
    assert is_correct(item, "0.8") is False


def test_difficulty_weighted_mastery():
    c = _curriculum()
    # a1 (diff1) wrong, a2 (diff3) right -> 3/4 = 0.75 -> Developing
    result = evaluate(c, {"a1": "Z", "a2": "10", "b1": "2", "b2": "3"})
    pa = result.point_results["a"]
    assert pa.mastery == 0.75
    assert pa.band == "Developing"
    pb = result.point_results["b"]
    assert pb.mastery == 1.0
    assert pb.band == "Secure"


def test_insufficient_evidence_when_too_few_items_answered():
    c = _curriculum()
    result = evaluate(c, {"a1": "A"})  # only 1 of point a's items, none of b
    assert result.point_results["a"].status == "insufficient_evidence"
    assert result.point_results["a"].mastery is None
    assert result.point_results["b"].status == "insufficient_evidence"


def test_strand_rollup_averages_and_flags_weakest():
    c = _curriculum()
    result = evaluate(c, {"a1": "Z", "a2": "10", "b1": "2", "b2": "3"})
    strand = result.strands[0]
    assert strand.strand == "Number"
    assert strand.average_mastery == pytest.approx(0.875)
    assert strand.weakest_point_id == "a"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_score.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.score'`

- [ ] **Step 3: Write the implementation**

`engine/score.py`:
```python
from __future__ import annotations

from engine.models import (
    Curriculum,
    EvaluationResult,
    Item,
    PointResult,
    StrandResult,
)

MIN_ITEMS = 2


def is_correct(item: Item, response: str | None) -> bool:
    if response is None:
        return False
    given = str(response).strip()
    expected = str(item.answer).strip()
    if item.type == "numeric":
        try:
            return float(given) == float(expected)
        except ValueError:
            return given == expected
    return given.lower() == expected.lower()


def evaluate(curriculum: Curriculum, responses: dict[str, str]) -> EvaluationResult:
    point_results: dict[str, PointResult] = {}
    for pid, point in curriculum.points.items():
        answered = [it for it in curriculum.items_for_point(pid) if it.id in responses]
        if len(answered) < MIN_ITEMS:
            point_results[pid] = PointResult(pid, None, None, "insufficient_evidence", len(answered))
            continue
        numerator = sum(it.difficulty * (1 if is_correct(it, responses[it.id]) else 0) for it in answered)
        denominator = sum(it.difficulty for it in answered)
        mastery = numerator / denominator
        band = curriculum.band_for(mastery).name
        point_results[pid] = PointResult(pid, mastery, band, "scored", len(answered))

    strands = _build_strands(curriculum, point_results)
    answered_item_ids = {it_id for it_id in responses if it_id in curriculum.items}
    return EvaluationResult(strands=strands, point_results=point_results, answered_item_ids=answered_item_ids)


def _build_strands(curriculum: Curriculum, point_results: dict[str, PointResult]) -> list[StrandResult]:
    strands: list[StrandResult] = []
    for strand in curriculum.strands():
        prs = [point_results[p.id] for p in curriculum.points_in_strand(strand)]
        scored = [pr for pr in prs if pr.status == "scored"]
        if scored:
            average = sum(pr.mastery for pr in scored) / len(scored)
            band = curriculum.band_for(average).name
            weakest = min(scored, key=lambda pr: (pr.mastery, pr.point_id)).point_id
        else:
            average, band, weakest = None, None, None
        strands.append(StrandResult(strand, band, average, weakest, prs))
    return strands
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_score.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add engine/score.py tests/test_score.py
git commit -m "feat: add difficulty-weighted threshold scoring engine"
```

---

## Task 7: Learning path

**Files:**
- Create: `engine/path.py`
- Test: `tests/test_path.py`

**Interfaces:**
- Consumes: `engine.models` (Task 2), `EvaluationResult` from `engine.score` (Task 6).
- Produces:
  - `impact(curriculum: Curriculum, point_id: str) -> int` (direct downstream dependents)
  - `build_path(curriculum: Curriculum, result: EvaluationResult) -> list[PathStep]`

`build_path` selects scored, non-`Secure` points; orders them by prerequisites (a weak prerequisite comes before its weak dependent) using Kahn's algorithm; breaks ties by descending `impact`, then by point id. Each step lists practice item ids for that point (sorted by ascending difficulty), excluding items already used diagnostically (`result.answered_item_ids`).

- [ ] **Step 1: Write the failing test**

`tests/test_path.py`:
```python
from engine.models import (
    Band, Curriculum, EvaluationResult, Item, KnowledgePoint, PointResult,
)
from engine.path import build_path, impact


def _curriculum():
    points = {
        "a": KnowledgePoint("a", "Number", "A", "d", (), ("X",)),
        "b": KnowledgePoint("b", "Number", "B", "d", ("a",), ("X",)),
        "c": KnowledgePoint("c", "Number", "C", "d", ("b",), ("X",)),
        "d": KnowledgePoint("d", "Number", "D", "d", (), ("X",)),
    }
    items = {
        "a1": Item("a1", ("a",), 1, "mcq", "?", "A", {}, {}),
        "a2": Item("a2", ("a",), 3, "mcq", "?", "A", {}, {}),
        "b1": Item("b1", ("b",), 2, "mcq", "?", "A", {}, {}),
        "d1": Item("d1", ("d",), 1, "mcq", "?", "A", {}, {}),
    }
    bands = (Band("Secure", 0.8), Band("Developing", 0.5), Band("Not yet", 0.0))
    return Curriculum(points=points, items=items, bands=bands, standards={"X": {}})


def _weak_result(weak_points):
    prs = {}
    for pid in ["a", "b", "c", "d"]:
        if pid in weak_points:
            prs[pid] = PointResult(pid, 0.4, "Not yet", "scored", 2)
        else:
            prs[pid] = PointResult(pid, 0.9, "Secure", "scored", 2)
    return EvaluationResult([], prs, answered_item_ids=set())


def test_impact_counts_direct_dependents():
    c = _curriculum()
    assert impact(c, "a") == 1  # b depends on a
    assert impact(c, "b") == 1  # c depends on b
    assert impact(c, "d") == 0


def test_path_orders_prerequisites_before_dependents():
    c = _curriculum()
    result = _weak_result({"a", "b", "c"})
    order = [step.point_id for step in build_path(c, result)]
    assert order.index("a") < order.index("b") < order.index("c")


def test_path_excludes_secure_points():
    c = _curriculum()
    result = _weak_result({"a"})
    order = [step.point_id for step in build_path(c, result)]
    assert order == ["a"]


def test_path_tie_break_by_impact_then_id():
    c = _curriculum()
    # a (impact 1, has dependent b which is Secure here) vs d (impact 0): a first
    result = _weak_result({"a", "d"})
    order = [step.point_id for step in build_path(c, result)]
    assert order == ["a", "d"]


def test_practice_items_exclude_diagnostic_items_and_sort_by_difficulty():
    c = _curriculum()
    result = _weak_result({"a"})
    result.answered_item_ids.add("a1")  # a1 already used diagnostically
    step = build_path(c, result)[0]
    assert step.practice_item_ids == ["a2"]  # a1 excluded, a2 kept
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_path.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.path'`

- [ ] **Step 3: Write the implementation**

`engine/path.py`:
```python
from __future__ import annotations

from engine.models import Curriculum, EvaluationResult, PathStep


def impact(curriculum: Curriculum, point_id: str) -> int:
    return sum(1 for p in curriculum.points.values() if point_id in p.prerequisites)


def build_path(curriculum: Curriculum, result: EvaluationResult) -> list[PathStep]:
    secure = curriculum.bands[0].name
    weak = [
        pid
        for pid, pr in result.point_results.items()
        if pr.status == "scored" and pr.band != secure
    ]
    weak_set = set(weak)

    indeg = {
        pid: sum(1 for pre in curriculum.points[pid].prerequisites if pre in weak_set)
        for pid in weak
    }
    remaining = set(weak)
    ordered: list[str] = []
    while remaining:
        ready = [pid for pid in remaining if indeg[pid] == 0]
        if not ready:  # safety: integrity tests forbid cycles, but never loop forever
            ready = list(remaining)
        ready.sort(key=lambda p: (-impact(curriculum, p), p))
        chosen = ready[0]
        ordered.append(chosen)
        remaining.remove(chosen)
        for q in remaining:
            if chosen in curriculum.points[q].prerequisites:
                indeg[q] -= 1

    steps: list[PathStep] = []
    for pid in ordered:
        practice = [
            it.id
            for it in sorted(curriculum.items_for_point(pid), key=lambda i: i.difficulty)
            if it.id not in result.answered_item_ids
        ]
        steps.append(PathStep(pid, curriculum.points[pid].title, practice))
    return steps
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_path.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add engine/path.py tests/test_path.py
git commit -m "feat: add prerequisite-sequenced learning path builder"
```

---

## Task 8: Reports

**Files:**
- Create: `templates/report_parent.md.j2`
- Create: `templates/report_student.md.j2`
- Create: `engine/report.py`
- Test: `tests/test_report.py`

**Interfaces:**
- Consumes: `engine.models` (Task 2). Templates live in `templates/`.
- Produces:
  - `render_parent(curriculum, result, path, templates_dir, student_name="Student") -> str`
  - `render_student(curriculum, result, path, templates_dir, student_name="Student") -> str`

- [ ] **Step 1: Write the failing test**

`tests/test_report.py`:
```python
from engine.models import (
    Band, Curriculum, EvaluationResult, Item, KnowledgePoint, PathStep,
    PointResult, StrandResult,
)
from engine.report import render_parent, render_student

TEMPLATES = "templates"


def _setup():
    points = {
        "a": KnowledgePoint("a", "Number", "Equivalent fractions", "d", (), ("X",)),
        "b": KnowledgePoint("b", "Number", "Add fractions", "d", ("a",), ("X",)),
    }
    items = {"b2": Item("b2", ("b",), 1, "mcq", "Add 1/2 + 1/4?", "B", {}, {})}
    bands = (Band("Secure", 0.8), Band("Developing", 0.5), Band("Not yet", 0.0))
    curriculum = Curriculum(points=points, items=items, bands=bands, standards={"X": {}})
    pa = PointResult("a", 0.9, "Secure", "scored", 2)
    pb = PointResult("b", 0.4, "Not yet", "scored", 2)
    strand = StrandResult("Number", "Developing", 0.65, "b", [pa, pb])
    result = EvaluationResult([strand], {"a": pa, "b": pb}, {"b1"})
    path = [PathStep("b", "Add fractions", ["b2"])]
    return curriculum, result, path


def test_parent_report_shows_strand_band_and_focus():
    curriculum, result, path = _setup()
    out = render_parent(curriculum, result, path, TEMPLATES, "Sam")
    assert "Sam" in out
    assert "Number" in out
    assert "Developing" in out
    assert "Add fractions" in out


def test_student_report_lists_steps_and_practice_prompt():
    curriculum, result, path = _setup()
    out = render_student(curriculum, result, path, TEMPLATES, "Sam")
    assert "Step 1" in out
    assert "Add fractions" in out
    assert "Add 1/2 + 1/4?" in out


def test_reports_handle_empty_path():
    curriculum, result, _ = _setup()
    out = render_student(curriculum, result, [], TEMPLATES, "Sam")
    assert "no gaps" in out.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_report.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.report'`

- [ ] **Step 3: Write the templates**

`templates/report_parent.md.j2`:
```jinja
# Learning Report for {{ name }}

## Where {{ name }} stands

{% for s in strands -%}
- **{{ s.strand }}**: {{ s.band or "Not enough evidence yet" }}
{% endfor %}
## What this means

{{ name }} is Secure in {{ secure_count }} of {{ strands | length }} area(s).
{% if focus %}The most useful next focus is **{{ focus[0].title }}**.{% else %}No specific gaps were found right now.{% endif %}

## Focus next

{% if focus -%}
{% for step in focus -%}
{{ loop.index }}. **{{ step.title }}**
{% endfor -%}
{% else -%}
Nothing specific to fix right now — keep practicing to stay sharp.
{% endif %}
```

`templates/report_student.md.j2`:
```jinja
# Your Learning Plan, {{ name }}

## Your results by area

{% for s in strands -%}
- **{{ s.strand }}**: {{ s.band or "Not enough evidence yet" }}
{% endfor %}
## Your step-by-step plan

{% if path -%}
{% for step in path %}
### Step {{ loop.index }}: {{ step.title }}

Practice these:
{% for item_id in step.practice_item_ids -%}
- {{ items[item_id].prompt }}
{% endfor -%}
{% if not step.practice_item_ids -%}
- (No extra practice items available yet for this skill.)
{% endif -%}
{% endfor %}
{% else -%}
Great work — no gaps to fix right now.
{% endif %}
```

- [ ] **Step 4: Write the implementation**

`engine/report.py`:
```python
from __future__ import annotations

from jinja2 import Environment, FileSystemLoader

from engine.models import Curriculum, EvaluationResult, PathStep


def _env(templates_dir: str) -> Environment:
    return Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_parent(
    curriculum: Curriculum,
    result: EvaluationResult,
    path: list[PathStep],
    templates_dir: str,
    student_name: str = "Student",
) -> str:
    secure_count = sum(1 for s in result.strands if s.band == curriculum.bands[0].name)
    tmpl = _env(templates_dir).get_template("report_parent.md.j2")
    return tmpl.render(
        name=student_name,
        strands=result.strands,
        focus=path[:3],
        secure_count=secure_count,
    )


def render_student(
    curriculum: Curriculum,
    result: EvaluationResult,
    path: list[PathStep],
    templates_dir: str,
    student_name: str = "Student",
) -> str:
    tmpl = _env(templates_dir).get_template("report_student.md.j2")
    return tmpl.render(
        name=student_name,
        strands=result.strands,
        path=path,
        items=curriculum.items,
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_report.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add templates engine/report.py tests/test_report.py
git commit -m "feat: add parent and student report rendering"
```

---

## Task 9: CLI end-to-end

**Files:**
- Create: `engine/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `load_curriculum` (Task 4), `evaluate` (Task 6), `build_path` (Task 7), `render_parent`/`render_student` (Task 8), and the authored content + `sample_responses.yaml` (Task 5).
- Produces: `main(argv: list[str] | None = None) -> int` that prints a rendered report to stdout.

- [ ] **Step 1: Write the failing test**

`tests/test_cli.py`:
```python
from engine.cli import main

BASE = [
    "--curriculum", "curriculum/grade5_math",
    "--schemas", "schemas",
    "--responses", "curriculum/grade5_math/sample_responses.yaml",
    "--templates", "templates",
    "--name", "Sam",
]


def test_cli_parent_report_runs_end_to_end(capsys):
    code = main(BASE + ["--audience", "parent"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Learning Report for Sam" in out
    assert "Number & Operations" in out


def test_cli_student_report_includes_a_plan(capsys):
    code = main(BASE + ["--audience", "student"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Your Learning Plan, Sam" in out
    assert "Step 1" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.cli'`

- [ ] **Step 3: Write the implementation**

`engine/cli.py`:
```python
from __future__ import annotations

import argparse

from engine.loader import load_curriculum, load_yaml
from engine.path import build_path
from engine.report import render_parent, render_student
from engine.score import evaluate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a student's diagnostic responses.")
    parser.add_argument("--curriculum", required=True)
    parser.add_argument("--schemas", required=True)
    parser.add_argument("--responses", required=True)
    parser.add_argument("--templates", required=True)
    parser.add_argument("--name", default="Student")
    parser.add_argument("--audience", choices=["parent", "student"], default="parent")
    args = parser.parse_args(argv)

    curriculum = load_curriculum(args.curriculum, args.schemas)
    responses = load_yaml(args.responses)["responses"]
    result = evaluate(curriculum, responses)
    path = build_path(curriculum, result)

    if args.audience == "parent":
        print(render_parent(curriculum, result, path, args.templates, args.name))
    else:
        print(render_student(curriculum, result, path, args.templates, args.name))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Run the full suite + a manual smoke run**

Run: `python -m pytest -v`
Expected: ALL tests pass.

Run: `python -m engine.cli --curriculum curriculum/grade5_math --schemas schemas --responses curriculum/grade5_math/sample_responses.yaml --templates templates --name Sam --audience student`
Expected: a printed learning plan with steps for the fraction points the demo student missed.

- [ ] **Step 6: Commit**

```bash
git add engine/cli.py tests/test_cli.py
git commit -m "feat: add end-to-end evaluation CLI"
```

---

## Notes for the implementer

- Run `python -m pytest` from the repo root so `pythonpath = ["."]` (from `pyproject.toml`) makes `engine` importable without installation.
- If a content-integrity test fails in Task 5, the bug is in the YAML content, not the test — fix the content.
- The demo student in `sample_responses.yaml` is intentionally strong on decimals and weak on fractions, so the learning path is non-empty and demonstrates prerequisite ordering (equivalent fractions / add-like before add-unlike, etc.).
- Keep every list sort key explicit (as written) — this is what guarantees deterministic output.
