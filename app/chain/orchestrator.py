# app/chain/orchestrator.py

from typing import List, Any
from time import perf_counter
from uuid import uuid4

from app.chain.contracts import PipelineStep
from app.chain.errors import PipelineError
from app.config import logger


class PipelineOrchestrator:
    """
    Executes a sequence of pipeline steps with centralized error handling,
    structured logging and tracing (trace_id + span_id).
    """

    def __init__(self, steps: List[PipelineStep]):
        self.steps = steps

    def run(self, input: Any) -> Any:
        trace_id = str(uuid4())
        value: Any = input

        logger.info({
            "event": "pipeline_start",
            "trace_id": trace_id,
            "step_count": len(self.steps),
        })

        for step in self.steps:
            step_name = type(step).__name__
            span_id = str(uuid4())
            start = perf_counter()

            logger.info({
                "event": "pipeline_step_start",
                "trace_id": trace_id,
                "span_id": span_id,
                "step": step_name,
            })

            try:
                value = step.invoke(value)

                duration_ms = (perf_counter() - start) * 1000
                logger.info({
                    "event": "pipeline_step_success",
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "step": step_name,
                    "duration_ms": round(duration_ms, 2),
                })

            except PipelineError:
                duration_ms = (perf_counter() - start) * 1000
                logger.error({
                    "event": "pipeline_step_failure",
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "step": step_name,
                    "duration_ms": round(duration_ms, 2),
                    "error_type": "PipelineError",
                }, exc_info=True)
                raise

            except Exception as exc:
                duration_ms = (perf_counter() - start) * 1000
                logger.error({
                    "event": "pipeline_step_failure",
                    "trace_id": trace_id,
                    "span_id": span_id,
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

        logger.info({
            "event": "pipeline_end",
            "trace_id": trace_id,
        })

        return value
