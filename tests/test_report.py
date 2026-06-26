from engine.models import (
    Band, Curriculum, EvaluationResult, Item, KnowledgePoint, PathStep,
    PointResult, StrandResult,
)
from engine.report import render_parent, render_student

TEMPLATES = "templates"


def _setup():
    points = {
        "a": KnowledgePoint("a", "Number", "Equivalent fractions", "d", (), ("X",)),
        "b": KnowledgePoint("b", "Number", "Add fractions", "d", ("a",), ("X",)),
    }
    items = {"b2": Item("b2", ("b",), 1, "mcq", "Add 1/2 + 1/4?", "B", {}, {})}
    bands = (Band("Secure", 0.8), Band("Developing", 0.5), Band("Not yet", 0.0))
    curriculum = Curriculum(points=points, items=items, bands=bands, standards={"X": {}})
    pa = PointResult("a", 0.9, "Secure", "scored", 2)
    pb = PointResult("b", 0.4, "Not yet", "scored", 2)
    strand = StrandResult("Number", "Developing", 0.65, "b", [pa, pb])
    result = EvaluationResult([strand], {"a": pa, "b": pb}, {"b1"})
    path = [PathStep("b", "Add fractions", ["b2"])]
    return curriculum, result, path


def test_parent_report_shows_strand_band_and_focus():
    curriculum, result, path = _setup()
    out = render_parent(curriculum, result, path, TEMPLATES, "Sam")
    assert "Sam" in out
    assert "Number" in out
    assert "Developing" in out
    assert "Add fractions" in out


def test_student_report_lists_steps_and_practice_prompt():
    curriculum, result, path = _setup()
    out = render_student(curriculum, result, path, TEMPLATES, "Sam")
    assert "Step 1" in out
    assert "Add fractions" in out
    assert "Add 1/2 + 1/4?" in out


def test_reports_handle_empty_path():
    curriculum, result, _ = _setup()
    out = render_student(curriculum, result, [], TEMPLATES, "Sam")
    assert "no gaps" in out.lower()


def test_parent_report_shows_per_point_groups_and_strengths():
    curriculum, result, path = _setup()
    out = render_parent(curriculum, result, path, TEMPLATES, "Sam")
    assert "Secure:" in out and "Equivalent fractions" in out   # per-point group
    assert "Not yet:" in out and "Add fractions" in out
    assert "Strengths" in out
    assert "assessed skills are secure" in out                  # strengths sentence
