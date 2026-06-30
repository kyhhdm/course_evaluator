import pytest

from engine.web import create_app, list_courses


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("COURSE_EVAL_DB", str(tmp_path / "web.db"))
    app = create_app(secret="test-secret")
    app.config.update(TESTING=True)
    return app.test_client()


def test_home_ok_and_create_student(client):
    assert client.get("/").status_code == 200
    r = client.post("/students", data={"name": "Maya"}, follow_redirects=True)
    assert r.status_code == 200
    assert b"Maya" in r.data            # landed on the student page
    assert b"No attempts yet" in r.data


def test_empty_name_rejected(client):
    r = client.post("/students", data={"name": "  "}, follow_redirects=True)
    assert b"Please enter a name" in r.data


def test_unknown_student_404(client):
    assert client.get("/students/999").status_code == 404


def test_list_courses_has_grade5():
    assert "grade5_math" in list_courses()


def test_student_history_and_report(client):
    from engine import store
    from engine.loader import load_course, load_yaml

    sid = store.create_student("Leo")
    c = load_course("curriculum/grade5_math", "schemas", "methodology", "standards")
    resp = load_yaml("curriculum/grade5_math/sample_responses.yaml")["responses"]
    aid = store.save_attempt(sid, "grade5_math", resp, c)

    page = client.get(f"/students/{sid}")
    assert page.status_code == 200
    assert b"Leo" in page.data and b"areas secure" in page.data   # history summary shown

    report = client.get(f"/attempts/{aid}")
    assert report.status_code == 200
    assert b"Learning Report for Leo" in report.data


def test_unknown_attempt_404(client):
    assert client.get("/attempts/999").status_code == 404


def _start(client, name="Maya"):
    from engine import store
    sid = store.create_student(name)
    client.get(f"/students/{sid}/test?start=1")
    return sid


def test_wizard_starts_at_first_question(client):
    sid = _start(client)
    r = client.get(f"/students/{sid}/test")
    assert r.status_code == 200
    assert b"Question 1 of" in r.data


def test_full_wizard_run_saves_attempt_and_redirects_to_report(client):
    from engine import store
    from engine.loader import load_course
    from engine.paper import ordered_items

    sid = _start(client, "Maya")
    item_ids = [it.id for it in ordered_items(
        load_course("curriculum/grade5_math", "schemas", "methodology", "standards"))]
    r = None
    for _ in item_ids:
        r = client.post(f"/students/{sid}/test", data={"answer": "A", "action": "next"})
    assert r.status_code == 302
    assert "/attempts/" in r.headers["Location"]
    assert len(store.list_attempts(sid)) == 1
    report = client.get(r.headers["Location"])
    assert b"Learning Report for Maya" in report.data


def test_back_preserves_previous_answer(client):
    sid = _start(client)
    client.post(f"/students/{sid}/test", data={"answer": "C", "action": "next"})   # Q1=C → Q2
    client.post(f"/students/{sid}/test", data={"answer": "B", "action": "back"})    # Q2=B → back to Q1
    r = client.get(f"/students/{sid}/test")
    assert b"Question 1 of" in r.data
    assert b'value="C" checked' in r.data            # Q1 answer preserved


def test_unknown_or_traversal_course_is_rejected(client):
    from engine import store
    sid = store.create_student("Maya")
    # path-traversal / unknown course must 404, never 500 or read outside curriculum/
    assert client.get(f"/students/{sid}/test?course=../../etc").status_code == 404
    assert client.get(f"/students/{sid}/test?course=nope").status_code == 404
