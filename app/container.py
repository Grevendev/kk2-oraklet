# app/container.py

from app.chain.orchestrator import PipelineOrchestrator
from app.chain.steps import PromptBuilder, LLMRunner, ResponseParser

def get_pipeline():
    return PipelineOrchestrator([
        PromptBuilder(),
        LLMRunner(),
        ResponseParser(),
    ])
