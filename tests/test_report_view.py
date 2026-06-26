from engine.models import (
    Band, Curriculum, EvaluationResult, KnowledgePoint, PointResult, StrandResult,
)
from engine.report_view import build_parent_view


def _curriculum():
    points = {
        "p1": KnowledgePoint("p1", "Fractions", "Equivalent fractions", "d", (), ()),
        "p2": KnowledgePoint("p2", "Fractions", "Add unlike", "d", (), ()),
        "p3": KnowledgePoint("p3", "Fractions", "Divide fractions", "d", (), ()),
        "p4": KnowledgePoint("p4", "Geometry", "Coordinate system", "d", (), ()),
        "p5": KnowledgePoint("p5", "Geometry", "Classify figures", "d", (), ()),
    }
    bands = (Band("Secure", 0.8), Band("Developing", 0.5), Band("Not yet", 0.0))
    return Curriculum(points=points, items={}, bands=bands, standards={})


def _result():
    pr1 = PointResult("p1", 0.9, "Secure", "scored", 2)
    pr2 = PointResult("p2", 0.6, "Developing", "scored", 2)
    pr3 = PointResult("p3", 0.3, "Not yet", "scored", 2)
    pr4 = PointResult("p4", 0.95, "Secure", "scored", 2)
    pr5 = PointResult("p5", None, None, "insufficient_evidence", 1)
    frac = StrandResult("Fractions", "Developing", 0.6, "p3", [pr1, pr2, pr3])
    geo = StrandResult("Geometry", "Secure", 0.95, "p4", [pr4, pr5])
    return EvaluationResult(
        [frac, geo], {"p1": pr1, "p2": pr2, "p3": pr3, "p4": pr4, "p5": pr5}, set()
    )


def test_groups_points_by_band_and_marks_unassessed():
    view = build_parent_view(_curriculum(), _result(), [], "Maya")
    frac = view.strand_groups[0]
    assert frac.strand == "Fractions"
    assert frac.secure == ["Equivalent fractions"]
    assert frac.developing == ["Add unlike"]
    assert frac.not_yet == ["Divide fractions"]
    assert frac.not_assessed == []
    geo = view.strand_groups[1]
    assert geo.secure == ["Coordinate system"]
    assert geo.not_assessed == ["Classify figures"]


def test_counts_and_strengths():
    view = build_parent_view(_curriculum(), _result(), [], "Maya")
    assert view.secure_skill_count == 2          # p1, p4
    assert view.assessed_skill_count == 4        # p1..p4
    assert view.unassessed_skill_count == 1      # p5
    assert view.secure_strand_count == 1         # Geometry (band Secure)
    assert view.total_strand_count == 2
    # strong strands are those whose band == top band name, in result order
    assert view.strengths.strong_strands == ["Geometry"]
    # highlights are up to 3 secure point titles in knowledge-map order
    assert view.strengths.highlight_points == ["Equivalent fractions", "Coordinate system"]


def test_focus_is_first_three_path_steps():
    from engine.models import PathStep
    path = [PathStep(f"x{i}", f"Step {i}", []) for i in range(5)]
    view = build_parent_view(_curriculum(), _result(), path, "Maya")
    assert [s.title for s in view.focus] == ["Step 0", "Step 1", "Step 2"]
    assert view.student_name == "Maya"
