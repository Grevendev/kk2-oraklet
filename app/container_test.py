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
        # input är nu en PromptBuilderOutput som innehåller .messages (en lista)
        # Vi hämtar innehållet från det sista meddelandet som ett exempel
        last_message = input.messages[-1]["content"] if input.messages else ""
        
        return LLMRunnerOutput(
            raw_output=(
                f"{last_message}\n\n"
                "<|im_start|>assistant\n"
                "Answer: Detta är ett test-svar från FakeLLMRunner.<|im_end|>"
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

