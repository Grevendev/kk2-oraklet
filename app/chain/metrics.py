# app/chain/metrics.py

from collections import defaultdict
from typing import Dict


class PipelineMetrics:
    """
    Simple in-memory metrics collector for pipeline execution.
    Can later be exposed via Prometheus or any metrics backend.
    """

    def __init__(self) -> None:
        self.pipeline_total_requests = 0
        self.pipeline_total_success = 0
        self.pipeline_total_failures = 0

        self.step_latency_ms: Dict[str, float] = defaultdict(float)
        self.step_success: Dict[str, int] = defaultdict(int)
        self.step_failures: Dict[str, int] = defaultdict(int)

    def record_step_success(self, step: str, duration_ms: float) -> None:
        self.step_success[step] += 1
        self.step_latency_ms[step] += duration_ms

    def record_step_failure(self, step: str, duration_ms: float) -> None:
        self.step_failures[step] += 1
        self.step_latency_ms[step] += duration_ms
