import pytest
from src.message import detect_lang

@pytest.mark.parametrize("text,expected_langs", [
    ("Hello, how are you?", ["en"]),
    ("Привет, как дела?", ["ru", "mk", "uk", "bg"]),
    ("Hola, ¿cómo estás?", ["es"]),
    ("Bonjour tout le monde", ["fr"]),
    ("Hallo, wie geht's dir?", ["de", "af", "nl"]),
])
def test_detect_lang_basic(text, expected_langs):
    detected = detect_lang(text)
    assert detected in expected_langs, f"Got '{detected}' not in {expected_langs}"


def test_detect_lang_empty_string():
    assert detect_lang("") is None

def test_detect_lang_numbers_only():
    assert detect_lang("1234567890") is None

def test_detect_lang_symbol_noise():
    assert detect_lang("!@#$%^&*()_+") is None
