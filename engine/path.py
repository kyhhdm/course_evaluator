from __future__ import annotations

from engine.models import Curriculum, EvaluationResult, PathStep


def impact(curriculum: Curriculum, point_id: str) -> int:
    return sum(1 for p in curriculum.points.values() if point_id in p.prerequisites)


def build_path(curriculum: Curriculum, result: EvaluationResult) -> list[PathStep]:
    secure = curriculum.bands[0].name
    weak = [
        pid
        for pid, pr in result.point_results.items()
        if pr.status == "scored" and pr.band != secure
    ]
    weak_set = set(weak)

    indeg = {
        pid: sum(1 for pre in curriculum.points[pid].prerequisites if pre in weak_set)
        for pid in weak
    }
    remaining = set(weak)
    ordered: list[str] = []
    while remaining:
        ready = [pid for pid in remaining if indeg[pid] == 0]
        if not ready:  # safety: integrity tests forbid cycles, but never loop forever
            ready = list(remaining)
        ready.sort(key=lambda p: (-impact(curriculum, p), p))
        chosen = ready[0]
        ordered.append(chosen)
        remaining.remove(chosen)
        for q in remaining:
            if chosen in curriculum.points[q].prerequisites:
                indeg[q] -= 1

    steps: list[PathStep] = []
    for pid in ordered:
        practice = [
            it.id
            for it in sorted(curriculum.practice_items_for_point(pid),
                             key=lambda i: (i.difficulty, i.id))
        ]
        steps.append(PathStep(pid, curriculum.points[pid].title, practice))
    return steps
