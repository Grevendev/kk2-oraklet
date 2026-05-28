# app/chain/orchestrator.py

from typing import List, Any
from time import perf_counter
from app.chain.contracts import PipelineStep
from app.chain.errors import PipelineError
from app.config import logger


class PipelineOrchestrator:
    """
    Executes a sequence of pipeline steps with centralized error handling
    and structured logging.
    """

    def __init__(self, steps: List[PipelineStep]):
        self.steps = steps

    def run(self, input: Any) -> Any:
        value: Any = input

        for step in self.steps:
            step_name = type(step).__name__

            start = perf_counter()
            logger.info({
                "event": "pipeline_step_start",
                "step": step_name,
            })

            try:
                value = step.invoke(value)

                duration_ms = (perf_counter() - start) * 1000
                logger.info({
                    "event": "pipeline_step_success",
                    "step": step_name,
                    "duration_ms": round(duration_ms, 2),
                })

            except PipelineError:
                duration_ms = (perf_counter() - start) * 1000
                logger.error({
                    "event": "pipeline_step_failure",
                    "step": step_name,
                    "duration_ms": round(duration_ms, 2),
                    "error_type": "PipelineError",
                }, exc_info=True)
                raise

            except Exception as exc:
                duration_ms = (perf_counter() - start) * 1000
                logger.error({
                    "event": "pipeline_step_failure",
                    "step": step_name,
                    "duration_ms": round(duration_ms, 2),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }, exc_info=True)

                raise PipelineError(
                    message="Unexpected error in pipeline step",
                    step_name=step_name,
                    original_exception=exc,
                ) from exc

        return value
