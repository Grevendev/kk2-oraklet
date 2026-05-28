# app/container.py

from app.chain.config import PipelineConfig
from app.chain.orchestrator import PipelineOrchestrator
from app.chain.steps import PromptBuilder, LLMRunner, ResponseParser


def get_pipeline():
    """
    Builds the production pipeline using PipelineConfig.
    """

    config = PipelineConfig(
        steps=[
            PromptBuilder(),
            LLMRunner(),
            ResponseParser(),
        ],
        model_name="gpt-4o-mini",
        parser_strategy="default",
    )

    return PipelineOrchestrator(config.steps)
