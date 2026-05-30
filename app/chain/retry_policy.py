# app/chain/retry_policy.py

import math
import random


class RetryPolicy:
    """
    Simple exponential backoff retry policy.
    Used by LLMRunner to decide delay between retries.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 0.5,
        max_delay: float = 5.0,
        factor: float = 2.0,
        jitter: float = 0.1,
    ) -> None:
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.factor = factor
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """
        Returns delay (in seconds) before the next retry.
        attempt: 0-based attempt index.
        """
        delay = self.base_delay * (self.factor ** attempt)
        delay = min(delay, self.max_delay)

        # Add small jitter to avoid thundering herd
        jitter_value = delay * self.jitter
        delay = delay + random.uniform(-jitter_value, jitter_value)

        return max(0.0, delay)
