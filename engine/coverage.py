from __future__ import annotations

from engine.models import CoverageReport, Curriculum


def compute_coverage(curriculum: Curriculum) -> CoverageReport:
    meta = curriculum.meta
    scope = {
        code
        for code, std in curriculum.standards.items()
        if std.framework == meta.framework and std.grade == meta.grade
    }
    referenced = {ref for p in curriculum.points.values() for ref in p.standard_refs}
    covered = sorted(scope & referenced)
    missing = sorted(scope - referenced)
    out_of_scope = sorted(referenced - scope)
    percentage = len(covered) / len(scope) if scope else 0.0
    return CoverageReport(
        framework=meta.framework,
        grade=meta.grade,
        total=len(scope),
        covered=covered,
        missing=missing,
        out_of_scope=out_of_scope,
        percentage=percentage,
    )


def format_coverage(report: CoverageReport) -> str:
    lines = [
        f"Coverage: {report.framework} grade {report.grade}",
        f"  {len(report.covered)} / {report.total} standards covered "
        f"({report.percentage * 100:.1f}%)",
        f"  Covered: {', '.join(report.covered) if report.covered else '(none)'}",
        f"  Missing ({len(report.missing)}): "
        f"{', '.join(report.missing) if report.missing else '(none)'}",
    ]
    if report.out_of_scope:
        lines.append(
            "  Out of scope (referenced, other grade/framework): "
            + ", ".join(report.out_of_scope)
        )
    return "\n".join(lines)
