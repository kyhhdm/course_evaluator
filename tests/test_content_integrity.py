import pytest

from engine.loader import load_curriculum

CURRICULUM_DIR = "curriculum/grade5_math"
SCHEMAS_DIR = "schemas"


@pytest.fixture(scope="module")
def curriculum():
    return load_curriculum(CURRICULUM_DIR, SCHEMAS_DIR)


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
