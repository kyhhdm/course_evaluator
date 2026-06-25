from engine.loader import load_catalog

CATALOG = "standards/ccss_math.yaml"
SCHEMA = "schemas/standards_catalog.schema.json"


def test_catalog_validates_and_has_required_fields():
    cat = load_catalog(CATALOG, SCHEMA)
    assert "CCSS.5.NF.A.1" in cat
    for code, std in cat.items():
        assert std.framework and std.grade and std.domain and std.description, code


def test_catalog_contains_all_26_grade5_standards():
    cat = load_catalog(CATALOG, SCHEMA)
    grade5 = [c for c, s in cat.items() if s.grade == "5"]
    assert len(grade5) == 26, f"expected 26 grade-5 standards, found {len(grade5)}"


# The exact canonical set of CCSS Grade-5 Math codes, verified against the official text
# in standards/reference/ (see SOURCES.md). This pins the catalog so any added, dropped,
# or renamed code fails the build rather than silently drifting.
OFFICIAL_GRADE5_CCSS_MATH = frozenset({
    "CCSS.5.OA.A.1", "CCSS.5.OA.A.2", "CCSS.5.OA.B.3",
    "CCSS.5.NBT.A.1", "CCSS.5.NBT.A.2", "CCSS.5.NBT.A.3", "CCSS.5.NBT.A.4",
    "CCSS.5.NBT.B.5", "CCSS.5.NBT.B.6", "CCSS.5.NBT.B.7",
    "CCSS.5.NF.A.1", "CCSS.5.NF.A.2", "CCSS.5.NF.B.3", "CCSS.5.NF.B.4",
    "CCSS.5.NF.B.5", "CCSS.5.NF.B.6", "CCSS.5.NF.B.7",
    "CCSS.5.MD.A.1", "CCSS.5.MD.B.2", "CCSS.5.MD.C.3", "CCSS.5.MD.C.4", "CCSS.5.MD.C.5",
    "CCSS.5.G.A.1", "CCSS.5.G.A.2", "CCSS.5.G.B.3", "CCSS.5.G.B.4",
})


def test_catalog_grade5_codes_match_official_set():
    cat = load_catalog(CATALOG, SCHEMA)
    grade5 = {c for c, s in cat.items() if s.grade == "5"}
    missing = OFFICIAL_GRADE5_CCSS_MATH - grade5
    extra = grade5 - OFFICIAL_GRADE5_CCSS_MATH
    assert not missing, f"catalog is missing official Grade-5 codes: {sorted(missing)}"
    assert not extra, f"catalog has non-official Grade-5 codes: {sorted(extra)}"


def test_catalog_includes_grade4_prerequisite():
    cat = load_catalog(CATALOG, SCHEMA)
    assert "CCSS.4.NF.A.1" in cat
    assert cat["CCSS.4.NF.A.1"].grade == "4"
