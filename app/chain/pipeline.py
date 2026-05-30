# app/chain/pipeline.py
#
# Central pipeline assembly for the Oraklet AI system.
# Denna version använder den generiska PipelineOrchestrator
# istället för att kedja stegen manuellt.

from app.chain.orchestrator import PipelineOrchestrator
from app.chain.steps import (
    PromptBuilder,
    LLMRunner,
    ResponseParser,
    PromptBuilderInput,
)
from app.state import state


class OrakletPipeline:
    """
    High-level orchestrator for the full AI chain.
    Kör:
        PromptBuilder → LLMRunner → ResponseParser
    via PipelineOrchestrator.
    """

    def __init__(self) -> None:
        self.orchestrator = PipelineOrchestrator([
            PromptBuilder(),
            LLMRunner(),
            ResponseParser(),
        ])

    def run(self, question: str, dataset=None):
        """
        Executes the full chain and returns ResponseParserOutput.
        """

        # Bestäm stats-källa
        if dataset is not None and hasattr(dataset, "stats"):
            stats_source = dataset.stats
        else:
            stats_source = state.stats

        # Säkerställ dict
        if not isinstance(stats_source, dict):
            stats_source = {}

        # Bygg input till första steget
        prompt_input = PromptBuilderInput(
            question=question,
            stats=stats_source,
        )

        # Kör hela kedjan via orchestratorn
        parsed = self.orchestrator.run(prompt_input)

        # Sätt originalfrågan på output
        parsed.question = question

        return parsed


# Global pipeline-instans (om du vill använda den direkt)
pipeline = OrakletPipeline()
