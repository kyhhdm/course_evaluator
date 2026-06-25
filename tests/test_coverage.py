import pytest

from engine.models import Band, CourseMeta, Curriculum, KnowledgePoint, Standard
from engine.coverage import compute_coverage, format_coverage


def _curr():
    points = {"p1": KnowledgePoint("p1", "S", "P1", "d", (), ("M.5.A", "M.4.Z"))}
    standards = {
        "M.5.A": Standard("F", "5", "D", "da"),
        "M.5.B": Standard("F", "5", "D", "db"),
        "M.4.Z": Standard("F", "4", "D", "dz"),
    }
    meta = CourseMeta("c", "C", "F", "5")
    return Curriculum(points=points, items={}, bands=(Band("Secure", 0.8),),
                      standards=standards, meta=meta)


def test_coverage_counts_in_scope_only():
    r = compute_coverage(_curr())
    assert r.total == 2
    assert r.covered == ["M.5.A"]
    assert r.missing == ["M.5.B"]
    assert r.out_of_scope == ["M.4.Z"]
    assert r.percentage == 0.5


def test_coverage_empty_scope_is_zero_percent():
    points = {"p1": KnowledgePoint("p1", "S", "P1", "d", (), ())}
    meta = CourseMeta("c", "C", "F", "9")
    c = Curriculum(points=points, items={}, bands=(Band("Secure", 0.8),),
                   standards={"M.5.A": Standard("F", "5", "D", "d")}, meta=meta)
    r = compute_coverage(c)
    assert r.total == 0 and r.percentage == 0.0


def test_format_coverage_is_deterministic_text():
    out = format_coverage(compute_coverage(_curr()))
    assert "F grade 5" in out
    assert "1 / 2 standards covered (50.0%)" in out
    assert "M.4.Z" in out


def test_grade5_math_real_coverage():
    from engine.loader import load_course
    c = load_course("curriculum/grade5_math", "schemas", "methodology", "standards")
    r = compute_coverage(c)
    assert r.total == 26
    assert "CCSS.5.NF.A.1" in r.covered
    assert "CCSS.5.G.A.1" in r.covered
    assert "CCSS.4.NF.A.1" in r.out_of_scope
    assert "CCSS.4.NF.A.1" not in r.missing
    assert len(r.covered) == 13
    assert len(r.missing) == 13
    assert r.percentage == pytest.approx(13 / 26)
