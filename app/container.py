# app/container.py
#
# Enkel DI-container för att bygga produktions-pipelinen.
# Använder PipelineOrchestrator direkt utan PipelineConfig
# (som inte finns i din kodbas).

from app.chain.orchestrator import PipelineOrchestrator
from app.chain.steps import PromptBuilder, LLMRunner, ResponseParser


def get_pipeline() -> PipelineOrchestrator:
    """
    Builds the production pipeline.
    """
    steps = [
        PromptBuilder(),
        LLMRunner(),
        ResponseParser(),
    ]
    return PipelineOrchestrator(steps)
