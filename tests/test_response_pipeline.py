import pytest

from aicaller.ai.llm import LLMDelta
from aicaller.ai.response_pipeline import AIResponsePipeline, ResponsePipelineError


def test_response_pipeline_validates_finished_llm_stream() -> None:
    pipeline = AIResponsePipeline()
    result = pipeline.validate_stream(
        (
            LLMDelta("Nam", sequence=1),
            LLMDelta("aste", sequence=2, is_final=True),
        ),
        language="hi",
    )
    assert result.text == "Namaste"
    assert result.language == "hi"


def test_response_pipeline_rejects_unfinished_stream() -> None:
    pipeline = AIResponsePipeline()
    with pytest.raises(ResponsePipelineError, match="did not finish"):
        pipeline.validate_stream((LLMDelta("hello", sequence=1),))
