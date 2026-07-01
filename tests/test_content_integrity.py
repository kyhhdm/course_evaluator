import pytest

from engine.loader import load_course, load_yaml

SCHEMAS_DIR = "schemas"
METHODOLOGY_DIR = "methodology"
STANDARDS_DIR = "standards"

# Courses covered by the content-integrity gate. Later courses are appended here.
COURSE_DIRS = [
    "curriculum/grade5_math",
    "curriculum/shormann_algebra_1",
    "curriculum/shormann_algebra_2",
]


@pytest.fixture(scope="module")
def curricula():
    return {
        d: load_course(d, SCHEMAS_DIR, METHODOLOGY_DIR, STANDARDS_DIR)
        for d in COURSE_DIRS
    }


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_prerequisites_reference_existing_points(course_dir, curricula):
    curriculum = curricula[course_dir]
    ids = set(curriculum.points)
    for p in curriculum.points.values():
        for pre in p.prerequisites:
            assert pre in ids, f"{course_dir}: {p.id} has unknown prerequisite {pre}"


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_no_prerequisite_cycles(course_dir, curricula):
    points = curricula[course_dir].points
    WHITE, GREY, BLACK = 0, 1, 2
    color = {pid: WHITE for pid in points}

    def visit(pid):
        color[pid] = GREY
        for pre in points[pid].prerequisites:
            if color[pre] == GREY:
                raise AssertionError(f"{course_dir}: cycle through {pid} -> {pre}")
            if color[pre] == WHITE:
                visit(pre)
        color[pid] = BLACK

    for pid in points:
        if color[pid] == WHITE:
            visit(pid)


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_every_point_has_at_least_two_diagnostic_items(course_dir, curricula):
    curriculum = curricula[course_dir]
    for pid in curriculum.points:
        assert len(curriculum.diagnostic_items_for_point(pid)) >= 2, \
            f"{course_dir}: {pid} has < 2 diagnostic items"


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_every_point_has_at_least_two_practice_items(course_dir, curricula):
    curriculum = curricula[course_dir]
    for pid in curriculum.points:
        assert len(curriculum.practice_items_for_point(pid)) >= 2, \
            f"{course_dir}: {pid} has < 2 practice items"


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_every_item_has_explicit_role(course_dir):
    raw = load_yaml(f"{course_dir}/item_bank.yaml")["items"]
    for it in raw:
        assert it.get("role") in ("diagnostic", "practice"), \
            f"{course_dir}: item {it['id']} is missing an explicit role"


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_every_item_references_existing_points(course_dir, curricula):
    curriculum = curricula[course_dir]
    ids = set(curriculum.points)
    for it in curriculum.items.values():
        for pid in it.points:
            assert pid in ids, f"{course_dir}: item {it.id} references unknown point {pid}"


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_every_standard_ref_exists_in_mapping(course_dir, curricula):
    curriculum = curricula[course_dir]
    codes = set(curriculum.standards)
    for p in curriculum.points.values():
        for ref in p.standard_refs:
            assert ref in codes, f"{course_dir}: {p.id} references unknown standard {ref}"


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_sample_responses_only_reference_real_items(course_dir, curricula):
    curriculum = curricula[course_dir]
    responses = load_yaml(f"{course_dir}/sample_responses.yaml")["responses"]
    for item_id in responses:
        assert item_id in curriculum.items, \
            f"{course_dir}: response references unknown item {item_id}"


# Allowed Shormann lesson numbers per Algebra 1 knowledge point (from the design spec).
ALLOWED_LESSONS = {
    "a1-num-realnum": {2, 3},
    "a1-num-exprad": {3, 30, 31, 32, 33, 58},
    "a1-num-units": {5, 6, 44, 45},
    "a1-expr-interpret": {8, 35, 36, 37, 38},
    "a1-expr-model": {7, 8, 48},
    "a1-expr-linear": {7, 46},
    "a1-poly-ops": {37, 38},
    "a1-poly-factor": {51, 75, 91},
    "a1-quad-solve": {75, 76, 91, 92},
    "a1-complex": {92, 95},
    "a1-func-concept": {15, 52, 53},
    "a1-func-graph": {16, 55, 56, 57},
    "a1-func-linexp": {48, 81},
    "a1-systems": {17, 61, 64, 70},
    "a1-geo-def": {9, 10, 11},
    "a1-geo-proof": {10, 66, 67, 68},
    "a1-geo-circle": {40, 66},
    "a1-geo-sim": {6, 9},
    "a1-geo-trig": {12, 19, 43, 80},
    "a1-geo-measure": {13, 41, 42},
    "a1-data-display": {23},
    "a1-data-scatter": {24, 94},
    "a1-data-interpret": {24, 94},
}


def test_shormann_alg1_items_cite_consistent_lessons(curricula):
    """Every Algebra 1 item cites >=1 lesson in 1..100, consistent with its point."""
    course = curricula["curriculum/shormann_algebra_1"]
    for item in course.items.values():
        for pt in item.points:
            if pt in ALLOWED_LESSONS:
                assert item.lesson_refs, f"{item.id} has no lesson_refs"
                for L in item.lesson_refs:
                    assert 1 <= L <= 100, f"{item.id} lesson {L} out of range"
                    assert L in ALLOWED_LESSONS[pt], (
                        f"{item.id} cites lesson {L} not allowed for {pt}"
                    )


@pytest.mark.parametrize("course_dir", COURSE_DIRS)
def test_mcq_options_have_no_duplicate_values(course_dir, curricula):
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

    for item in curricula[course_dir].items.values():
        if item.type != "mcq":
            continue
        option_pairs = []
        for key, val in item.options.items():
            numeric = parse_option(val)
            if numeric is not None:
                option_pairs.append((key, numeric, val))
        answer_key = getattr(item, "answer", None)
        answer_numeric = None
        if answer_key and answer_key in item.options:
            answer_numeric = parse_option(item.options[answer_key])
        if answer_numeric is not None:
            for key, val, raw in option_pairs:
                if key == answer_key:
                    continue
                assert abs(val - answer_numeric) >= 1e-9, (
                    f"{course_dir}: item {item.id}: distractor {key}='{raw}' is "
                    f"numerically equal to keyed answer {answer_key}="
                    f"'{item.options[answer_key]}'"
                )
