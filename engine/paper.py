from __future__ import annotations

from jinja2 import Environment, FileSystemLoader

from engine.models import Curriculum, EvaluationResult, Item, PathStep


def _env(templates_dir: str) -> Environment:
    return Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def ordered_groups(curriculum: Curriculum) -> list[dict]:
    """Group each item under its first knowledge point.

    Strands in knowledge-map order, points in knowledge-map order within a
    strand, items in item-bank order within a point. Each item appears once.
    """
    buckets: dict[str, list[Item]] = {pid: [] for pid in curriculum.points}
    for item in curriculum.items.values():  # item-bank (insertion) order
        if not item.points:
            continue
        primary = item.points[0]
        if primary in buckets:
            buckets[primary].append(item)
    groups: list[dict] = []
    for strand in curriculum.strands():
        point_groups = []
        for point in curriculum.points_in_strand(strand):
            if buckets[point.id]:
                point_groups.append({"point": point, "items": buckets[point.id]})
        if point_groups:
            groups.append({"strand": strand, "points": point_groups})
    return groups


def ordered_items(curriculum: Curriculum) -> list[Item]:
    items: list[Item] = []
    for g in ordered_groups(curriculum):
        for pg in g["points"]:
            items.extend(pg["items"])
    return items


def render_paper_html(curriculum: Curriculum, templates_dir: str) -> str:
    tmpl = _env(templates_dir).get_template("test_paper.html.j2")
    return tmpl.render(groups=ordered_groups(curriculum), course=curriculum.meta)


def render_answer_key_html(curriculum: Curriculum, templates_dir: str) -> str:
    tmpl = _env(templates_dir).get_template("answer_key.html.j2")
    return tmpl.render(groups=ordered_groups(curriculum), course=curriculum.meta)


def render_answer_sheet_html(curriculum: Curriculum, templates_dir: str) -> str:
    tmpl = _env(templates_dir).get_template("answer_sheet.html.j2")
    return tmpl.render(items=ordered_items(curriculum), course=curriculum.meta)


def render_answer_sheet_template(curriculum: Curriculum) -> str:
    """Emit a YAML responses skeleton: one blank entry per item, prompt as a comment."""
    lines = ["responses:"]
    for item in ordered_items(curriculum):
        prompt = item.prompt.replace("\n", " ")
        lines.append(f"  {item.id}:   # {prompt}")
    return "\n".join(lines) + "\n"


def drop_blank_responses(raw: dict) -> dict:
    """Drop keys whose value is None or blank so unanswered items are not scored."""
    return {k: v for k, v in raw.items() if v is not None and str(v).strip() != ""}


def render_report_html(
    curriculum: Curriculum,
    result: EvaluationResult,
    path: list[PathStep],
    templates_dir: str,
    student_name: str = "Student",
) -> str:
    secure_count = sum(1 for s in result.strands if s.band == curriculum.bands[0].name)
    tmpl = _env(templates_dir).get_template("report.html.j2")
    return tmpl.render(
        name=student_name,
        strands=result.strands,
        focus=path[:3],
        secure_count=secure_count,
    )
