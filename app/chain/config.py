# app/chain/config.py

from typing import List, Type
from app.chain.contracts import PipelineStep


class PipelineConfig:
    """
    Defines how a pipeline should be constructed:
    - which steps to include
    - in which order
    - which model or parser strategy to use (future extension)
    """

    def __init__(
        self,
        steps: List[PipelineStep],
        model_name: str = "gpt-4o-mini",
        parser_strategy: str = "default",
    ) -> None:
        self.steps = steps
        self.model_name = model_name
        self.parser_strategy = parser_strategy
