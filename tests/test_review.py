from engine.models import Band, Curriculum, Item, KnowledgePoint
from engine.review import build_review


def _curriculum():
    points = {"a": KnowledgePoint("a", "Fractions", "Equivalent fractions", "d", (), ())}
    items = {
        "Q1": Item("Q1", ("a",), 1, "mcq", "Which equals 1/2?", "B",
                   {"A": "one third", "B": "two quarters"}, {"A": "Halve it."}),
        "Q2": Item("Q2", ("a",), 1, "mcq", "Pick the true one", "A",
                   {"A": "right", "B": "wrong"}, {"B": "B is wrong because reasons."}),
        "Q3": Item("Q3", ("a",), 2, "numeric", "2 + 2 = ?", "4", {}, {}),
        "Q4": Item("Q4", ("a",), 1, "mcq", "Skipped one", "A", {"A": "x", "B": "y"}, {}),
    }
    return Curriculum(points=points, items=items, bands=(Band("Secure", 0.8),), standards={})


def test_build_review_groups_marks_and_explains():
    # Q1 correct; Q2 wrong (has feedback); Q3 wrong numeric; Q4 skipped (absent)
    review = build_review(_curriculum(), {"Q1": "B", "Q2": "B", "Q3": "5"})
    assert len(review) == 1 and review[0]["strand"] == "Fractions"
    pg = review[0]["points"][0]
    assert pg["title"] == "Equivalent fractions"
    assert pg["total"] == 4 and pg["correct_count"] == 1
    assert [q["id"] for q in pg["questions"]] == ["Q1", "Q2", "Q3", "Q4"]  # deterministic order
    q = {e["id"]: e for e in pg["questions"]}
    assert q["Q1"]["is_correct"] and q["Q1"]["student_answer_text"] == "two quarters"
    assert q["Q1"]["feedback"] == ""                                    # no feedback when correct
    assert not q["Q2"]["is_correct"] and q["Q2"]["feedback"] == "B is wrong because reasons."
    assert not q["Q3"]["is_correct"] and q["Q3"]["status"] == "answered"
    assert q["Q3"]["correct_answer_text"] == "4"
    assert q["Q4"]["status"] == "skipped" and not q["Q4"]["is_correct"]
    assert q["Q4"]["student_answer"] == ""


def test_mcq_option_text_is_case_insensitive():
    from engine.models import Band, Curriculum, Item, KnowledgePoint
    points = {"a": KnowledgePoint("a", "S", "P", "d", (), ())}
    items = {"Q": Item("Q", ("a",), 1, "mcq", "?", "B", {"A": "aye", "B": "bee"}, {})}
    c = Curriculum(points=points, items=items, bands=(Band("Secure", 0.8),), standards={})
    # lowercase "b" is correct (is_correct is case-insensitive) and resolves the option text
    q = build_review(c, {"Q": "b"})[0]["points"][0]["questions"][0]
    assert q["is_correct"] and q["student_answer_text"] == "bee"
