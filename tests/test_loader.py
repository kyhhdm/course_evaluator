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
