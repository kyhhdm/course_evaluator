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
