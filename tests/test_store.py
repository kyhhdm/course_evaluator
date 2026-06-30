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
    assert "parent_view" in snap and "student_plan" in snap
    assert snap["parent_view"]["student_name"] == "Maya"        # name resolved into the view
    assert "strands" in snap["student_plan"] and "steps" in snap["student_plan"]


def test_get_attempt_returns_none_for_unknown_id(tmp_path):
    store.init_db(_db(tmp_path))
    assert store.get_attempt(999, db_path=_db(tmp_path)) is None
