# Authoring a New Course

Copy this `_template/` directory to `curriculum/<your_course_id>/` and fill it in.

## Checklist

1. **course.yaml** — set `id` (must match the folder name), `name`, `framework`
   (e.g. `CCSS-Math`), and `grade`. The `(framework, grade)` pair defines which
   standards count toward this course's coverage.
2. **Standards catalog** — make sure every standard you will reference exists in
   `standards/<framework>.yaml` (filename = framework lowercased with `-` → `_`,
   e.g. `CCSS-Math` → `ccss_math.yaml`). Add missing standards there, not here.
3. **knowledge_map.yaml** — author strands and knowledge points. Each point needs
   `id`, `strand`, `title`, `description`, optional `prerequisites` (ids of other
   points), and `standard_refs` (catalog codes). Keep prerequisites acyclic.
4. **item_bank.yaml** — author at least 2 items per knowledge point. Each item needs
   `id`, `points`, `difficulty` (1–3), `type` (`mcq`|`numeric`), `prompt`, `answer`,
   and (for mcq) `options`. No distractor may equal the keyed answer.
5. **bands.yaml** (optional) — only add one here if this course needs thresholds
   different from `methodology/bands.yaml`; otherwise the shared default is used.
6. **Verify** — run `python -m pytest` (the content-integrity tests validate
   structure) and `python -m engine.cli --curriculum curriculum/<your_course_id>
   --coverage` to see standards coverage.
