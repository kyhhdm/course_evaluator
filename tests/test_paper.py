from engine.models import Band, Curriculum, Item, KnowledgePoint
from engine.paper import ordered_groups, ordered_items, render_paper_html

TEMPLATES = "templates"


def _curriculum():
    points = {
        "a": KnowledgePoint("a", "Fractions", "Equivalent fractions", "d", (), ()),
        "b": KnowledgePoint("b", "Fractions", "Add fractions", "d", ("a",), ()),
    }
    items = {
        "A1": Item("A1", ("a",), 1, "mcq", "Which equals 1/2?", "B", {"A": "2/3", "B": "3/6"}, {}),
        "A2": Item("A2", ("a",), 2, "numeric", "2/5 = ?/20", "42", {}, {}),
        "B1": Item("B1", ("b",), 1, "numeric", "1/5 + 2/5 = ?/5", "3", {}, {}),
    }
    bands = (Band("Secure", 0.8), Band("Developing", 0.5), Band("Not yet", 0.0))
    return Curriculum(points=points, items=items, bands=bands, standards={})


def test_ordered_groups_groups_by_strand_each_item_once():
    groups = ordered_groups(_curriculum())
    assert [g["strand"] for g in groups] == ["Fractions"]
    flat = [it.id for it in ordered_items(_curriculum())]
    assert flat == ["A1", "A2", "B1"]


def test_paper_html_shows_prompts_and_options_but_no_answers():
    html = render_paper_html(_curriculum(), TEMPLATES)
    assert "Which equals 1/2?" in html      # prompt present
    assert "3/6" in html                      # mcq option text present
    assert "42" not in html                   # numeric answer NOT leaked
    assert "correct" not in html.lower()      # no correct-answer marker
    assert "1/5 + 2/5 = ?/5" in html   # numeric item's prompt renders
    assert "Answer:" in html            # numeric blank rendered (else-branch covered)


def test_answer_key_html_shows_answers_and_feedback():
    from engine.paper import render_answer_key_html
    c = _curriculum()
    c.items["A1"].distractor_feedback = {"A": "Scale numerator and denominator together."}
    html = render_answer_key_html(c, TEMPLATES)
    assert "Equivalent fractions" in html          # point title shown on the key
    assert "42" in html                             # numeric answer shown
    assert "Scale numerator" in html                # distractor feedback shown


def test_answer_sheet_html_lists_every_item_id():
    from engine.paper import render_answer_sheet_html
    html = render_answer_sheet_html(_curriculum(), TEMPLATES)
    for item_id in ("A1", "A2", "B1"):
        assert item_id in html
    assert "42" not in html      # the sheet is blank — no answers
