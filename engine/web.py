from __future__ import annotations

import os
import secrets
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, session

from engine import store
from engine.loader import load_course
from engine.paper import ordered_items

CURRICULUM_ROOT = "curriculum"
SCHEMAS, METHODOLOGY, STANDARDS = "schemas", "methodology", "standards"


def list_courses() -> list[str]:
    root = Path(CURRICULUM_ROOT)
    if not root.is_dir():
        return []
    return sorted(
        d.name
        for d in root.iterdir()
        if d.is_dir() and d.name != "_template" and (d / "course.yaml").exists()
    )


def _load(course_id: str):
    return load_course(f"{CURRICULUM_ROOT}/{course_id}", SCHEMAS, METHODOLOGY, STANDARDS)


def _secret() -> str:
    env = os.environ.get("COURSE_EVAL_SECRET")
    if env:
        return env
    p = Path("var/secret_key")
    if p.exists():
        return p.read_text().strip()
    p.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_hex(32)
    p.write_text(key)
    return key


def _find_student(student_id: int) -> dict:
    for s in store.list_students():
        if s["id"] == student_id:
            return s
    abort(404)


def create_app(secret: str | None = None) -> Flask:
    app = Flask(__name__, template_folder="../templates/web")
    app.secret_key = secret or _secret()

    @app.get("/")
    def home():
        return render_template("home.html", students=store.list_students(), courses=list_courses())

    @app.post("/students")
    def add_student():
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("Please enter a name.")
            return redirect("/")
        sid = store.create_student(name)
        return redirect(f"/students/{sid}")

    @app.get("/students/<int:student_id>")
    def student(student_id):
        s = _find_student(student_id)
        return render_template(
            "student.html",
            student=s,
            attempts=store.list_attempts(student_id),
            courses=list_courses(),
        )

    return app


def main() -> None:
    app = create_app()
    host = os.environ.get("COURSE_EVAL_HOST", "127.0.0.1")
    port = int(os.environ.get("COURSE_EVAL_PORT", "5000"))
    app.run(host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    main()
