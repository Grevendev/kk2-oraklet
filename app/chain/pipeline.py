# app/chain/pipeline.py
#
# Central pipeline assembly for the Oraklet AI system.
# Kör alla steg via PipelineOrchestrator.

from app.chain.orchestrator import PipelineOrchestrator
from app.chain.steps import (
    PromptBuilder,
    LLMRunner,
    ResponseParser,
    PromptBuilderInput,
    GLOBAL_CIRCUIT_BREAKER,   
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

        
        # Testet förväntar sig att pipeline har en .circuit property.
        self.circuit = GLOBAL_CIRCUIT_BREAKER

    def run(self, question: str, dataset=None):
        """
        Executes the full chain and returns ResponseParserOutput.
        """

        # Bestäm stats-källa
        if dataset is not None and hasattr(dataset, "stats"):
            stats_source = dataset.stats
        else:
            stats_source = state.stats

        if not isinstance(stats_source, dict):
            stats_source = {}

        # Input till första steget
        prompt_input = PromptBuilderInput(
            question=question,
            stats=stats_source,
        )

        # Kör hela kedjan
        parsed = self.orchestrator.run(prompt_input)

        # Sätt originalfrågan
        parsed.question = question

        return parsed


# Global pipeline-instans (om du vill använda den direkt)
pipeline = OrakletPipeline()
