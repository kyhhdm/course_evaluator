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


import yaml

from engine.score import evaluate


def test_answer_sheet_template_round_trips_through_evaluate():
    from engine.paper import drop_blank_responses, render_answer_sheet_template
    c = _curriculum()
    text = render_answer_sheet_template(c)
    parsed = yaml.safe_load(text)

    # every item id is present as a key in the responses map
    assert set(parsed["responses"].keys()) == {"A1", "A2", "B1"}

    # blank template -> all values empty -> filtered to nothing -> no scoring, no error
    blank = drop_blank_responses(parsed["responses"])
    assert blank == {}
    result = evaluate(c, blank)
    assert result.point_results["a"].status == "insufficient_evidence"

    # a filled-in pair scores the point (both A-items correct -> Secure)
    filled = drop_blank_responses({"A1": "B", "A2": "8", "B1": ""})
    assert filled == {"A1": "B", "A2": "8"}


from engine.models import EvaluationResult, PathStep, PointResult, StrandResult


def test_report_html_shows_name_band_and_focus():
    from engine.paper import render_report_html
    c = _curriculum()
    pa = PointResult("a", 0.9, "Secure", "scored", 2)
    pb = PointResult("b", 0.4, "Not yet", "scored", 2)
    strand = StrandResult("Fractions", "Developing", 0.65, "b", [pa, pb])
    result = EvaluationResult([strand], {"a": pa, "b": pb}, {"A1"})
    path = [PathStep("b", "Add fractions", ["B1"])]
    html = render_report_html(c, result, path, TEMPLATES, "Sam")
    assert "Sam" in html
    assert "Fractions" in html
    assert "Developing" in html
    assert "Add fractions" in html


def test_print_surfaces_exclude_practice_items():
    from engine.paper import ordered_items, render_paper_html, render_answer_sheet_template
    points = {"a": KnowledgePoint("a", "Fractions", "Equivalent fractions", "d", (), ())}
    items = {
        "D1": Item("D1", ("a",), 1, "numeric", "Diagnostic prompt one", "1", {}, {}),
        "D2": Item("D2", ("a",), 2, "numeric", "Diagnostic prompt two", "2", {}, {}),
        "P1": Item("P1", ("a",), 1, "numeric", "Practice prompt hidden", "9", {}, {}, role="practice"),
    }
    bands = (Band("Secure", 0.8),)
    c = Curriculum(points=points, items=items, bands=bands, standards={})
    assert [it.id for it in ordered_items(c)] == ["D1", "D2"]   # practice excluded
    html = render_paper_html(c, TEMPLATES)
    assert "Diagnostic prompt one" in html
    assert "Practice prompt hidden" not in html
    blank = render_answer_sheet_template(c)
    assert "P1" not in blank and "D1" in blank
