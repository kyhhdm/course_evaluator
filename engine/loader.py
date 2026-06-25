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
