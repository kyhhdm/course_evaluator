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
