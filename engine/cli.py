from __future__ import annotations

import argparse

from engine.loader import load_curriculum, load_yaml
from engine.path import build_path
from engine.report import render_parent, render_student
from engine.score import evaluate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a student's diagnostic responses.")
    parser.add_argument("--curriculum", required=True)
    parser.add_argument("--schemas", required=True)
    parser.add_argument("--responses", required=True)
    parser.add_argument("--templates", required=True)
    parser.add_argument("--name", default="Student")
    parser.add_argument("--audience", choices=["parent", "student"], default="parent")
    args = parser.parse_args(argv)

    curriculum = load_curriculum(args.curriculum, args.schemas)
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
