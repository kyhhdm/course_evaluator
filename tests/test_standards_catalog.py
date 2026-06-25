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
