from src.language import detect_language


def test_language_detection_targets_supported_languages():
    assert detect_language("Привет, нужна виза") == "ru"
    assert detect_language("Need visa information") == "en"
    assert detect_language("Toshkentda ish bormi") == "uz"
    assert detect_language("ขอวีซ่าได้ไหม") == "th"
    assert detect_language("12345") == "other"


def test_language_detection_falls_back_from_missing_fasttext_model():
    config = {"backend": "fasttext", "fasttext_model_path": "missing.bin"}
    assert detect_language("Need visa information", config) == "en"
