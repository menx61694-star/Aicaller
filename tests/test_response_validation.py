import pytest

from aicaller.ai.response_validation import ResponseValidationError, ResponseValidator


def test_response_validator_normalizes_whitespace() -> None:
    result = ResponseValidator().validate("  hello   there\n")
    assert result.text == "hello there"


def test_response_validator_preserves_language() -> None:
    result = ResponseValidator().validate("Namaste", language="hi")
    assert result.language == "hi"


def test_response_validator_rejects_empty_response() -> None:
    with pytest.raises(ResponseValidationError, match="must not be empty"):
        ResponseValidator().validate("   ")


def test_response_validator_rejects_oversized_response() -> None:
    with pytest.raises(ResponseValidationError, match="maximum length"):
        ResponseValidator(max_chars=3).validate("hello")


def test_response_validator_rejects_control_characters() -> None:
    with pytest.raises(ResponseValidationError, match="control characters"):
        ResponseValidator().validate("hello\x00world")


def test_response_validator_rejects_empty_language() -> None:
    with pytest.raises(ResponseValidationError, match="language"):
        ResponseValidator().validate("hello", language=" ")
