# app/chain/retry_policy.py

import random
import time


class RetryPolicy:
    """
    Exponential backoff with jitter for transient LLM failures.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 0.2,
        max_delay: float = 2.0,
    ) -> None:
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        """
        Exponential backoff + jitter.
        """
        exp = min(self.max_delay, self.base_delay * (2 ** attempt))
        jitter = random.uniform(0, exp * 0.25)
        return exp + jitter
