from pathlib import Path

import pytest

from engine.loader import load_catalog, load_bands, load_course, validate, load_yaml



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


def test_existing_items_default_empty_lesson_refs():
    """Courses without lesson_refs load with an empty list (no breakage)."""
    from engine.loader import load_course
    c = load_course("curriculum/grade5_math", "schemas", "methodology", "standards")
    assert all(it.lesson_refs == [] for it in c.items.values())


def test_items_get_role_with_default_diagnostic():
    from engine.loader import load_course
    c = load_course("curriculum/grade5_math", "schemas", "methodology", "standards")
    # every loaded item exposes a role; current content has none yet -> default
    assert all(it.role in ("diagnostic", "practice") for it in c.items.values())
    assert any(it.role == "diagnostic" for it in c.items.values())
