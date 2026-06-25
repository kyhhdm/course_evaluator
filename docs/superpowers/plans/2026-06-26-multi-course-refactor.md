# Multi-Course Refactor & Standards Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separate shared principles (bands, standards catalog, methodology) from per-course material, add a per-course manifest, and add an informational standards-coverage report so curriculum coverage is measurable per course.

**Architecture:** Lift `bands.yaml` to `methodology/` and the standards mapping to a shared `standards/ccss_math.yaml` catalog with `framework/grade/domain/description`. Each course gains a `course.yaml` manifest declaring `(framework, grade)`, which defines the coverage denominator. A new `engine/coverage.py` computes a `CoverageReport`; the loader gains `load_catalog`/`load_bands`/`load_course` (replacing `load_curriculum`); the CLI gains `--coverage`. Scoring/path/report behavior is unchanged.

**Tech Stack:** Python 3.12, PyYAML, jsonschema (Draft 2020-12), Jinja2, pytest.

## Global Constraints

- Python `>=3.10`. Dependencies limited to `pyyaml`, `jsonschema`, `jinja2` (runtime), `pytest` (dev). No others.
- Engine output deterministic — stable sort order everywhere (coverage lists are always `sorted`).
- Coverage is **informational only** — it never fails a test or blocks on low coverage.
- Mastery bands highest-first: `Secure` (≥0.8), `Developing` (≥0.5), `Not yet` (≥0.0).
- Bands resolution: shared `methodology/bands.yaml` default; `curriculum/<course>/bands.yaml` overrides it only if that file exists.
- The coverage denominator is the catalog entries whose `framework == course.framework` AND `grade == course.grade`. Referenced codes outside that slice (e.g. grade-4 prerequisites) are reported as `out_of_scope`, never counted in the denominator.
- Catalog filename convention: `framework.lower().replace("-", "_") + ".yaml"` (e.g. `CCSS-Math` → `ccss_math.yaml`).
- Standard codes keep their framework prefix as the catalog key (e.g. `CCSS.5.NF.A.1`); grade comes from the explicit `grade` field, never parsed from the code.
- Run tests as `python -m pytest` from the repo root.

---

## File Structure

```
methodology/
  bands.yaml                 # NEW (moved from course in Task 6); created Task 5
  METHODOLOGY.md             # NEW (Task 7)
standards/
  ccss_math.yaml             # NEW (Task 5) — full CCSS Grade-5 catalog + grade-4 prereqs in use
curriculum/
  _template/                 # NEW (Task 7) — skeleton + AUTHORING.md
  grade5_math/
    course.yaml              # NEW (Task 5)
    knowledge_map.yaml       # unchanged
    item_bank.yaml           # unchanged
    sample_responses.yaml    # unchanged
    bands.yaml               # DELETED in Task 6 (moved to methodology/)
    standard_mapping.yaml     # DELETED in Task 6 (replaced by shared catalog)
engine/
  models.py                  # Task 1: + Standard, CourseMeta, CoverageReport; Curriculum.meta
  loader.py                  # Task 3: + load_catalog, load_bands, load_course, _build_points, _build_items
  coverage.py                # NEW (Task 4): compute_coverage, format_coverage
  cli.py                     # Task 6: load_course + --coverage + shared-dir flags
schemas/
  course.schema.json         # NEW (Task 2)
  standards_catalog.schema.json  # NEW (Task 2); standard_mapping.schema.json DELETED in Task 6
tests/
  test_models.py             # Task 1 (extend)
  test_schemas.py            # Task 2 (extend), Task 6 (drop obsolete test)
  test_loader.py             # Task 3 (extend), Task 6 (drop load_curriculum tests)
  test_coverage.py           # NEW (Task 4 unit; Task 5 real-content)
  test_standards_catalog.py  # NEW (Task 5)
  test_content_integrity.py  # Task 6 (switch to load_course)
  test_cli.py                # Task 6 (new flags + coverage)
  test_template.py           # NEW (Task 7)
README.md                    # Task 7
```

---

## Task 1: Models — Standard, CourseMeta, CoverageReport, Curriculum.meta

**Files:**
- Modify: `engine/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: nothing new.
- Produces:
  - `Standard(framework: str, grade: str, domain: str, description: str)`
  - `CourseMeta(id: str, name: str, framework: str, grade: str)`
  - `CoverageReport(framework: str, grade: str, total: int, covered: list[str], missing: list[str], out_of_scope: list[str], percentage: float)`
  - `Curriculum` now has `standards: dict[str, Standard]` and `meta: CourseMeta | None = None`.

- [ ] **Step 1: Write the failing test** — append to `tests/test_models.py`:

```python
from engine.models import Standard, CourseMeta, CoverageReport


def test_new_dataclasses_construct():
    std = Standard("CCSS-Math", "5", "Number & Operations—Fractions", "Add unlike fractions")
    meta = CourseMeta("grade5_math", "Grade 5 Mathematics", "CCSS-Math", "5")
    rep = CoverageReport("CCSS-Math", "5", 26, ["a"], ["b"], ["c"], 0.5)
    assert std.grade == "5"
    assert meta.framework == "CCSS-Math"
    assert rep.total == 26 and rep.percentage == 0.5


