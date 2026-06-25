from engine.cli import main

BASE = [
    "--curriculum", "curriculum/grade5_math",
    "--schemas", "schemas",
    "--responses", "curriculum/grade5_math/sample_responses.yaml",
    "--templates", "templates",
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
