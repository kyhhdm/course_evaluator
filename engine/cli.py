from __future__ import annotations

import argparse
import os

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
    parser.add_argument("--paper", action="store_true",
                        help="Write the offline print pack (paper, answer sheet, answer key, "
                             "blank responses file) into --out and exit.")
    parser.add_argument("--pdf", action="store_true",
                        help="Also write the evaluation report as report.pdf into --out.")
    parser.add_argument("--out", help="Output directory for --paper / --pdf.")
    args = parser.parse_args(argv)

    curriculum = load_course(args.curriculum, args.schemas, args.methodology, args.standards)

    if args.coverage:
        print(format_coverage(compute_coverage(curriculum)))
        return 0

    if args.paper:
        if not args.out:
            parser.error("--paper requires --out")
        os.makedirs(args.out, exist_ok=True)
        from engine.paper import (
            render_answer_key_html,
            render_answer_sheet_html,
            render_answer_sheet_template,
            render_paper_html,
        )
        from engine.pdf import html_to_pdf

        html_to_pdf(render_paper_html(curriculum, args.templates),
                    os.path.join(args.out, "test_paper.pdf"))
        html_to_pdf(render_answer_sheet_html(curriculum, args.templates),
                    os.path.join(args.out, "answer_sheet.pdf"))
        html_to_pdf(render_answer_key_html(curriculum, args.templates),
                    os.path.join(args.out, "answer_key.pdf"))
        with open(os.path.join(args.out, "answers_blank.yaml"), "w") as fh:
            fh.write(render_answer_sheet_template(curriculum))
        print(f"Wrote print pack to {args.out}")
        return 0

    if not args.responses:
        parser.error("--responses is required unless --coverage or --paper is given")
    from engine.paper import drop_blank_responses
    responses = drop_blank_responses(load_yaml(args.responses)["responses"])
    result = evaluate(curriculum, responses)
    path = build_path(curriculum, result)

    if args.pdf:
        if not args.out:
            parser.error("--pdf requires --out")
        os.makedirs(args.out, exist_ok=True)
        from engine.paper import render_report_html
        from engine.pdf import html_to_pdf

        out_path = os.path.join(args.out, "report.pdf")
        html_to_pdf(render_report_html(curriculum, result, path, args.templates, args.name),
                    out_path)
        print(f"Wrote report to {out_path}")
        return 0

    if args.audience == "parent":
        print(render_parent(curriculum, result, path, args.templates, args.name))
    else:
        print(render_student(curriculum, result, path, args.templates, args.name))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
