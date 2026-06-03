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
        # Tester använder "CLOSED", "OPEN", "HALF_OPEN"
        self.state = "CLOSED"
        self.opened_at = 0.0

    # ---------------------------------------------------------
    # Compatibility with test suite
    # ---------------------------------------------------------
    @property
    def max_failures(self) -> int:
        return self.failure_threshold

    @max_failures.setter
    def max_failures(self, value: int) -> None:
        self.failure_threshold = value

    @property
    def failure_count(self) -> int:
        return self.failures

    @failure_count.setter
    def failure_count(self, value: int) -> None:
        self.failures = value

    # ---------------------------------------------------------
    # Internal mechanics
    # ---------------------------------------------------------
    def _trip(self) -> None:
        self.state = "OPEN"
        self.opened_at = time.time()

    def _can_recover(self) -> bool:
        return (time.time() - self.opened_at) >= self.recovery_time_sec

    def before_call(self) -> None:
        if self.state == "OPEN":
            if self._can_recover():
                self.state = "HALF_OPEN"
            else:
                raise PipelineError(
                    message="Circuit breaker is OPEN — LLM temporarily disabled.",
                    step_name="LLMRunner",
                )

    def after_success(self) -> None:
        self.failures = 0
        self.state = "CLOSED"

    def after_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self._trip()
    
    def reset(self) -> None:
        """
        Fully reset the circuit breaker to a clean CLOSED state.
        Used in test envionments to avoid state leakage between tests.
        """
        self.failures = 0
        self.state = "CLOSED"
        self.opened_at = 0.0
