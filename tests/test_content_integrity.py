import pytest

from engine.loader import load_course

CURRICULUM_DIR = "curriculum/grade5_math"
SCHEMAS_DIR = "schemas"
METHODOLOGY_DIR = "methodology"
STANDARDS_DIR = "standards"


@pytest.fixture(scope="module")
def curriculum():
    return load_course(CURRICULUM_DIR, SCHEMAS_DIR, METHODOLOGY_DIR, STANDARDS_DIR)


def test_prerequisites_reference_existing_points(curriculum):
    ids = set(curriculum.points)
    for p in curriculum.points.values():
        for pre in p.prerequisites:
            assert pre in ids, f"{p.id} has unknown prerequisite {pre}"


def test_no_prerequisite_cycles(curriculum):
    points = curriculum.points
    WHITE, GREY, BLACK = 0, 1, 2
    color = {pid: WHITE for pid in points}

    def visit(pid):
        color[pid] = GREY
        for pre in points[pid].prerequisites:
            if color[pre] == GREY:
                raise AssertionError(f"cycle through {pid} -> {pre}")
            if color[pre] == WHITE:
                visit(pre)
        color[pid] = BLACK

    for pid in points:
        if color[pid] == WHITE:
            visit(pid)


def test_every_point_has_at_least_two_items(curriculum):
    for pid in curriculum.points:
        assert len(curriculum.items_for_point(pid)) >= 2, f"{pid} has < 2 items"


def test_every_item_references_existing_points(curriculum):
    ids = set(curriculum.points)
    for it in curriculum.items.values():
        for pid in it.points:
            assert pid in ids, f"item {it.id} references unknown point {pid}"


def test_every_standard_ref_exists_in_mapping(curriculum):
    codes = set(curriculum.standards)
    for p in curriculum.points.values():
        for ref in p.standard_refs:
            assert ref in codes, f"{p.id} references unknown standard {ref}"


def test_sample_responses_only_reference_real_items(curriculum):
    from engine.loader import load_yaml
    responses = load_yaml(f"{CURRICULUM_DIR}/sample_responses.yaml")["responses"]
    for item_id in responses:
        assert item_id in curriculum.items, f"response references unknown item {item_id}"


def test_mcq_options_have_no_duplicate_values(curriculum):
    def parse_option(s):
        s = str(s).strip()
        if "/" in s:
            parts = s.split("/")
            if len(parts) == 2:
                try:
                    return float(parts[0]) / float(parts[1])
                except (ValueError, ZeroDivisionError):
                    return None
        try:
            return float(s)
        except ValueError:
            return None

    for item in curriculum.items.values():
        if item.type != "mcq":
            continue
        option_pairs = []
        for key, val in item.options.items():
            numeric = parse_option(val)
            if numeric is not None:
                option_pairs.append((key, numeric, val))
        # Find the numeric value of the keyed answer (if parseable)
        answer_key = getattr(item, "answer", None)
        answer_numeric = None
        if answer_key and answer_key in item.options:
            answer_numeric = parse_option(item.options[answer_key])
        # Assert no distractor is numerically equal to the keyed answer
        # (a distractor that equals the correct answer creates an ambiguous item)
        if answer_numeric is not None:
            for key, val, raw in option_pairs:
                if key == answer_key:
                    continue
                assert abs(val - answer_numeric) >= 1e-9, (
                    f"Item {item.id}: distractor {key}='{raw}' is numerically equal "
                    f"to keyed answer {answer_key}='{item.options[answer_key]}'"
                )
