from __future__ import annotations

import argparse

from engine.coverage import compute_coverage, format_coverage
from engine.loader import load_course, load_yaml
from engine.path import build_path
from engine.report import render_parent, render_student
from engine.score import evaluate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a student's diagnostic responses.")
    parser.add_argument("--curriculum", required=True)
    parser.add_argument("--schemas", default="schemas")
    parser.add_argument("--methodology", default="methodology")
    parser.add_argument("--standards", default="standards")
    parser.add_argument("--templates", default="templates")
    parser.add_argument("--responses")
    parser.add_argument("--name", default="Student")
    parser.add_argument("--audience", choices=["parent", "student"], default="parent")
    parser.add_argument("--coverage", action="store_true",
                        help="Print the standards-coverage report and exit.")
    args = parser.parse_args(argv)

    curriculum = load_course(args.curriculum, args.schemas, args.methodology, args.standards)

    if args.coverage:
        print(format_coverage(compute_coverage(curriculum)))
        return 0

    if not args.responses:
        parser.error("--responses is required unless --coverage is given")
    responses = load_yaml(args.responses)["responses"]
    result = evaluate(curriculum, responses)
    path = build_path(curriculum, result)

    if args.audience == "parent":
        print(render_parent(curriculum, result, path, args.templates, args.name))
    else:
        print(render_student(curriculum, result, path, args.templates, args.name))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
