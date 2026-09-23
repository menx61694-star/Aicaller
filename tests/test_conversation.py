import pytest

from aicaller.ai.conversation import ConversationError, ConversationManager


def test_conversation_tracks_partial_and_final_user_turn() -> None:
    manager = ConversationManager(max_turns=2)
    manager.apply_user_transcript("hello", sequence=1, is_final=False, language="en")
    assert manager.context().current_transcript == "hello"
    manager.apply_user_transcript("hello there", sequence=2, is_final=True, language="en")

    context = manager.context()
    assert context.current_transcript == ""
    assert context.last_user_language == "en"
    assert context.turns[0].role == "user"
    assert context.turns[0].text == "hello there"


def test_conversation_is_bounded() -> None:
    manager = ConversationManager(max_turns=2)
    for sequence, text in enumerate(("one", "two", "three"), start=1):
        manager.apply_user_transcript(text, sequence=sequence, is_final=True)
    assert [turn.text for turn in manager.context().turns] == ["two", "three"]


def test_conversation_rejects_stale_sequence() -> None:
    manager = ConversationManager()
    manager.apply_user_transcript("one", sequence=1, is_final=True)
    with pytest.raises(ConversationError, match="must increase"):
        manager.apply_user_transcript("old", sequence=1, is_final=True)


def test_conversation_rejects_empty_text() -> None:
    manager = ConversationManager()
    with pytest.raises(ConversationError, match="must not be empty"):
        manager.add_assistant_turn("  ", sequence=1)
