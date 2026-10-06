import pytest

from aicaller.ai.disclosure import AIDisclosurePolicy, DisclosureError


def test_disclosure_defaults_to_english() -> None:
    result = AIDisclosurePolicy().disclosure()
    assert result is not None
    assert result.language == "en"
    assert "AI" in result.text


def test_disclosure_supports_hindi() -> None:
    result = AIDisclosurePolicy().disclosure("hi")
    assert result is not None
    assert result.language == "hi"


def test_disclosure_falls_back_to_english_for_unknown_language() -> None:
    result = AIDisclosurePolicy().disclosure("mr")
    assert result is not None
    assert result.language == "en"


def test_disclosure_can_be_disabled() -> None:
    assert AIDisclosurePolicy(enabled=False).disclosure() is None


def test_disclosure_rejects_empty_language() -> None:
    with pytest.raises(DisclosureError, match="must not be empty"):
        AIDisclosurePolicy().disclosure(" ")
