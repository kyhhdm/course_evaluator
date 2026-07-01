from __future__ import annotations

from engine.models import Curriculum
from engine.paper import ordered_groups
from engine.score import is_correct


def _is_blank(resp) -> bool:
    return resp is None or str(resp).strip() == ""


def build_review(curriculum: Curriculum, responses: dict) -> list[dict]:
    review: list[dict] = []
    for group in ordered_groups(curriculum):
        point_groups = []
        for pg in group["points"]:
            point = pg["point"]
            questions = []
            correct_count = 0
            for item in pg["items"]:
                resp = responses.get(item.id)
                skipped = _is_blank(resp)
                ok = is_correct(item, resp) if not skipped else False
                if ok:
                    correct_count += 1
                if item.type == "mcq":
                    student_text = "" if skipped else item.options.get(str(resp), "")
                    correct_text = item.options.get(item.answer, "")
                else:
                    student_text = "" if skipped else str(resp)
                    correct_text = item.answer
                feedback = ""
                if not ok and not skipped:
                    feedback = item.distractor_feedback.get(str(resp), "")
                questions.append({
                    "id": item.id,
                    "prompt": item.prompt,
                    "type": item.type,
                    "student_answer": "" if skipped else str(resp),
                    "student_answer_text": student_text,
                    "correct_answer": item.answer,
                    "correct_answer_text": correct_text,
                    "is_correct": ok,
                    "status": "skipped" if skipped else "answered",
                    "feedback": feedback,
                })
            point_groups.append({
                "title": point.title,
                "correct_count": correct_count,
                "total": len(questions),
                "questions": questions,
            })
        review.append({"strand": group["strand"], "points": point_groups})
    return review
