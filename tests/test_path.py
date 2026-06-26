from engine.models import (
    Band, Curriculum, EvaluationResult, Item, KnowledgePoint, PointResult,
)
from engine.path import build_path, impact


def _curriculum():
    points = {
        "a": KnowledgePoint("a", "Number", "A", "d", (), ("X",)),
        "b": KnowledgePoint("b", "Number", "B", "d", ("a",), ("X",)),
        "c": KnowledgePoint("c", "Number", "C", "d", ("b",), ("X",)),
        "d": KnowledgePoint("d", "Number", "D", "d", (), ("X",)),
    }
    items = {
        "a1": Item("a1", ("a",), 1, "mcq", "?", "A", {}, {}),
        "a2": Item("a2", ("a",), 3, "mcq", "?", "A", {}, {}),
        "b1": Item("b1", ("b",), 2, "mcq", "?", "A", {}, {}),
        "d1": Item("d1", ("d",), 1, "mcq", "?", "A", {}, {}),
        "ap1": Item("ap1", ("a",), 2, "mcq", "?", "A", {}, {}, role="practice"),
        "ap2": Item("ap2", ("a",), 1, "mcq", "?", "A", {}, {}, role="practice"),
    }
    bands = (Band("Secure", 0.8), Band("Developing", 0.5), Band("Not yet", 0.0))
    return Curriculum(points=points, items=items, bands=bands, standards={"X": {}})


def _weak_result(weak_points):
    prs = {}
    for pid in ["a", "b", "c", "d"]:
        if pid in weak_points:
            prs[pid] = PointResult(pid, 0.4, "Not yet", "scored", 2)
        else:
            prs[pid] = PointResult(pid, 0.9, "Secure", "scored", 2)
    return EvaluationResult([], prs, answered_item_ids=set())


def test_impact_counts_direct_dependents():
    c = _curriculum()
    assert impact(c, "a") == 1  # b depends on a
    assert impact(c, "b") == 1  # c depends on b
    assert impact(c, "d") == 0


def test_path_orders_prerequisites_before_dependents():
    c = _curriculum()
    result = _weak_result({"a", "b", "c"})
    order = [step.point_id for step in build_path(c, result)]
    assert order.index("a") < order.index("b") < order.index("c")


def test_path_excludes_secure_points():
    c = _curriculum()
    result = _weak_result({"a"})
    order = [step.point_id for step in build_path(c, result)]
    assert order == ["a"]


def test_path_tie_break_by_impact_then_id():
    c = _curriculum()
    # a (impact 1, has dependent b which is Secure here) vs d (impact 0): a first
    result = _weak_result({"a", "d"})
    order = [step.point_id for step in build_path(c, result)]
    assert order == ["a", "d"]


def test_practice_items_come_from_practice_pool_sorted_by_difficulty():
    c = _curriculum()
    result = _weak_result({"a"})
    result.answered_item_ids.add("a1")  # answering a diagnostic item must NOT change practice
    step = build_path(c, result)[0]
    assert step.practice_item_ids == ["ap2", "ap1"]  # difficulty 1 before 2; diagnostics excluded


def test_practice_items_empty_when_no_practice_pool():
    c = _curriculum()
    result = _weak_result({"d"})  # point d has no practice items
    step = build_path(c, result)[0]
    assert step.practice_item_ids == []
