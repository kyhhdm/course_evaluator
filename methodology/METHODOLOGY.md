# Course Evaluator — Methodology

Shared principles that apply to every course. Course-specific material lives under
`curriculum/<course>/`; the principles here are global.

## Two-layer status model

A student's status is reported at two layers:

- **Strands** — the parent/student headline (e.g. "Number & Operations").
- **Knowledge points** — the actionable detail under each strand, and the unit the
  "where to improve" guidance operates on.

## Scoring — transparent difficulty-weighted thresholds

For each knowledge point, mastery is the difficulty-weighted fraction of answered
items the student got right: `sum(difficulty * correct) / sum(difficulty)`. A point
with fewer than two answered items is reported as *insufficient evidence* rather than
given a false score. Mastery maps to a band:

- **Secure** ≥ 0.8
- **Developing** ≥ 0.5
- **Not yet** ≥ 0.0

Bands live in `methodology/bands.yaml` and may be overridden per course.

## Learning path

The "where to improve" output lists the student's non-Secure points, ordered so that
prerequisite gaps come first (topological order), ties broken by how many later points
depend on each. Each step links practice items for that point, excluding items already
used in the diagnostic.

## Standards & coverage

Each course declares a `framework` and `grade` in its `course.yaml`. Knowledge points
reference standard codes from the shared catalog in `standards/<framework>.yaml`. The
coverage report (`--coverage`) shows how many of that grade's standards the course
covers — an informational measure of project goal #2, never an enforced gate.

## Adding a course

See `curriculum/_template/AUTHORING.md`.
