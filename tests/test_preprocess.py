import pandas as pd

from src.preprocess import clean_text, fix_encoding, parse_datetime


def test_fix_encoding_recovers_cyrillic_mojibake():
    assert fix_encoding("Р’РёР·Р°") == "Виза"


def test_clean_text_removes_urls_and_preserves_cyrillic_and_emoji():
    assert clean_text("  Привет 😀 https://example.com  ") == "Привет 😀"


def test_parse_datetime_with_utc_offset():
    parsed = parse_datetime(pd.Series(["13.10.2020 15:59:22 UTC+07:00"]))
    assert str(parsed.iloc[0]) == "2020-10-13 08:59:22+00:00"

