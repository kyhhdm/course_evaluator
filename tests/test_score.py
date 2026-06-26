import pytest

from engine.models import Band, Curriculum, Item, KnowledgePoint
from engine.score import evaluate, is_correct, MIN_ITEMS


def _curriculum():
    points = {
        "a": KnowledgePoint("a", "Number", "A", "d", (), ("X",)),
        "b": KnowledgePoint("b", "Number", "B", "d", ("a",), ("X",)),
    }
    items = {
        "a1": Item("a1", ("a",), 1, "mcq", "?", "A", {"A": "x"}, {}),
        "a2": Item("a2", ("a",), 3, "numeric", "?", "10", {}, {}),
        "b1": Item("b1", ("b",), 1, "numeric", "?", "2", {}, {}),
        "b2": Item("b2", ("b",), 1, "numeric", "?", "3", {}, {}),
    }
    bands = (Band("Secure", 0.8), Band("Developing", 0.5), Band("Not yet", 0.0))
    return Curriculum(points=points, items=items, bands=bands, standards={"X": {}})


def test_is_correct_handles_mcq_case_insensitively():
    item = Item("x", ("a",), 1, "mcq", "?", "B", {"B": "y"}, {})
    assert is_correct(item, "b") is True
    assert is_correct(item, "C") is False
    assert is_correct(item, None) is False


def test_is_correct_handles_numeric_equivalence():
    item = Item("x", ("a",), 1, "numeric", "?", "0.7", {}, {})
    assert is_correct(item, "0.70") is True
    assert is_correct(item, "0.7") is True
    assert is_correct(item, "0.8") is False


def test_difficulty_weighted_mastery():
    c = _curriculum()
    # a1 (diff1) wrong, a2 (diff3) right -> 3/4 = 0.75 -> Developing
    result = evaluate(c, {"a1": "Z", "a2": "10", "b1": "2", "b2": "3"})
    pa = result.point_results["a"]
    assert pa.mastery == 0.75
    assert pa.band == "Developing"
    pb = result.point_results["b"]
    assert pb.mastery == 1.0
    assert pb.band == "Secure"


def test_insufficient_evidence_when_too_few_items_answered():
    c = _curriculum()
    result = evaluate(c, {"a1": "A"})  # only 1 of point a's items, none of b
    assert result.point_results["a"].status == "insufficient_evidence"
    assert result.point_results["a"].mastery is None
    assert result.point_results["b"].status == "insufficient_evidence"


def test_strand_rollup_averages_and_flags_weakest():
    c = _curriculum()
    result = evaluate(c, {"a1": "Z", "a2": "10", "b1": "2", "b2": "3"})
    strand = result.strands[0]
    assert strand.strand == "Number"
    assert strand.average_mastery == pytest.approx(0.875)
    assert strand.weakest_point_id == "a"


def test_practice_responses_are_ignored_by_scoring():
    points = {"a": KnowledgePoint("a", "Number", "A", "d", (), ("X",))}
    items = {
        "a1": Item("a1", ("a",), 1, "numeric", "?", "1", {}, {}),
        "a2": Item("a2", ("a",), 1, "numeric", "?", "2", {}, {}),
        "ap": Item("ap", ("a",), 1, "numeric", "?", "9", {}, {}, role="practice"),
    }
    bands = (Band("Secure", 0.8), Band("Developing", 0.5), Band("Not yet", 0.0))
    c = Curriculum(points=points, items=items, bands=bands, standards={"X": {}})
    # 'ap' is a practice item; even if (wrongly) present in responses it must not be scored
    result = evaluate(c, {"a1": "1", "a2": "2", "ap": "0"})
    pa = result.point_results["a"]
    assert pa.answered_count == 2           # only the two diagnostic items
    assert pa.mastery == 1.0                # 'ap' wrong answer did not drag it down
