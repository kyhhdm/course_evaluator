# Item Pool with Diagnostic/Practice Roles — Design

**Date:** 2026-06-26
**Status:** Approved, pending implementation plan
**Scope:** Foundational item-bank capability. First of two sequenced sub-projects;
the second (report-quality improvements: per-point detail, unassessed-area caveat,
strengths section, plan-length capping) builds on top of this one and is **out of scope here**.

## Goal

Turn the item bank into a larger pool where each item has an explicit **role** —
`diagnostic` (appears on the test, is scored) or `practice` (reserved for the learning
path). This makes the student plan's practice links functional and lets the question bank
grow without diagnostic and practice questions overlapping. Authoring a question stays
"append a YAML entry."

## Why now

`engine/path.py` currently defines a step's practice items as *diagnostic items for the
point that were not answered on the test* (`path.py:39-43`). Because the diagnostic uses
all 2–3 authored items per point, nothing is left over, so every practice list renders as
"(No extra practice items available yet for this skill.)". The role split fixes this at the
root: practice items are a separate pool, never placed on the test.

## Non-goals

- No database engine, no selection/sampling logic — the test is **all** diagnostic items,
  practice is **all** practice items. Fully deterministic, no seeding.
- No directory-split of the item bank (single `item_bank.yaml` per course stays). Explicit
  YAGNI; clean upgrade path later if volume demands.
- No report-template changes beyond what is needed to render the now-populated practice
  links. Per-point detail, unassessed-area caveat, strengths section, and plan-length
  capping are the **next** sub-project.
- No change to coverage, bands, or scoring math.

## Schema & model

- **`schemas/item_bank.schema.json`** — add an optional `role` property:
  `{"enum": ["diagnostic", "practice"]}`. Not added to `required`; absence means
  `diagnostic`. `additionalProperties: false` is preserved.
- **`engine/loader.py`** — when building each `Item`, set
  `role = data.get("role", "diagnostic")` (JSON Schema `default` is annotation-only and is
  not applied by `jsonschema`, so the loader applies it).
- **`engine/models.py`** — `Item` gains `role: str = "diagnostic"` as the **last** field, so
  existing positional `Item(...)` construction in tests stays valid.
- **`engine/models.py`** — `Curriculum.items_for_point` gains an optional role filter:
  `items_for_point(self, point_id: str, role: str | None = None) -> list[Item]`
  (default `None` = all roles; backward-compatible). Add two thin convenience accessors used
  by callers: `diagnostic_items_for_point(pid)` and `practice_items_for_point(pid)`, each
  delegating to `items_for_point(pid, role=...)`.

## Where the diagnostic/practice split applies

- **Test surfaces — `engine/paper.py`.** `ordered_groups` (and therefore `ordered_items`,
  the test paper, answer sheet, answer key, and `answers_blank.yaml`) bucket only
  `role == "diagnostic"` items. Practice items never appear on the printed test or in the
  blank responses file.
- **Scoring — `engine/score.py`.** `evaluate` treats diagnostic items as the answerable
  universe: `answered = [it for it in curriculum.diagnostic_items_for_point(pid) if it.id in
  responses]`. Practice items are never on the test, so this is explicit-clarity more than a
  behavior change, but it guarantees a stray practice id in `responses` can never be scored.
  The `MIN_ITEMS` (=2) floor now means "≥2 answered **diagnostic** items".
- **Learning path — `engine/path.py`.** A step's practice list becomes the point's practice
  pool, ordered easy→hard:
  `practice = [it.id for it in sorted(curriculum.practice_items_for_point(pid), key=lambda i:
  (i.difficulty, i.id))]`. This replaces the "unanswered diagnostic items" heuristic. (The
  secondary `i.id` sort key removes the pre-existing equal-difficulty nondeterminism.)
- **Coverage — `engine/coverage.py`.** Unchanged; it reads knowledge-point `standard_refs`,
  not items.

## Content plan

- **Migrate** the 68 existing items: add `role: diagnostic` to each. (They are the test.)
- **Author** 2–3 `role: practice` items per knowledge point across all 28 points
  (~60–80 new items). Each item:
  - is math-verified (answer correct), schema-valid, and maps to exactly its one point;
  - has `difficulty` 1–3 (so the path orders practice easy→hard);
  - for MCQs, passes the ambiguous-distractor guard (no distractor equals the keyed answer)
    and may include `distractor_feedback`;
  - is distinct from the diagnostic items for that point (different numbers/wording).
- **Storage** stays a single `item_bank.yaml` per course, organized by knowledge point with
  the point's diagnostic items first, then its practice items, under a clear comment header.
- **`curriculum/_template/`** — add `role` to the skeleton item and a note in its
  `AUTHORING.md` explaining diagnostic vs practice.

## Report wiring

`report_student.md.j2` already renders `step.practice_item_ids` and falls back to the
"(none available)" line only when the list is empty. Once `path.py` populates the list from
the practice pool, real prompts appear; no template change is required beyond confirming this
behavior with a test. Plan-length capping and the richer report sections are deferred to the
next sub-project.

## Testing & determinism

- **`tests/test_content_integrity.py`** gains role-awareness for the Grade-5 content:
  - every item has an explicit `role` in (`diagnostic`, `practice`);
  - **≥2 diagnostic items per point** (the scoring `MIN_ITEMS` floor);
  - **≥2 practice items per point**;
  - the existing ambiguous-distractor guard runs over **all** items (diagnostic + practice);
  - existing checks (prerequisites resolve, no cycles, standard refs exist) unchanged.
- **`tests/test_schemas.py`** — `role` accepted with a valid enum value; an invalid `role`
  rejected.
- **`tests/test_models.py` / `tests/test_loader.py`** — `role` defaults to `diagnostic` when
  absent; `items_for_point(role=...)` and the two convenience accessors filter correctly.
- **`tests/test_path.py`** — a point with practice items yields those ids (difficulty-ordered)
  in its `PathStep`, independent of which diagnostic items were answered; a point with no
  practice items yields an empty list.
- **`tests/test_paper.py`** — the print pack / blank YAML exclude `role: practice` items.
- **`tests/test_score.py`** — scoring is unchanged for diagnostic-only responses; a practice
  id present in `responses` is ignored.
- Determinism: no selection logic; diagnostic = all diagnostic items, practice = all practice
  items, both in stable (item-bank / difficulty+id) order. The pipeline stays a pure function
  over the YAML.

## Risks / mitigations

- **Large content-authoring surface (~60–80 items).** Mitigated by per-point authoring with
  math verification and the content-integrity guards as the gate; the implementation plan
  decomposes authoring per strand/point so each chunk is independently testable.
- **Positional `Item` construction in tests.** Mitigated by appending `role` as the last
  field with a default.
- **Silent regressions in test surfaces.** Mitigated by explicit "practice items excluded
  from the print pack / blank YAML" tests and the role-aware integrity checks.
