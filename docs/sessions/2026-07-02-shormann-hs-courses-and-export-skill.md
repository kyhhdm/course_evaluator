# Shormann HS math courses + an export-session skill

- **Date:** 2026-07-02
- **Branch / commits:** `feat/shormann-hs-math` → merged to `main` as PR #11 (merge `7246d05`); key commits `dd55945` (HS catalog), `8c78d28` (parametrized tests), `9985be3` (Alg 1), `8e15e3e` (Alg 2), `ffc2a6d` (alignment report), `8f47495` (source PDFs). New `export-session` skill under `.claude/skills/` (untracked at session end).
- **Summary:** Added two Shormann-modeled high-school math courses (Algebra 1 & 2 with integrated geometry) plus a CCSS high-school standards band and a Shormann→CCSS alignment report, shipped via PR #11; then built and tested a reusable `export-session` skill that writes a session summary plus a verbatim transcript into `docs/sessions/`.

## Request

Two threads:
1. "Add math courses for high schoolers, and check how the high-school credits at `diveintomath.com/shormann` align to CCSS."
2. "Create a skill to let the user export a session to `docs/sessions/xxx.md` with a name representing the whole session" — then extended to also save the whole conversation verbatim beside the summary.

## What we did

**Shormann HS courses (thread 1):**
- Researched the Shormann lineup and credits (Algebra 1 & 2 each fold in ½ Geometry; combined = 1 credit each of Alg 1, Alg 2, Geometry). Shormann is explicitly *not* Common Core, so the CCSS crosswalk is one we constructed.
- Found the key engine fact: the loader stringifies `grade` and coverage is a plain equality, so a shared `grade: "HS"` band works with **no engine/schema changes**.
- Brainstormed a design (spec committed), folded in the real lesson-level scope from the Shormann Teacher's Guides, then wrote a bite-sized implementation plan.
- Executed the plan with subagent-driven development — a fresh implementer + reviewer per task, then a final whole-branch review:
  1. Added 25 HS CCSS standards (`grade: HS`) + a catalog pin test.
  2. Parametrized the content-integrity suite over all courses.
  3. Authored Shormann Algebra 1 (6 points, 24 items; coverage 12/25).
  4. Authored Shormann Algebra 2 (6 points, 24 items; coverage 15/25).
  5. Wrote the Shormann→CCSS alignment report.
- Every authored answer key was independently math-verified in review. Final review: READY TO MERGE, no Critical/Important. Merged PR #11 (locally, since the token lacked merge-API permission) and preserved the Shormann source PDFs under `standards/reference/`.

**export-session skill (thread 2):**
- Followed writing-skills TDD: RED baseline (agent invented an ad-hoc convention), GREEN (skill drove correct location, naming, and structure — and a better whole-session name), REFACTOR (fixed a self-contradictory date rule and an ambiguous "omit if none").
- Extended it per the follow-up request: since a skill cannot invoke `/export`, added `scripts/render_transcript.py`, which renders the current session's on-disk JSONL (`$CLAUDE_CODE_SESSION_ID`) to a verbatim Markdown transcript. Verified it against this session (426 messages).

## Artifacts

- Courses: `curriculum/shormann_algebra_1/`, `curriculum/shormann_algebra_2/` (4 YAML files each).
- Standards: 25 HS entries appended to `standards/ccss_math.yaml`; pin tests in `tests/test_standards_catalog.py`.
- Tests: `tests/test_content_integrity.py` parametrized over `COURSE_DIRS`.
- Docs: `docs/shormann-ccss-alignment.md`; spec + plan under `docs/superpowers/`.
- References: `standards/reference/Shormann_Algebra{1,2}_TeacherGuide.pdf`, `Shormann_Algebra2_ScopeAndSequence.pdf` + `SOURCES.md` section.
- Skill: `.claude/skills/export-session/SKILL.md` + `scripts/render_transcript.py`.

## Outcome

- PR #11 merged to `main`; full suite **121 passed**. Combined HS coverage 24/25 (only `CCSS.HSN.Q.A.1` uncovered, by design); grade-5 coverage unchanged.
- `export-session` skill created and tested; produces this pair of files.

## Follow-ups

- Decide whether to commit `.claude/skills/export-session/` (currently untracked; usable as-is).
- These two `docs/sessions/` files are untracked — commit them if you want the session record versioned.
