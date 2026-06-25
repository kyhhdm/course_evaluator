from pathlib import Path

import pytest

from engine.loader import load_curriculum, validate, load_yaml, load_catalog, load_bands, load_course


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
