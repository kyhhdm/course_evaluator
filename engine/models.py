from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class KnowledgePoint:
    id: str
    strand: str
    title: str
    description: str
    prerequisites: tuple[str, ...] = ()
    standard_refs: tuple[str, ...] = ()


@dataclass
class Item:
    id: str
    points: tuple[str, ...]
    difficulty: int
    type: str
    prompt: str
    answer: str
    options: dict[str, str] = field(default_factory=dict)
    distractor_feedback: dict[str, str] = field(default_factory=dict)
    role: str = "diagnostic"


@dataclass
class Band:
    name: str
    min_score: float


@dataclass
class PointResult:
    point_id: str
    mastery: float | None
    band: str | None
    status: str  # "scored" | "insufficient_evidence"
    answered_count: int


@dataclass
class StrandResult:
    strand: str
    band: str | None
    average_mastery: float | None
    weakest_point_id: str | None
    point_results: list[PointResult]


@dataclass
class EvaluationResult:
    strands: list[StrandResult]
    point_results: dict[str, PointResult]
    answered_item_ids: set[str]


@dataclass
class PathStep:
    point_id: str
    title: str
    practice_item_ids: list[str]


@dataclass
class Standard:
    framework: str
    grade: str
    domain: str
    description: str


@dataclass
class CourseMeta:
    id: str
    name: str
    framework: str
    grade: str


@dataclass
class CoverageReport:
    framework: str
    grade: str
    total: int
    covered: list[str]
    missing: list[str]
    out_of_scope: list[str]
    percentage: float


@dataclass
class Curriculum:
    points: dict[str, KnowledgePoint]
    items: dict[str, Item]
    bands: tuple[Band, ...]  # sorted descending by min_score
    standards: dict[str, Standard]
    meta: CourseMeta | None = None

    def items_for_point(self, point_id: str) -> list[Item]:
        return [it for it in self.items.values() if point_id in it.points]

    def points_in_strand(self, strand: str) -> list[KnowledgePoint]:
        return [p for p in self.points.values() if p.strand == strand]

    def strands(self) -> list[str]:
        seen: list[str] = []
        for p in self.points.values():
            if p.strand not in seen:
                seen.append(p.strand)
        return seen

    def band_for(self, score: float) -> Band:
        for band in self.bands:  # already descending by min_score
            if score >= band.min_score:
                return band
        return self.bands[-1]
