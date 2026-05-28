# app/chain/contracts.py

from typing import Protocol, TypeVar, Generic

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")

class PipelineStep(Protocol, Generic[InputT, OutputT]):
    """
    Formal contract for all pipeline steps.
    Every step must implement:
        def invoke(self, input: InputT) -> OutputT
    """
    def invoke(self, input: InputT) -> OutputT:
        ...
