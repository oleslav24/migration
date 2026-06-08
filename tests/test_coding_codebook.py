from src.coding.codebook import flatten_codes, get_codes_by_group, load_codebook, validate_codebook


def test_codebook_load_validate_and_flatten():
    book = load_codebook("codebooks/migration_codebook.yaml")
    errors = validate_codebook(book)
    assert errors == []
    frame = flatten_codes(book)
    assert {"code_id", "description"}.issubset(frame.columns)
    assert len(frame) > 10


def test_get_codes_by_group_returns_expected_values():
    book = load_codebook("codebooks/migration_codebook.yaml")
    group = get_codes_by_group(book, "migration_driver")
    assert "visa_legal" in group
    assert "work_income" in group

