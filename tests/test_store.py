from engine import store


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
