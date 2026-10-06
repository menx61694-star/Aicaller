from aicaller.ai.conversation import ConversationManager
from aicaller.ai.disclosure import AIDisclosurePolicy
from aicaller.ai.intent import CallIntent, IntentContextStore
from aicaller.ai.llm import LLMDelta
from aicaller.ai.policy import PolicyAction, PolicyContextStore
from aicaller.ai.response_pipeline import AIResponsePipeline


def test_phase3_deterministic_ai_chain() -> None:
    conversation = ConversationManager()
    conversation.apply_user_transcript(
        "Mujhe urgent help chahiye",
        sequence=1,
        is_final=True,
        language="hi",
    )

    intent = IntentContextStore()
    intent.update(CallIntent.URGENT, 0.95, source_sequence=1)

    policy = PolicyContextStore()
    policy.update(
        PolicyAction.REQUEST_HUMAN,
        "urgent caller requires human review",
        source_sequence=1,
    )

    pipeline = AIResponsePipeline()
    result = pipeline.validate_stream(
        (
            LLMDelta("Ji, ", sequence=1),
            LLMDelta("main help karta hoon.", sequence=2, is_final=True),
        ),
        language="hi",
    )

    disclosure = AIDisclosurePolicy().disclosure("hi")

    assert conversation.context().last_user_language == "hi"
    assert intent.get().intent is CallIntent.URGENT
    assert policy.get().action is PolicyAction.REQUEST_HUMAN
    assert result.text == "Ji, main help karta hoon."
    assert result.language == "hi"
    assert disclosure is not None
    assert disclosure.language == "hi"
