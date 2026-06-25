from engine.models import (
    KnowledgePoint, Item, Band, Curriculum,
    PointResult, StrandResult, EvaluationResult, PathStep,
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
