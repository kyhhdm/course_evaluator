from engine.models import (
    KnowledgePoint, Item, Band, Curriculum,
    PointResult, StrandResult, EvaluationResult, PathStep,
    Standard, CourseMeta, CoverageReport,
)


def _curriculum():
    points = {
        "a": KnowledgePoint("a", "Number", "A", "desc", (), ("X",)),
        "b": KnowledgePoint("b", "Number", "B", "desc", ("a",), ("Y",)),
    }
    items = {
        "i1": Item("i1", ("a",), 1, "mcq", "?", "A", {"A": "x"}, {}),
        "i2": Item("i2", ("a", "b"), 3, "numeric", "?", "5", {}, {}),
    }
    bands = (Band("Secure", 0.8), Band("Developing", 0.5), Band("Not yet", 0.0))
    return Curriculum(points=points, items=items, bands=bands, standards={})


def test_items_for_point_matches_tagged_items():
    c = _curriculum()
    assert [it.id for it in c.items_for_point("a")] == ["i1", "i2"]
    assert [it.id for it in c.items_for_point("b")] == ["i2"]


def test_points_in_strand_returns_all_points():
    c = _curriculum()
    assert {p.id for p in c.points_in_strand("Number")} == {"a", "b"}


def test_band_for_picks_highest_band_at_or_below_score():
    c = _curriculum()
    assert c.band_for(0.95).name == "Secure"
    assert c.band_for(0.80).name == "Secure"
    assert c.band_for(0.79).name == "Developing"
    assert c.band_for(0.50).name == "Developing"
    assert c.band_for(0.10).name == "Not yet"


def test_result_dataclasses_construct():
    pr = PointResult("a", 0.9, "Secure", "scored", 3)
    sr = StrandResult("Number", "Secure", 0.9, "a", [pr])
    er = EvaluationResult([sr], {"a": pr}, {"i1"})
    ps = PathStep("a", "A", ["i2"])
    assert er.strands[0].weakest_point_id == "a"
    assert ps.practice_item_ids == ["i2"]


def test_new_dataclasses_construct():
    std = Standard("CCSS-Math", "5", "Number & Operations—Fractions", "Add unlike fractions")
    meta = CourseMeta("grade5_math", "Grade 5 Mathematics", "CCSS-Math", "5")
    rep = CoverageReport("CCSS-Math", "5", 26, ["a"], ["b"], ["c"], 0.5)
    assert std.grade == "5"
    assert meta.framework == "CCSS-Math"
    assert rep.total == 26 and rep.percentage == 0.5


def test_curriculum_accepts_meta_and_defaults_none():
    c = Curriculum(points={}, items={}, bands=(Band("Secure", 0.8),), standards={})
    assert c.meta is None
    c2 = Curriculum(points={}, items={}, bands=(Band("Secure", 0.8),), standards={},
                    meta=CourseMeta("i", "n", "CCSS-Math", "5"))
    assert c2.meta.grade == "5"


def test_item_lesson_refs_field():
    """Item accepts lesson_refs; defaults to empty list."""
    from engine.models import Item
    base = dict(id="X", points=("p",), difficulty=1, type="numeric", prompt="q", answer="1")
    assert Item(**base).lesson_refs == []
    assert Item(**base, lesson_refs=[43, 80]).lesson_refs == [43, 80]


def test_items_for_point_filters_by_role():
    points = {"a": KnowledgePoint("a", "Number", "A", "d", (), ("X",))}
    items = {
        "d1": Item("d1", ("a",), 1, "mcq", "?", "A", {}, {}),                    # default diagnostic
        "d2": Item("d2", ("a",), 2, "mcq", "?", "A", {}, {}, role="diagnostic"),
        "p1": Item("p1", ("a",), 1, "mcq", "?", "A", {}, {}, role="practice"),
    }
    c = Curriculum(points=points, items=items, bands=(Band("Secure", 0.8),), standards={})
    assert [it.id for it in c.items_for_point("a")] == ["d1", "d2", "p1"]
    assert [it.id for it in c.diagnostic_items_for_point("a")] == ["d1", "d2"]
    assert [it.id for it in c.practice_items_for_point("a")] == ["p1"]