def test_curriculum_accepts_meta_and_defaults_none():
    from engine.models import Curriculum, Band
    c = Curriculum(points={}, items={}, bands=(Band("Secure", 0.8),), standards={})
    assert c.meta is None
    c2 = Curriculum(points={}, items={}, bands=(Band("Secure", 0.8),), standards={},
                    meta=CourseMeta("i", "n", "CCSS-Math", "5"))
    assert c2.meta.grade == "5"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models.py -v`
Expected: FAIL — `ImportError: cannot import name 'Standard'`.

- [ ] **Step 3: Add the dataclasses** — in `engine/models.py`, insert these three dataclasses immediately **before** the `Curriculum` class (so `Standard`/`CourseMeta` are defined before `Curriculum` references them):

```python
@dataclass
class Standard:
    framework: str
    grade: str
    domain: str
    description: str


@dataclass
class CourseMeta:
    id: str
    name: str
    framework: str
    grade: str


@dataclass
class CoverageReport:
    framework: str
    grade: str
    total: int
    covered: list[str]
    missing: list[str]
    out_of_scope: list[str]
    percentage: float
```

- [ ] **Step 4: Update the `Curriculum` fields** — change the `standards` annotation and add `meta`. Replace:

```python
    bands: tuple[Band, ...]  # sorted descending by min_score
    standards: dict[str, dict]
```

with:

```python
    bands: tuple[Band, ...]  # sorted descending by min_score
    standards: dict[str, Standard]
    meta: CourseMeta | None = None
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_models.py -v`
Expected: PASS (all model tests, old and new).

- [ ] **Step 6: Run the full suite** (confirm no regression — score/path/report build `Curriculum` with keyword args and `standards={...}`, which still works)

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add engine/models.py tests/test_models.py
git commit -m "feat: add Standard, CourseMeta, CoverageReport models"
```

---

## Task 2: Schemas — standards catalog + course manifest

**Files:**
- Create: `schemas/standards_catalog.schema.json`
- Create: `schemas/course.schema.json`
- Test: `tests/test_schemas.py` (extend)

**Interfaces:**
- Consumes: nothing.
- Produces: two JSON Schemas used by the loader (Task 3) and content tasks. The catalog schema requires each standard to have `framework`, `grade`, `domain`, `description`. The course schema requires `id`, `name`, `framework`, `grade`.

- [ ] **Step 1: Write the failing test** — append to `tests/test_schemas.py`:

```python
def test_standards_catalog_schema_requires_all_fields():
    v = _validator("standards_catalog.schema.json")
    good = {"standards": {"CCSS.5.NF.A.1": {"framework": "CCSS-Math", "grade": 5,
                                            "domain": "Fractions", "description": "d"}}}
    v.validate(good)
    bad = {"standards": {"CCSS.5.NF.A.1": {"framework": "CCSS-Math", "description": "d"}}}
    assert list(v.iter_errors(bad))


def test_course_schema_requires_manifest_fields():
    v = _validator("course.schema.json")
    v.validate({"id": "grade5_math", "name": "Grade 5 Math", "framework": "CCSS-Math", "grade": 5})
    assert list(v.iter_errors({"id": "grade5_math", "name": "Grade 5 Math"}))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_schemas.py -v`
Expected: FAIL — `FileNotFoundError` for the new schema files.

