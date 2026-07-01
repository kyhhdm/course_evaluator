from engine import store
from engine.loader import load_course, load_yaml

CURRICULUM = "curriculum/grade5_math"


def _grade5():
    return load_course(CURRICULUM, "schemas", "methodology", "standards")


def _db(tmp_path):
    return str(tmp_path / "test.db")


def test_init_db_is_idempotent(tmp_path):
    db = _db(tmp_path)
    store.init_db(db)
    store.init_db(db)  # second call must not raise
    assert (tmp_path / "test.db").exists()


def test_create_and_list_students(tmp_path):
    db = _db(tmp_path)
    sid1 = store.create_student("Maya", db_path=db)
    sid2 = store.create_student("Leo", db_path=db)
    assert sid1 != sid2
    students = store.list_students(db_path=db)
    assert [s["name"] for s in students] == ["Maya", "Leo"]   # ordered by id
    assert all("created_at" in s for s in students)


def test_save_and_get_attempt_roundtrips_with_snapshot(tmp_path):
    db = _db(tmp_path)
    sid = store.create_student("Maya", db_path=db)
    responses = load_yaml(f"{CURRICULUM}/sample_responses.yaml")["responses"]
    aid = store.save_attempt(sid, "grade5_math", responses, _grade5(), db_path=db)

    got = store.get_attempt(aid, db_path=db)
    assert got["student_id"] == sid
    assert got["course_id"] == "grade5_math"
    assert got["responses"]["EQF-1"] == responses["EQF-1"]      # source of truth stored
    snap = got["snapshot"]
    assert snap["version"] == 2                                 # snapshot schema version stamped
    assert "parent_view" in snap and "student_plan" in snap
    assert snap["parent_view"]["student_name"] == "Maya"        # name resolved into the view
    assert "strands" in snap["student_plan"] and "steps" in snap["student_plan"]


def test_get_attempt_returns_none_for_unknown_id(tmp_path):
    db = _db(tmp_path)
    store.init_db(db)
    assert store.get_attempt(999, db_path=db) is None


def test_save_attempt_raises_for_unknown_student(tmp_path):
    import pytest
    db = _db(tmp_path)
    store.init_db(db)
    with pytest.raises(ValueError, match="unknown student_id"):
        store.save_attempt(999, "grade5_math", {}, _grade5(), db_path=db)


def test_list_attempts_newest_first_with_summary(tmp_path):
    db = _db(tmp_path)
    sid = store.create_student("Maya", db_path=db)
    responses = load_yaml(f"{CURRICULUM}/sample_responses.yaml")["responses"]
    c = _grade5()
    a1 = store.save_attempt(sid, "grade5_math", responses, c, db_path=db, created_at="2026-01-01T09:00:00")
    a2 = store.save_attempt(sid, "grade5_math", responses, c, db_path=db, created_at="2026-02-01T09:00:00")

    listed = store.list_attempts(sid, db_path=db)
    assert [a["id"] for a in listed] == [a2, a1]                 # newest first
    assert listed[0]["summary"] == "2 of 5 areas secure"         # exact summary format locked


def test_render_attempt_html_matches_live_and_survives_content_change(tmp_path):
    from engine.paper import render_report_html
    from engine.path import build_path
    from engine.score import evaluate
    from engine.paper import drop_blank_responses

    db = _db(tmp_path)
    sid = store.create_student("Maya", db_path=db)
    responses = load_yaml(f"{CURRICULUM}/sample_responses.yaml")["responses"]
    c = _grade5()
    aid = store.save_attempt(sid, "grade5_math", responses, c, db_path=db)

    # snapshot render matches a live render of the same attempt (key content)
    clean = drop_blank_responses(responses)
    live = render_report_html(c, evaluate(c, clean), build_path(c, evaluate(c, clean)), "templates", "Maya")
    from_snapshot = store.render_attempt_html(store.get_attempt(aid, db_path=db))
    for marker in ("Learning Report for Maya", "Strengths", "fully Secure in"):
        assert marker in live and marker in from_snapshot

    # content-drift immunity: mutate the in-memory curriculum, snapshot still renders
    c.points.clear()
    c.items.clear()
    still = store.render_attempt_html(store.get_attempt(aid, db_path=db))
    assert "Learning Report for Maya" in still      # renders with curriculum cleared
    assert "Equivalent fractions" in still          # a frozen point title survived the clear


def test_save_attempt_freezes_review_v2(tmp_path):
    db = _db(tmp_path)
    sid = store.create_student("Maya", db_path=db)
    responses = load_yaml(f"{CURRICULUM}/sample_responses.yaml")["responses"]
    aid = store.save_attempt(sid, "grade5_math", responses, _grade5(), db_path=db)
    snap = store.get_attempt(aid, db_path=db)["snapshot"]
    assert snap["version"] == 2
    assert isinstance(snap["review"], list) and snap["review"]
    assert snap["review"][0]["strand"]
    q = snap["review"][0]["points"][0]["questions"][0]
    assert {"id", "prompt", "is_correct", "status", "correct_answer"} <= set(q)
