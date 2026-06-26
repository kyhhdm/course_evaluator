from __future__ import annotations

from engine.models import (
    Curriculum,
    EvaluationResult,
    Item,
    PointResult,
    StrandResult,
)

MIN_ITEMS = 2


def is_correct(item: Item, response: str | None) -> bool:
    if response is None:
        return False
    given = str(response).strip()
    expected = str(item.answer).strip()
    if item.type == "numeric":
        try:
            return float(given) == float(expected)
        except ValueError:
            return given == expected
    return given.lower() == expected.lower()


def evaluate(curriculum: Curriculum, responses: dict[str, str]) -> EvaluationResult:
    point_results: dict[str, PointResult] = {}
    for pid, point in curriculum.points.items():
        answered = [it for it in curriculum.diagnostic_items_for_point(pid) if it.id in responses]
        if len(answered) < MIN_ITEMS:
            point_results[pid] = PointResult(pid, None, None, "insufficient_evidence", len(answered))
            continue
        numerator = sum(it.difficulty * (1 if is_correct(it, responses[it.id]) else 0) for it in answered)
        denominator = sum(it.difficulty for it in answered)
        mastery = numerator / denominator
        band = curriculum.band_for(mastery).name
        point_results[pid] = PointResult(pid, mastery, band, "scored", len(answered))

    strands = _build_strands(curriculum, point_results)
    answered_item_ids = {it_id for it_id in responses if it_id in curriculum.items}
    return EvaluationResult(strands=strands, point_results=point_results, answered_item_ids=answered_item_ids)


def _build_strands(curriculum: Curriculum, point_results: dict[str, PointResult]) -> list[StrandResult]:
    strands: list[StrandResult] = []
    for strand in curriculum.strands():
        prs = [point_results[p.id] for p in curriculum.points_in_strand(strand)]
        scored = [pr for pr in prs if pr.status == "scored"]
        if scored:
            average = sum(pr.mastery for pr in scored) / len(scored)
            band = curriculum.band_for(average).name
            weakest = min(scored, key=lambda pr: (pr.mastery, pr.point_id)).point_id
        else:
            average, band, weakest = None, None, None
        strands.append(StrandResult(strand, band, average, weakest, prs))
    return strands
