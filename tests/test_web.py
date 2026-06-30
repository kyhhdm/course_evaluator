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
