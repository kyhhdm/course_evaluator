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


# The curated CCSS high-school Math band this project authors HS courses against.
# Pins the catalog so any added/dropped/renamed HS code fails the build.
OFFICIAL_HS_CCSS_MATH = frozenset({
    "CCSS.HSN.Q.A.1", "CCSS.HSN.RN.A.2", "CCSS.HSN.CN.A.1", "CCSS.HSN.CN.C.7",
    "CCSS.HSA.SSE.A.1", "CCSS.HSA.SSE.B.3", "CCSS.HSA.APR.A.1", "CCSS.HSA.CED.A.1",
    "CCSS.HSA.REI.B.3", "CCSS.HSA.REI.B.4", "CCSS.HSA.REI.C.6",
    "CCSS.HSF.IF.A.1", "CCSS.HSF.IF.B.4", "CCSS.HSF.BF.B.3",
    "CCSS.HSF.LE.A.1", "CCSS.HSF.LE.A.2",
    "CCSS.HSG.CO.A.1", "CCSS.HSG.CO.C.10", "CCSS.HSG.SRT.A.2", "CCSS.HSG.SRT.C.8",
    "CCSS.HSG.C.A.2", "CCSS.HSG.GMD.A.3",
    "CCSS.HSS.ID.A.1", "CCSS.HSS.ID.B.6", "CCSS.HSS.ID.C.7",
})


def test_catalog_hs_codes_match_official_set():
    cat = load_catalog(CATALOG, SCHEMA)
    hs = {c for c, s in cat.items() if s.grade == "HS"}
    missing = OFFICIAL_HS_CCSS_MATH - hs
    extra = hs - OFFICIAL_HS_CCSS_MATH
    assert not missing, f"catalog is missing official HS codes: {sorted(missing)}"
    assert not extra, f"catalog has non-official HS codes: {sorted(extra)}"


def test_catalog_hs_entries_are_well_formed():
    cat = load_catalog(CATALOG, SCHEMA)
    for code in OFFICIAL_HS_CCSS_MATH:
        std = cat[code]
        assert std.framework == "CCSS-Math", code
        assert std.grade == "HS", code
        assert std.domain and std.description, code