- [ ] **Step 3: Create `schemas/standards_catalog.schema.json`**:

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
        "required": ["framework", "grade", "domain", "description"],
        "properties": {
          "framework": {"type": "string"},
          "grade": {"type": ["string", "integer"]},
          "domain": {"type": "string"},
          "description": {"type": "string"}
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 4: Create `schemas/course.schema.json`**:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["id", "name", "framework", "grade"],
  "properties": {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "framework": {"type": "string"},
    "grade": {"type": ["string", "integer"]}
  },
  "additionalProperties": false
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_schemas.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add schemas/standards_catalog.schema.json schemas/course.schema.json tests/test_schemas.py
git commit -m "feat: add standards-catalog and course-manifest schemas"
```

---

## Task 3: Loader — load_catalog, load_bands, load_course

**Files:**
- Modify: `engine/loader.py`
- Test: `tests/test_loader.py` (extend)

**Interfaces:**
- Consumes: `Band`, `Curriculum`, `Item`, `KnowledgePoint`, `Standard`, `CourseMeta` from `engine.models`; the schemas from Task 2.
- Produces:
  - `load_catalog(path, schema_path) -> dict[str, Standard]`
  - `load_bands(default_path, override_path, schema_path) -> tuple[Band, ...]` (override wins only if it exists)
  - `load_course(course_dir, schemas_dir, methodology_dir, standards_dir) -> Curriculum` (carries `meta`)
  - `_build_points(km_data) -> dict[str, KnowledgePoint]`, `_build_items(ib_data) -> dict[str, Item]` (shared helpers)
  - `load_curriculum` retained for now (refactored to use the helpers); removed in Task 6.

- [ ] **Step 1: Write the failing test** — append to `tests/test_loader.py`:

```python
from engine.loader import load_catalog, load_bands, load_course


def _write_shared(tmp_path):
    course = tmp_path / "course"
    method = tmp_path / "methodology"
    standards = tmp_path / "standards"
    for d in (course, method, standards):
        d.mkdir()
    (course / "course.yaml").write_text(
        "id: c1\nname: Course One\nframework: CCSS-Math\ngrade: 5\n")
    (course / "knowledge_map.yaml").write_text(
        "points:\n  - id: a\n    strand: Number\n    title: A\n    description: d\n"
        "    prerequisites: []\n    standard_refs: [CCSS.5.NF.A.1]\n")
    (course / "item_bank.yaml").write_text(
        "items:\n  - id: i1\n    points: [a]\n    difficulty: 1\n    type: numeric\n"
        "    prompt: '?'\n    answer: '1'\n")
    (method / "bands.yaml").write_text(
        "bands:\n  - {name: Developing, min_score: 0.5}\n"
        "  - {name: Secure, min_score: 0.8}\n  - {name: Not yet, min_score: 0.0}\n")
    (standards / "ccss_math.yaml").write_text(
        "standards:\n"
        "  CCSS.5.NF.A.1: {framework: CCSS-Math, grade: 5, domain: Fractions, description: d}\n")
    return course, method, standards


def test_load_catalog_builds_standard_objects(tmp_path):
    _, _, standards = _write_shared(tmp_path)
    cat = load_catalog(standards / "ccss_math.yaml", "schemas/standards_catalog.schema.json")
    assert cat["CCSS.5.NF.A.1"].grade == "5"
    assert cat["CCSS.5.NF.A.1"].domain == "Fractions"


def test_load_bands_uses_override_when_present(tmp_path):
    _, method, _ = _write_shared(tmp_path)
    override = tmp_path / "override.yaml"
    override.write_text("bands:\n  - {name: Secure, min_score: 0.9}\n")
    bands = load_bands(method / "bands.yaml", override, "schemas/bands.schema.json")
    assert [b.name for b in bands] == ["Secure"]  # override file won
    missing = tmp_path / "nope.yaml"
    bands2 = load_bands(method / "bands.yaml", missing, "schemas/bands.schema.json")
    assert [b.name for b in bands2] == ["Secure", "Developing", "Not yet"]  # default


def test_load_course_wires_everything(tmp_path):
    course, method, standards = _write_shared(tmp_path)
    c = load_course(course, "schemas", method, standards)
    assert c.meta.framework == "CCSS-Math" and c.meta.grade == "5"
    assert set(c.points) == {"a"}
    assert c.standards["CCSS.5.NF.A.1"].grade == "5"
    assert [b.name for b in c.bands] == ["Secure", "Developing", "Not yet"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_loader.py -v`
Expected: FAIL — `ImportError: cannot import name 'load_catalog'`.

- [ ] **Step 3: Update `engine/loader.py`** — change the import line, add helpers and the three new functions, and refactor `load_curriculum` to use the helpers. Replace the import:

```python
from engine.models import Band, Curriculum, Item, KnowledgePoint
```

with:

```python
from engine.models import Band, CourseMeta, Curriculum, Item, KnowledgePoint, Standard
```

Then add these helpers (place after `validate`):

```python
def _build_points(km: dict) -> dict[str, KnowledgePoint]:
    return {
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


def _build_items(ib: dict) -> dict[str, Item]:
    return {
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


def _build_bands(bd: dict) -> tuple[Band, ...]:
    return tuple(
        sorted(
            (Band(b["name"], float(b["min_score"])) for b in bd["bands"]),
            key=lambda b: b.min_score,
            reverse=True,
        )
    )


def load_catalog(path: str | Path, schema_path: str | Path) -> dict[str, Standard]:
    data = load_yaml(path)
    validate(data, schema_path)
    return {
        code: Standard(
            framework=str(s["framework"]),
            grade=str(s["grade"]),
            domain=s["domain"],
            description=s["description"],
        )
        for code, s in data["standards"].items()
    }


def load_bands(default_path: str | Path, override_path: str | Path | None,
               schema_path: str | Path) -> tuple[Band, ...]:
    path = Path(override_path) if override_path and Path(override_path).exists() else Path(default_path)
    bd = load_yaml(path)
    validate(bd, schema_path)
    return _build_bands(bd)


def load_course(course_dir: str | Path, schemas_dir: str | Path,
                methodology_dir: str | Path, standards_dir: str | Path) -> Curriculum:
    cdir, sdir = Path(course_dir), Path(schemas_dir)
    mdir, stdir = Path(methodology_dir), Path(standards_dir)

    cm = load_yaml(cdir / "course.yaml")
    validate(cm, sdir / "course.schema.json")
    meta = CourseMeta(id=cm["id"], name=cm["name"], framework=cm["framework"], grade=str(cm["grade"]))

    km = load_yaml(cdir / "knowledge_map.yaml")
    validate(km, sdir / "knowledge_map.schema.json")
    ib = load_yaml(cdir / "item_bank.yaml")
    validate(ib, sdir / "item_bank.schema.json")

    bands = load_bands(mdir / "bands.yaml", cdir / "bands.yaml", sdir / "bands.schema.json")
    catalog_file = stdir / (meta.framework.lower().replace("-", "_") + ".yaml")
    standards = load_catalog(catalog_file, sdir / "standards_catalog.schema.json")

    return Curriculum(points=_build_points(km), items=_build_items(ib),
                      bands=bands, standards=standards, meta=meta)
```

Then refactor the existing `load_curriculum` body to use the helpers (replace its `points = {...}`, `items = {...}`, `bands = tuple(...)` blocks and the final return):

```python
    points = _build_points(km)
    items = _build_items(ib)
    bands = _build_bands(bd)
    return Curriculum(points=points, items=items, bands=bands, standards=sm["standards"])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_loader.py -v`
Expected: PASS (old `load_curriculum` tests + new ones).

- [ ] **Step 5: Run the full suite**

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add engine/loader.py tests/test_loader.py
git commit -m "feat: add load_catalog, load_bands, load_course to loader"
```

---

## Task 4: Coverage module

**Files:**
- Create: `engine/coverage.py`
- Test: `tests/test_coverage.py`

**Interfaces:**
- Consumes: `Curriculum`, `CoverageReport` from `engine.models`.
- Produces:
  - `compute_coverage(curriculum) -> CoverageReport`
  - `format_coverage(report) -> str`

- [ ] **Step 1: Write the failing test** — `tests/test_coverage.py`:

```python
import pytest

from engine.models import Band, CourseMeta, Curriculum, KnowledgePoint, Standard
from engine.coverage import compute_coverage, format_coverage


def _curr():
    points = {"p1": KnowledgePoint("p1", "S", "P1", "d", (), ("M.5.A", "M.4.Z"))}
    standards = {
        "M.5.A": Standard("F", "5", "D", "da"),
        "M.5.B": Standard("F", "5", "D", "db"),
        "M.4.Z": Standard("F", "4", "D", "dz"),
    }
    meta = CourseMeta("c", "C", "F", "5")
    return Curriculum(points=points, items={}, bands=(Band("Secure", 0.8),),
                      standards=standards, meta=meta)


def test_coverage_counts_in_scope_only():
    r = compute_coverage(_curr())
    assert r.total == 2
    assert r.covered == ["M.5.A"]
    assert r.missing == ["M.5.B"]
    assert r.out_of_scope == ["M.4.Z"]
    assert r.percentage == 0.5


def test_coverage_empty_scope_is_zero_percent():
    points = {"p1": KnowledgePoint("p1", "S", "P1", "d", (), ())}
    meta = CourseMeta("c", "C", "F", "9")
    c = Curriculum(points=points, items={}, bands=(Band("Secure", 0.8),),
                   standards={"M.5.A": Standard("F", "5", "D", "d")}, meta=meta)
    r = compute_coverage(c)
    assert r.total == 0 and r.percentage == 0.0


def test_format_coverage_is_deterministic_text():
    out = format_coverage(compute_coverage(_curr()))
    assert "F grade 5" in out
    assert "1 / 2 standards covered (50.0%)" in out
    assert "M.4.Z" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_coverage.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.coverage'`.

- [ ] **Step 3: Write `engine/coverage.py`**:

```python
from __future__ import annotations

from engine.models import CoverageReport, Curriculum


def compute_coverage(curriculum: Curriculum) -> CoverageReport:
    meta = curriculum.meta
    scope = {
        code
        for code, std in curriculum.standards.items()
        if std.framework == meta.framework and std.grade == meta.grade
    }
    referenced = {ref for p in curriculum.points.values() for ref in p.standard_refs}
    covered = sorted(scope & referenced)
    missing = sorted(scope - referenced)
    out_of_scope = sorted(referenced - scope)
    percentage = len(covered) / len(scope) if scope else 0.0
    return CoverageReport(
        framework=meta.framework,
        grade=meta.grade,
        total=len(scope),
        covered=covered,
        missing=missing,
        out_of_scope=out_of_scope,
        percentage=percentage,
    )


def format_coverage(report: CoverageReport) -> str:
    lines = [
        f"Coverage: {report.framework} grade {report.grade}",
        f"  {len(report.covered)} / {report.total} standards covered "
        f"({report.percentage * 100:.1f}%)",
        f"  Covered: {', '.join(report.covered) if report.covered else '(none)'}",
        f"  Missing ({len(report.missing)}): "
        f"{', '.join(report.missing) if report.missing else '(none)'}",
    ]
    if report.out_of_scope:
        lines.append(
            "  Out of scope (referenced, other grade/framework): "
            + ", ".join(report.out_of_scope)
        )
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_coverage.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add engine/coverage.py tests/test_coverage.py
git commit -m "feat: add standards-coverage computation and formatting"
```

---

## Task 5: Author shared content (catalog, methodology bands, course manifest)

**Files:**
- Create: `standards/ccss_math.yaml`
- Create: `methodology/bands.yaml`
- Create: `curriculum/grade5_math/course.yaml`
- Test: `tests/test_standards_catalog.py`
- Test: `tests/test_coverage.py` (append a real-content test)

**Interfaces:**
- Consumes: `load_catalog`, `load_course` (Task 3), `compute_coverage` (Task 4), the catalog schema (Task 2).
- Produces: the real shared content. Nothing is deleted yet; the old course `bands.yaml`/`standard_mapping.yaml` remain until Task 6. (`load_bands` uses the course `bands.yaml` as an override while it still exists — same content, same result.)

- [ ] **Step 1: Create `methodology/bands.yaml`** (same content as the course copy):

```yaml
bands:
  - name: Secure
    min_score: 0.8
  - name: Developing
    min_score: 0.5
  - name: "Not yet"
    min_score: 0.0
```

- [ ] **Step 2: Create `curriculum/grade5_math/course.yaml`**:

```yaml
id: grade5_math
name: Grade 5 Mathematics
framework: CCSS-Math
grade: 5
```

- [ ] **Step 3: Create `standards/ccss_math.yaml`** — the full CCSS Grade-5 Math catalog (26 standards) plus the grade-4 prerequisite in use. Codes sourced from the Common Core State Standards (corestandards.org):

```yaml
standards:
  # --- Grade 4 prerequisite referenced by Grade 5 ---
  CCSS.4.NF.A.1:
    framework: CCSS-Math
    grade: 4
    domain: Number & Operations—Fractions
    description: "Explain why a/b equals (n*a)/(n*b); recognize and generate equivalent fractions."
  # --- 5.OA Operations & Algebraic Thinking ---
  CCSS.5.OA.A.1:
    framework: CCSS-Math
    grade: 5
    domain: Operations & Algebraic Thinking
    description: "Use parentheses, brackets, or braces in numerical expressions and evaluate them."
  CCSS.5.OA.A.2:
    framework: CCSS-Math
    grade: 5
    domain: Operations & Algebraic Thinking
    description: "Write and interpret simple numerical expressions without evaluating them."
  CCSS.5.OA.B.3:
    framework: CCSS-Math
    grade: 5
    domain: Operations & Algebraic Thinking
    description: "Generate two numerical patterns from two rules and graph the ordered pairs."
  # --- 5.NBT Number & Operations in Base Ten ---
  CCSS.5.NBT.A.1:
    framework: CCSS-Math
    grade: 5
    domain: Number & Operations in Base Ten
    description: "A digit represents 10x the place to its right and 1/10 the place to its left."
  CCSS.5.NBT.A.2:
    framework: CCSS-Math
    grade: 5
    domain: Number & Operations in Base Ten
    description: "Explain patterns when multiplying/dividing by powers of 10; use exponents for 10."
  CCSS.5.NBT.A.3:
    framework: CCSS-Math
    grade: 5
    domain: Number & Operations in Base Ten
    description: "Read, write, and compare decimals to thousandths."
  CCSS.5.NBT.A.4:
    framework: CCSS-Math
    grade: 5
    domain: Number & Operations in Base Ten
    description: "Use place value understanding to round decimals to any place."
  CCSS.5.NBT.B.5:
    framework: CCSS-Math
    grade: 5
    domain: Number & Operations in Base Ten
    description: "Fluently multiply multi-digit whole numbers using the standard algorithm."
  CCSS.5.NBT.B.6:
    framework: CCSS-Math
    grade: 5
    domain: Number & Operations in Base Ten
    description: "Find whole-number quotients with up to four-digit dividends and two-digit divisors."
  CCSS.5.NBT.B.7:
    framework: CCSS-Math
    grade: 5
    domain: Number & Operations in Base Ten
    description: "Add, subtract, multiply, and divide decimals to hundredths."
  # --- 5.NF Number & Operations—Fractions ---
  CCSS.5.NF.A.1:
    framework: CCSS-Math
    grade: 5
    domain: Number & Operations—Fractions
    description: "Add and subtract fractions with unlike denominators, including mixed numbers."
  CCSS.5.NF.A.2:
    framework: CCSS-Math
    grade: 5
    domain: Number & Operations—Fractions
    description: "Solve word problems adding and subtracting fractions referring to the same whole."
  CCSS.5.NF.B.3:
    framework: CCSS-Math
    grade: 5
    domain: Number & Operations—Fractions
    description: "Interpret a fraction as division of the numerator by the denominator (a/b = a / b)."
  CCSS.5.NF.B.4:
    framework: CCSS-Math
    grade: 5
    domain: Number & Operations—Fractions
    description: "Multiply a fraction or whole number by a fraction."
  CCSS.5.NF.B.5:
    framework: CCSS-Math
    grade: 5
    domain: Number & Operations—Fractions
    description: "Interpret multiplication as scaling (resizing)."
  CCSS.5.NF.B.6:
    framework: CCSS-Math
    grade: 5
    domain: Number & Operations—Fractions
    description: "Solve real-world problems involving multiplication of fractions and mixed numbers."
  CCSS.5.NF.B.7:
    framework: CCSS-Math
    grade: 5
    domain: Number & Operations—Fractions
    description: "Divide unit fractions by whole numbers and whole numbers by unit fractions."
  # --- 5.MD Measurement & Data ---
  CCSS.5.MD.A.1:
    framework: CCSS-Math
    grade: 5
    domain: Measurement & Data
    description: "Convert among different-sized standard measurement units within a system."
  CCSS.5.MD.B.2:
    framework: CCSS-Math
    grade: 5
    domain: Measurement & Data
    description: "Make a line plot to display a data set of measurements in fractions of a unit."
  CCSS.5.MD.C.3:
    framework: CCSS-Math
    grade: 5
    domain: Measurement & Data
    description: "Recognize volume as an attribute of solid figures and understand volume measurement."
  CCSS.5.MD.C.4:
    framework: CCSS-Math
    grade: 5
    domain: Measurement & Data
    description: "Measure volumes by counting unit cubes."
  CCSS.5.MD.C.5:
    framework: CCSS-Math
    grade: 5
    domain: Measurement & Data
    description: "Relate volume to multiplication and addition; solve real-world volume problems."
  # --- 5.G Geometry ---
  CCSS.5.G.A.1:
    framework: CCSS-Math
    grade: 5
    domain: Geometry
    description: "Understand a coordinate system; interpret coordinate values of points."
  CCSS.5.G.A.2:
    framework: CCSS-Math
    grade: 5
    domain: Geometry
    description: "Represent real-world problems by graphing points in the first quadrant."
  CCSS.5.G.B.3:
    framework: CCSS-Math
    grade: 5
    domain: Geometry
    description: "Attributes of a category of two-dimensional figures belong to all subcategories."
  CCSS.5.G.B.4:
    framework: CCSS-Math
    grade: 5
    domain: Geometry
    description: "Classify two-dimensional figures in a hierarchy based on properties."
```

- [ ] **Step 4: Write `tests/test_standards_catalog.py`**:

```python
from engine.loader import load_catalog

CATALOG = "standards/ccss_math.yaml"
SCHEMA = "schemas/standards_catalog.schema.json"


def test_catalog_validates_and_has_required_fields():
    cat = load_catalog(CATALOG, SCHEMA)
    assert "CCSS.5.NF.A.1" in cat
    for code, std in cat.items():
        assert std.framework and std.grade and std.domain and std.description, code


def test_catalog_contains_all_26_grade5_standards():
    cat = load_catalog(CATALOG, SCHEMA)
    grade5 = [c for c, s in cat.items() if s.grade == "5"]
    assert len(grade5) == 26, f"expected 26 grade-5 standards, found {len(grade5)}"
```

- [ ] **Step 5: Append the real-content coverage test** to `tests/test_coverage.py`:

```python
def test_grade5_math_real_coverage():
    from engine.loader import load_course
    c = load_course("curriculum/grade5_math", "schemas", "methodology", "standards")
    r = compute_coverage(c)
    assert r.total == 26
    assert "CCSS.5.NF.A.1" in r.covered
    assert "CCSS.5.G.A.1" in r.missing
    assert "CCSS.4.NF.A.1" in r.out_of_scope
    assert "CCSS.4.NF.A.1" not in r.missing
    assert len(r.covered) == 6
    assert r.percentage == pytest.approx(6 / 26)
```

- [ ] **Step 6: Run the new tests**

Run: `python -m pytest tests/test_standards_catalog.py tests/test_coverage.py -v`
Expected: PASS. If `test_catalog_contains_all_26_grade5_standards` fails, the catalog YAML is miscounted — fix the YAML, not the test.

- [ ] **Step 7: Run the full suite**

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add standards/ccss_math.yaml methodology/bands.yaml curriculum/grade5_math/course.yaml \
        tests/test_standards_catalog.py tests/test_coverage.py
git commit -m "feat: author shared CCSS-Math catalog, methodology bands, course manifest"
```

---

## Task 6: Cutover — switch to load_course, add --coverage, remove old path

**Files:**
- Modify: `engine/cli.py`
- Modify: `engine/loader.py` (remove `load_curriculum`)
- Modify: `tests/test_content_integrity.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_loader.py` (remove `load_curriculum` tests)
- Modify: `tests/test_schemas.py` (remove obsolete standard_mapping test)
- Delete: `curriculum/grade5_math/bands.yaml`, `curriculum/grade5_math/standard_mapping.yaml`, `schemas/standard_mapping.schema.json`

**Interfaces:**
- Consumes: `load_course`, `load_yaml` (Task 3); `compute_coverage`, `format_coverage` (Task 4).
- Produces: a CLI driven by `load_course` with `--coverage` and shared-dir flags; `load_curriculum` no longer exists.

- [ ] **Step 1: Write the failing test** — replace the contents of `tests/test_cli.py` with:

```python
from engine.cli import main

BASE = [
    "--curriculum", "curriculum/grade5_math",
    "--responses", "curriculum/grade5_math/sample_responses.yaml",
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


def test_cli_coverage_report(capsys):
    code = main(["--curriculum", "curriculum/grade5_math", "--coverage"])
    out = capsys.readouterr().out
    assert code == 0
    assert "CCSS-Math grade 5" in out
    assert "6 / 26" in out
    assert "CCSS.5.NF.A.1" in out


def test_cli_requires_responses_without_coverage():
    import pytest
    with pytest.raises(SystemExit):
        main(["--curriculum", "curriculum/grade5_math"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL — the coverage flag / new defaults don't exist yet.

- [ ] **Step 3: Rewrite `engine/cli.py`**:

```python
from __future__ import annotations

import argparse

from engine.coverage import compute_coverage, format_coverage
from engine.loader import load_course, load_yaml
from engine.path import build_path
from engine.report import render_parent, render_student
from engine.score import evaluate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a student's diagnostic responses.")
    parser.add_argument("--curriculum", required=True)
    parser.add_argument("--schemas", default="schemas")
    parser.add_argument("--methodology", default="methodology")
    parser.add_argument("--standards", default="standards")
    parser.add_argument("--templates", default="templates")
    parser.add_argument("--responses")
    parser.add_argument("--name", default="Student")
    parser.add_argument("--audience", choices=["parent", "student"], default="parent")
    parser.add_argument("--coverage", action="store_true",
                        help="Print the standards-coverage report and exit.")
    args = parser.parse_args(argv)

    curriculum = load_course(args.curriculum, args.schemas, args.methodology, args.standards)

    if args.coverage:
        print(format_coverage(compute_coverage(curriculum)))
        return 0

    if not args.responses:
        parser.error("--responses is required unless --coverage is given")
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

- [ ] **Step 4: Switch `tests/test_content_integrity.py` to `load_course`** — replace the top of the file (imports + fixture) with:

```python
import pytest

from engine.loader import load_course

CURRICULUM_DIR = "curriculum/grade5_math"
SCHEMAS_DIR = "schemas"
METHODOLOGY_DIR = "methodology"
STANDARDS_DIR = "standards"


@pytest.fixture(scope="module")
def curriculum():
    return load_course(CURRICULUM_DIR, SCHEMAS_DIR, METHODOLOGY_DIR, STANDARDS_DIR)
```

Leave every test function below unchanged (`curriculum.standards` is now a `dict[str, Standard]`, but `test_every_standard_ref_exists_in_mapping` only checks key membership via `set(curriculum.standards)`, which still works).

- [ ] **Step 5: Remove `load_curriculum`** from `engine/loader.py` — delete the entire `def load_curriculum(...)` function (the helpers `_build_points`/`_build_items`/`_build_bands` and the new loaders remain).

- [ ] **Step 6: Remove obsolete tests** — in `tests/test_loader.py`, delete `_write_mini`, `test_load_curriculum_builds_models`, and `test_load_curriculum_sorts_bands_descending` (the `load_course`/`load_catalog`/`load_bands` tests and `test_validate_raises_on_bad_content` stay; update the import line to drop `load_curriculum`):

```python
from engine.loader import load_catalog, load_bands, load_course, validate, load_yaml
```

In `tests/test_schemas.py`, delete `test_standard_mapping_schema_requires_framework_and_description` (the standards-catalog and course schema tests from Task 2 cover the replacement).

- [ ] **Step 7: Delete the old files**

```bash
git rm curriculum/grade5_math/bands.yaml curriculum/grade5_math/standard_mapping.yaml schemas/standard_mapping.schema.json
```

- [ ] **Step 8: Run the full suite**

Run: `python -m pytest -q`
Expected: all pass. Then a manual smoke run of the new coverage command:

Run: `python -m engine.cli --curriculum curriculum/grade5_math --coverage`
Expected: prints `Coverage: CCSS-Math grade 5` and `6 / 26 standards covered (23.1%)` with the covered/missing/out-of-scope lists.

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "refactor: cut over to load_course + shared catalog/bands, add --coverage"
```

---

## Task 7: Docs & course skeleton

**Files:**
- Create: `methodology/METHODOLOGY.md`
- Create: `curriculum/_template/course.yaml`
- Create: `curriculum/_template/knowledge_map.yaml`
- Create: `curriculum/_template/item_bank.yaml`
- Create: `curriculum/_template/sample_responses.yaml`
- Create: `curriculum/_template/AUTHORING.md`
- Modify: `README.md`
- Test: `tests/test_template.py`

**Interfaces:**
- Consumes: the `course.schema.json` (Task 2) for validating the template manifest.
- Produces: documentation and a copy-and-fill skeleton. The template is a skeleton, not a loadable course, and is excluded from real-content checks (no test calls `load_course` on it).

- [ ] **Step 1: Write the failing test** — `tests/test_template.py`:

```python
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from engine.loader import load_yaml

TEMPLATE = Path("curriculum/_template")


def test_template_has_all_skeleton_files():
    for name in ("course.yaml", "knowledge_map.yaml", "item_bank.yaml",
                 "sample_responses.yaml", "AUTHORING.md"):
        assert (TEMPLATE / name).exists(), f"missing template file {name}"


def test_template_manifest_validates_against_course_schema():
    schema = json.loads(Path("schemas/course.schema.json").read_text())
    Draft202012Validator(schema).validate(load_yaml(TEMPLATE / "course.yaml"))


def test_methodology_doc_exists():
    assert Path("methodology/METHODOLOGY.md").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_template.py -v`
Expected: FAIL — template files / methodology doc missing.

- [ ] **Step 3: Create `curriculum/_template/course.yaml`**:

```yaml
id: REPLACE_ME_course_id
name: REPLACE ME Course Name
framework: CCSS-Math
grade: 5
```

- [ ] **Step 4: Create the template stub content files**

`curriculum/_template/knowledge_map.yaml`:
```yaml
points: []
```

`curriculum/_template/item_bank.yaml`:
```yaml
items: []
```

`curriculum/_template/sample_responses.yaml`:
```yaml
responses: {}
```

- [ ] **Step 5: Create `curriculum/_template/AUTHORING.md`**:

```markdown
# Authoring a New Course

Copy this `_template/` directory to `curriculum/<your_course_id>/` and fill it in.

## Checklist

1. **course.yaml** — set `id` (must match the folder name), `name`, `framework`
   (e.g. `CCSS-Math`), and `grade`. The `(framework, grade)` pair defines which
   standards count toward this course's coverage.
2. **Standards catalog** — make sure every standard you will reference exists in
   `standards/<framework>.yaml` (filename = framework lowercased with `-` → `_`,
   e.g. `CCSS-Math` → `ccss_math.yaml`). Add missing standards there, not here.
3. **knowledge_map.yaml** — author strands and knowledge points. Each point needs
   `id`, `strand`, `title`, `description`, optional `prerequisites` (ids of other
   points), and `standard_refs` (catalog codes). Keep prerequisites acyclic.
4. **item_bank.yaml** — author at least 2 items per knowledge point. Each item needs
   `id`, `points`, `difficulty` (1–3), `type` (`mcq`|`numeric`), `prompt`, `answer`,
   and (for mcq) `options`. No distractor may equal the keyed answer.
5. **bands.yaml** (optional) — only add one here if this course needs thresholds
   different from `methodology/bands.yaml`; otherwise the shared default is used.
6. **Verify** — run `python -m pytest` (the content-integrity tests validate
   structure) and `python -m engine.cli --curriculum curriculum/<your_course_id>
   --coverage` to see standards coverage.
```

- [ ] **Step 6: Create `methodology/METHODOLOGY.md`**:

```markdown
# Course Evaluator — Methodology

Shared principles that apply to every course. Course-specific material lives under
`curriculum/<course>/`; the principles here are global.

## Two-layer status model

A student's status is reported at two layers:

- **Strands** — the parent/student headline (e.g. "Number & Operations").
- **Knowledge points** — the actionable detail under each strand, and the unit the
  "where to improve" guidance operates on.

## Scoring — transparent difficulty-weighted thresholds

For each knowledge point, mastery is the difficulty-weighted fraction of answered
items the student got right: `sum(difficulty * correct) / sum(difficulty)`. A point
with fewer than two answered items is reported as *insufficient evidence* rather than
given a false score. Mastery maps to a band:

- **Secure** ≥ 0.8
- **Developing** ≥ 0.5
- **Not yet** ≥ 0.0

Bands live in `methodology/bands.yaml` and may be overridden per course.

## Learning path

The "where to improve" output lists the student's non-Secure points, ordered so that
prerequisite gaps come first (topological order), ties broken by how many later points
depend on each. Each step links practice items for that point, excluding items already
used in the diagnostic.

## Standards & coverage

Each course declares a `framework` and `grade` in its `course.yaml`. Knowledge points
reference standard codes from the shared catalog in `standards/<framework>.yaml`. The
coverage report (`--coverage`) shows how many of that grade's standards the course
covers — an informational measure of project goal #2, never an enforced gate.

## Adding a course

See `curriculum/_template/AUTHORING.md`.
```

- [ ] **Step 7: Replace `README.md`**:

```markdown
# course_evaluator

An evaluation system for K-12 courses. It turns a tagged diagnostic into a status
report (strands → knowledge points) and a prioritized, practice-linked learning path
for students and parents, and reports how much of a curriculum's standards a course
covers.

## Layout

- `methodology/` — shared principles (`METHODOLOGY.md`) and default mastery `bands.yaml`.
- `standards/` — shared standards catalogs per framework (e.g. `ccss_math.yaml`).
- `curriculum/<course>/` — per-course material: `course.yaml`, `knowledge_map.yaml`,
  `item_bank.yaml`, `sample_responses.yaml`. `_template/` is the skeleton for new courses.
- `engine/` — the evaluation engine (loader, scoring, learning path, reports, coverage, CLI).
- `schemas/` — JSON Schemas validating all content.
- `templates/` — Jinja2 report templates.

## Usage

Run from the repo root.

Evaluate a student (parent or student report):
```
python -m engine.cli --curriculum curriculum/grade5_math \
  --responses curriculum/grade5_math/sample_responses.yaml \
  --name Sam --audience student
```

Standards coverage for a course:
```
python -m engine.cli --curriculum curriculum/grade5_math --coverage
```

Run the tests:
```
python -m pytest
```

## Adding a course

Copy `curriculum/_template/` and follow `curriculum/_template/AUTHORING.md`.
```

- [ ] **Step 8: Run the tests**

Run: `python -m pytest tests/test_template.py -v`
Expected: PASS (3 tests).

- [ ] **Step 9: Run the full suite**

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 10: Commit**

```bash
git add methodology/METHODOLOGY.md curriculum/_template README.md tests/test_template.py
git commit -m "docs: add methodology doc, course template, and README"
```

---

## Notes for the implementer

- Run `python -m pytest` from the repo root (the `pyproject.toml` `pythonpath`/`testpaths` make `engine` importable).
- Content tasks: if an integrity or catalog test fails, the bug is in the YAML content, not the test — fix the content.
- The cutover (Task 6) is the only task that deletes files; ensure the full suite is green before committing it.
- Determinism: every coverage list is `sorted()`. Do not introduce set-ordering into any printed output.
