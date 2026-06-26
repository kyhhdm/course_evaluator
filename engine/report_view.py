from __future__ import annotations

from dataclasses import dataclass, field

from engine.models import Curriculum, EvaluationResult, PathStep


@dataclass
class StrandGroup:
    strand: str
    band: str | None
    secure: list[str] = field(default_factory=list)
    developing: list[str] = field(default_factory=list)
    not_yet: list[str] = field(default_factory=list)
    not_assessed: list[str] = field(default_factory=list)


@dataclass
class Strengths:
    strong_strands: list[str] = field(default_factory=list)
    highlight_points: list[str] = field(default_factory=list)


@dataclass
class ParentReportView:
    student_name: str
    strand_groups: list[StrandGroup]
    strengths: Strengths
    secure_skill_count: int
    assessed_skill_count: int
    unassessed_skill_count: int
    secure_strand_count: int
    total_strand_count: int
    focus: list[PathStep]


def build_parent_view(
    curriculum: Curriculum,
    result: EvaluationResult,
    path: list[PathStep],
    student_name: str = "Student",
) -> ParentReportView:
    bands = curriculum.bands
    assert len(bands) == 3, "report_view targets the default three-band model"
    secure_name, developing_name, not_yet_name = (bands[0].name, bands[1].name, bands[2].name)

    strand_groups: list[StrandGroup] = []
    secure_skill_count = assessed_skill_count = unassessed_skill_count = 0
    highlight_points: list[str] = []

    for sr in result.strands:
        group = StrandGroup(strand=sr.strand, band=sr.band)
        for pr in sr.point_results:
            title = curriculum.points[pr.point_id].title
            if pr.status == "insufficient_evidence":
                group.not_assessed.append(title)
                unassessed_skill_count += 1
                continue
            assessed_skill_count += 1
            if pr.band == secure_name:
                group.secure.append(title)
                secure_skill_count += 1
                highlight_points.append(title)
            elif pr.band == developing_name:
                group.developing.append(title)
            else:
                group.not_yet.append(title)
        strand_groups.append(group)

    strong_strands = [sr.strand for sr in result.strands if sr.band == secure_name]
    strengths = Strengths(strong_strands=strong_strands, highlight_points=highlight_points[:3])

    return ParentReportView(
        student_name=student_name,
        strand_groups=strand_groups,
        strengths=strengths,
        secure_skill_count=secure_skill_count,
        assessed_skill_count=assessed_skill_count,
        unassessed_skill_count=unassessed_skill_count,
        secure_strand_count=len(strong_strands),
        total_strand_count=len(result.strands),
        focus=path[:3],
    )
