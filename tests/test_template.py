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
