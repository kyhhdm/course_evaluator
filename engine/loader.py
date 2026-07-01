from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from engine.models import Band, CourseMeta, Curriculum, Item, KnowledgePoint, Standard


def load_yaml(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate(data: dict, schema_path: str | Path) -> None:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(data)


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
            role=it.get("role", "diagnostic"),
            lesson_refs=it.get("lesson_refs", []),
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
