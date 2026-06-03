# app/chain/errors.py

from typing import Optional


class PipelineError(Exception):
    """
    Base error for all pipeline-related failures.
    Wraps underlying exceptions and carries step context.
    """

    def __init__(
        self,
        message: str,
        step_name: Optional[str] = None,
        original_exception: Optional[BaseException] = None,
    ) -> None:
        # Tester kräver att .message finns
        self.message = message

        # Metadata som används av orchestrator och exception handlers
        self.step_name = step_name
        self.original_exception = original_exception

        # Bygg full felsträng
        full_message = message
        if step_name:
            full_message = f"[{step_name}] {full_message}"
        if original_exception:
            full_message = (
                f"{full_message} "
                f"(caused by {type(original_exception).__name__}: {original_exception})"
            )

        # Initiera Exception med full_message
        super().__init__(full_message)


class PromptBuilderError(PipelineError):
    """Errors originating from the PromptBuilder step."""


class LLMRunnerError(PipelineError):
    """Errors originating from the LLMRunner step."""


class ResponseParserError(PipelineError):
    """Errors originating from the ResponseParser step."""
