# app/chain/circuit_breaker.py

import time
from app.chain.errors import PipelineError


class CircuitBreaker:
    """
    Simple circuit breaker for protecting unstable steps like LLMRunner.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_time_sec: int = 10,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_time_sec = recovery_time_sec

        self.failures = 0
        self.state = "closed"  # closed, open, half-open
        self.opened_at = 0.0

    # ---------------------------------------------------------
    # Compatibility with test suite
    # ---------------------------------------------------------
    @property
    def max_failures(self) -> int:
        """Tests expect this attribute."""
        return self.failure_threshold

    @property
    def failure_count(self) -> int:
        """Tests expect this attribute."""
        return self.failures

    # ---------------------------------------------------------
    # Internal mechanics
    # ---------------------------------------------------------
    def _trip(self) -> None:
        self.state = "open"
        self.opened_at = time.time()

    def _can_recover(self) -> bool:
        return (time.time() - self.opened_at) >= self.recovery_time_sec

    def before_call(self) -> None:
        if self.state == "open":
            if self._can_recover():
                self.state = "half-open"
            else:
                raise PipelineError(
                    message="Circuit breaker is OPEN — LLM temporarily disabled.",
                    step_name="LLMRunner",
                )

    def after_success(self) -> None:
        self.failures = 0
        self.state = "closed"

    def after_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self._trip()
