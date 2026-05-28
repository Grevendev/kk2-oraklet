# app/chain/orchestrator.py

from typing import List, Any
from app.chain.contracts import PipelineStep

class PipelineOrchestrator:
    """
    Executes a sequence of pipeline steps.
    """

    def __init__(self, steps: List[PipelineStep]):
        self.steps = steps

    def run(self, input: Any) -> Any:
        value = input
        for step in self.steps:
            value = step.invoke(value)
        return value
