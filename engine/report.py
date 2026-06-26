from __future__ import annotations

from jinja2 import Environment, FileSystemLoader

from engine.models import Curriculum, EvaluationResult, PathStep


def _env(templates_dir: str) -> Environment:
    return Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_parent(
    curriculum: Curriculum,
    result: EvaluationResult,
    path: list[PathStep],
    templates_dir: str,
    student_name: str = "Student",
) -> str:
    from engine.report_view import build_parent_view

    view = build_parent_view(curriculum, result, path, student_name)
    tmpl = _env(templates_dir).get_template("report_parent.md.j2")
    return tmpl.render(view=view)


def render_student(
    curriculum: Curriculum,
    result: EvaluationResult,
    path: list[PathStep],
    templates_dir: str,
    student_name: str = "Student",
) -> str:
    tmpl = _env(templates_dir).get_template("report_student.md.j2")
    return tmpl.render(
        name=student_name,
        strands=result.strands,
        path=path,
        items=curriculum.items,
    )
