from engine.cli import main

BASE = [
    "--curriculum", "curriculum/grade5_math",
    "--responses", "curriculum/grade5_math/sample_responses.yaml",
    "--name", "Sam",
]


def test_cli_parent_report_runs_end_to_end(capsys):
    code = main(BASE + ["--audience", "parent"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Learning Report for Sam" in out
    assert "Number & Operations" in out


def test_cli_student_report_includes_a_plan(capsys):
    code = main(BASE + ["--audience", "student"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Your Learning Plan, Sam" in out
    assert "Step 1" in out


def test_cli_coverage_report(capsys):
    code = main(["--curriculum", "curriculum/grade5_math", "--coverage"])
    out = capsys.readouterr().out
    assert code == 0
    assert "CCSS-Math grade 5" in out
    assert "26 / 26" in out
    assert "100.0%" in out
    assert "CCSS.5.NF.A.1" in out


def test_cli_requires_responses_without_coverage():
    import pytest
    with pytest.raises(SystemExit):
        main(["--curriculum", "curriculum/grade5_math"])


def test_cli_paper_writes_print_pack(tmp_path):
    out = tmp_path / "pack"
    code = main([
        "--curriculum", "curriculum/grade5_math",
        "--paper", "--out", str(out),
    ])
    assert code == 0
    for fname in ("test_paper.pdf", "answer_sheet.pdf", "answer_key.pdf"):
        p = out / fname
        assert p.exists() and p.read_bytes()[:4] == b"%PDF"
    blank = (out / "answers_blank.yaml").read_text()
    assert "responses:" in blank
    assert "EQF-1:" in blank


def test_cli_paper_requires_out():
    import pytest
    with pytest.raises(SystemExit):
        main(["--curriculum", "curriculum/grade5_math", "--paper"])


def test_cli_pdf_report_writes_pdf(tmp_path):
    out = tmp_path / "rep"
    code = main(BASE + ["--pdf", "--out", str(out)])
    assert code == 0
    p = out / "report.pdf"
    assert p.exists() and p.read_bytes()[:4] == b"%PDF"
