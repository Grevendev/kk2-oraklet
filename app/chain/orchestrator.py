# app/chain/orchestrator.py

from typing import List, Any, TypeVar, Generic, get_origin, get_args
from time import perf_counter
from uuid import uuid4

from app.chain.contracts import PipelineStep
from app.chain.errors import PipelineError
from app.config import logger

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class PipelineOrchestrator(Generic[InputT, OutputT]):
    """
    Executes a sequence of pipeline steps with centralized error handling,
    structured logging, tracing and runtime schema validation.
    """

    def __init__(self, steps: List[PipelineStep[Any, Any]]):
        self.steps = steps

    # ----------------------------------------------------------------------
    # Runtime schema validation between steps
    # ----------------------------------------------------------------------
    def _validate_step_types(self, prev_step, next_step, value):
        """
        Validates that the output type of prev_step matches the input type of next_step.
        """

        prev_bases = getattr(prev_step.__class__, "__orig_bases__", [])
        next_bases = getattr(next_step.__class__, "__orig_bases__", [])

        if not prev_bases or not next_bases:
            return

        try:
            prev_generic = get_args(prev_bases[0])
            next_generic = get_args(next_bases[0])
        except Exception:
            return

        if len(prev_generic) != 2 or len(next_generic) != 2:
            return

        prev_output_type = prev_generic[1]
        next_input_type = next_generic[0]

        # Validate runtime type
        if not isinstance(value, next_input_type):
            raise PipelineError(
                message=(
                    f"Schema mismatch: step '{type(prev_step).__name__}' "
                    f"returned {type(value).__name__}, but "
                    f"'{type(next_step).__name__}' expects {next_input_type.__name__}"
                ),
                step_name=type(next_step).__name__,
            )

    # ----------------------------------------------------------------------
    # Pipeline execution
    # ----------------------------------------------------------------------
    def run(self, input: InputT) -> OutputT:
        trace_id = str(uuid4())
        value: Any = input

        logger.info({
            "event": "pipeline_start",
            "trace_id": trace_id,
            "step_count": len(self.steps),
        })

        for i, step in enumerate(self.steps):
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
                # Execute step
                value = step.invoke(value)

                # NEW: schema validation between steps
                if i < len(self.steps) - 1:
                    next_step = self.steps[i + 1]
                    self._validate_step_types(step, next_step, value)

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

        return value  # type: ignore[return-value]
