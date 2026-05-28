# app/chain/orchestrator.py

from typing import List, Any
from app.chain.contracts import PipelineStep
from app.chain.errors import PipelineError
from app.config import logger


class PipelineOrchestrator:
    """
    Executes a sequence of pipeline steps with centralized error handling.
    """

    def __init__(self, steps: List[PipelineStep]):
        self.steps = steps

    def run(self, input: Any) -> Any:
        value: Any = input

        for step in self.steps:
            step_name = type(step).__name__
            try:
                logger.info("PipelineOrchestrator: invoking step '%s'", step_name)
                value = step.invoke(value)
            except PipelineError:
                # Redan en pipeline-aware exception, bara bubbla upp
                logger.error("PipelineOrchestrator: step '%s' raised PipelineError", step_name, exc_info=True)
                raise
            except Exception as exc:
                # Wrap ALL other exceptions i en PipelineError
                logger.error(
                    "PipelineOrchestrator: step '%s' failed with unexpected error: %s",
                    step_name,
                    str(exc),
                    exc_info=True,
                )
                raise PipelineError(
                    message="Unexpected error in pipeline step",
                    step_name=step_name,
                    original_exception=exc,
                ) from exc

        return value
