# Richer Parent Report + Focused Student Plan — Design

**Date:** 2026-06-27
**Status:** Approved, pending implementation plan
**Scope:** The remaining report-quality improvements identified when reviewing a simulated
report: deliver the two-layer model in the parent report (per-point detail), surface
unassessed skills, add a strengths section, and cap the student plan length. Builds on the
merged item-pool/roles work (PR #5).

## Goal

Make the parent report a complete, trustworthy snapshot a parent can act on — showing not
just strand headlines but the knowledge-point breakdown beneath them, what the student is
strong at, and which skills could not be assessed — while keeping the student report a short,
focused action plan.

## Problems being fixed (observed in a simulated report)

1. The parent report shows only 5 strand bands + 3 focus titles; the 26 per-point results
   (the actionable detail the methodology promises) never appear.
2. Skills left blank score as `insufficient_evidence` and silently vanish — a strand can read
   "Secure" while hiding an unassessed point, which misleads a parent.
3. The report leads entirely with weaknesses; the student's genuine strengths are not named.
4. The student plan lists every gap (11 steps in the simulation), overwhelming the reader.

## Non-goals

- No change to scoring, bands, path-ordering, coverage, or the item bank.
- No new dependencies. No PDF/print-pack structural change beyond the parent report's content.
- Student report stays markdown-only (no student PDF); it gains only the plan cap.
- No change to `build_path`'s return value (it still returns the full ordered path).

## Audience split

- **Parent report** (markdown via `render_parent` AND PDF via `render_report_html`): gains
  per-point detail, strengths, and unassessed handling.
- **Student report** (markdown via `render_student`): gains only the plan-length cap; keeps
  its step-by-step actionable plan.

## Architecture — one derivation, dumb templates

`render_parent` (in `engine/report.py`) and `render_report_html` (in `engine/paper.py`)
currently duplicate the `secure_count` computation, and the templates do ad-hoc logic. Adding
strengths/groupings/unassessed to both renderers would multiply that duplication. Introduce a
single pure builder that both consume:

- **`engine/report_view.py`** (new) — `build_parent_view(curriculum, result, path) ->
  ParentReportView`. Pure function over existing dataclasses; no I/O, no new deps.
- **`ParentReportView`** dataclass fields:
  - `student_name: str`
  - `strand_groups: list[StrandGroup]` — one per strand, in knowledge-map strand order.
  - `strengths: Strengths` — strongest strands + secure-skill highlights.
  - `secure_skill_count: int`, `assessed_skill_count: int`, `unassessed_skill_count: int`
  - `secure_strand_count: int`, `total_strand_count: int`
  - `focus: list[PathStep]` — the top 3 path steps (parent focus, unchanged).
- **`StrandGroup`** dataclass:
  - `strand: str`, `band: str | None`
  - `secure: list[str]`, `developing: list[str]`, `not_yet: list[str]`,
    `not_assessed: list[str]` — knowledge-point **titles**, each list in knowledge-map order.
  The band→list mapping is derived from each point's `PointResult` (`status` +`band`):
  `insufficient_evidence` → `not_assessed`; otherwise the point's band name selects the list
  (`Secure`/`Developing`/`Not yet`). Band-name→bucket uses `curriculum.bands` names, so a
  course with custom band names still maps correctly (highest band → `secure`-equivalent
  bucket; see "Band mapping" below).
- **`Strengths`** dataclass:
  - `strong_strands: list[str]` — strands whose `band` equals the top band name, in order.
  - `highlight_points: list[str]` — up to 3 secure point titles, knowledge-map order.
  (The template renders the "N of M assessed skills are secure, including …" sentence from
  these plus the counts.)

Both `render_parent` and `render_report_html` call `build_parent_view` and pass the view to
their templates; `report_parent.md.j2` and `report.html.j2` become dumb presenters of the
same structure.

### Band mapping (determinism + custom bands)

`curriculum.bands` is sorted highest-first (`Secure`, `Developing`, `Not yet` by default).
The builder maps each scored point to one of the three named `StrandGroup` fields by its band
name: the default band names `Secure`/`Developing`/`Not yet` map to `secure`/`developing`/
`not_yet` respectively. The builder asserts these three default band names are present in
`curriculum.bands`; a course using a different band set is a documented known limitation (a
later enhancement), not a silent mis-bucketing. "Secure" (the top band) is always referenced
via `curriculum.bands[0].name`, never a hard-coded string, so `strengths.strong_strands` and
`secure_skill_count` stay correct if the top band is renamed.

## Parent report layout

```
Learning Report for {name}

Where {name} stands
  {Strand}: {band}
    Secure:       {titles; "; "-joined}        (line shown only when non-empty)
    Developing:   {titles}
    Not yet:      {titles}
    Not assessed: {titles} (too few answers)
  ... every strand, in knowledge-map order

What this means
  {name} is Secure in {secure_strand_count} of {total_strand_count} areas.
  {if unassessed_skill_count} {unassessed_skill_count} skill(s) couldn't be assessed —
  too few answers there.

Strengths
  {if strong_strands} Strongest in {strong_strands joined}. {endif}
  {secure_skill_count} of {assessed_skill_count} assessed skills are secure{if highlight_points},
  including {highlight_points joined}{endif}.

Focus next
  1..3. {focus step titles}   (unchanged; empty-state text unchanged)
```

A group line renders only when its list is non-empty. The HTML/PDF template mirrors this
exact structure with the existing `print.css` styling.

## Student report — focused plan

`render_student` slices the path to the top 5 steps and passes the remainder count to the
template. `report_student.md.j2` renders the 5 steps (with their practice items, unchanged)
then, when there are more, a closing line: "…and {remainder} more area(s) to work on after
these." `build_path` is unchanged. The cap constant (5) lives in `render_student` (named
constant `STUDENT_PLAN_STEPS = 5`).

## Testing

- **`tests/test_report_view.py`** (new): `build_parent_view` groups scored points into the
  correct band buckets; `insufficient_evidence` points land in `not_assessed`; `strengths`
  lists top-band strands and ≤3 secure highlights; counts (`secure_skill_count`,
  `assessed_skill_count`, `unassessed_skill_count`) are correct; ordering is knowledge-map
  order; uses a small fixture covering all four buckets in one strand and an all-unassessed
  strand.
- **`tests/test_report.py`**: parent markdown renders the per-point group labels, the
  unassessed headline note, and the strengths sentence; empty-state paths still render.
- **`tests/test_paper.py`**: `render_report_html` renders the same per-point groups, strengths,
  and unassessed note in HTML.
- **`tests/test_report.py`**: student report caps at 5 steps and shows the "…and N more" note
  when the path is longer; shows no note when ≤5; practice items still render.
- Determinism asserted on group/strengths ordering.
- Full suite green via `uv run pytest`.

## Risks / mitigations

- **Duplication creeping back** — mitigated by the single `build_parent_view` builder both
  renderers consume.
- **Custom band sets** — the builder targets the default three-band model the course uses and
  drives "secure" off `curriculum.bands[0].name`; non-default band sets are a documented known
  limitation, not silently mis-bucketed (the builder asserts the expected band names).
- **Verbosity** — group lines render only when non-empty; strengths and counts are one
  sentence each.
