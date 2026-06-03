# app/container_test.py

from app.chain.orchestrator import PipelineOrchestrator
from app.chain.steps import PromptBuilder, ResponseParser
from app.chain.steps import LLMRunnerOutput
from app.chain.contracts import PipelineStep


class FakeLLMRunner(PipelineStep):
    """
    Test-only LLM runner that returns deterministic output.
    """

    def invoke(self, input):
        return LLMRunnerOutput(
            raw_output=(
                f"{input.prompt}\n\n"
                "Answer: Detta är ett test-svar från FakeLLMRunner."
            )
        )


def get_test_pipeline():
    """
    Returns a clean, deterministic pipeline for pytest.
    """
    return PipelineOrchestrator([
        PromptBuilder(),
        FakeLLMRunner(),
        ResponseParser(),
    ])

def get_retry_test_pipeline():
    """
    Pipeline som använder riktiga LLMRunner för retry-policy tester.
    """
    from app.chain.steps import LLMRunner
    return PipelineOrchestrator([
        PromptBuilder(),
        LLMRunner(),
        ResponseParser(),
    ])

