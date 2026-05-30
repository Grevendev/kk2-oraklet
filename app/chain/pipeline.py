# app/chain/pipeline.py
#
# Central pipeline assembly for the Oraklet AI system.
# This file constructs the full Runnable chain:
#
#   PromptBuilder → LLMRunner → ResponseParser
#
# The pipeline is created once and reused by /ai/ask.


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
    """

    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.llm_runner = LLMRunner()
        self.parser = ResponseParser()

    def run(self, question: str, dataset=None):
        """
        Executes the full chain and returns ResponseParserOutput.
        """

        # Determine stats source
        stats_source = None

        if dataset and hasattr(dataset, "stats"):
            stats_source = dataset.stats
        else:
            stats_source = state.stats

        # Ensure stats is always a dict
        if not isinstance(stats_source, dict):
            stats_source = {}

        # Step 1: Build prompt
        prompt_input = PromptBuilderInput(
            question=question,
            stats=stats_source
        )
        prompt_output = self.prompt_builder.invoke(prompt_input)

        # Step 2: Run LLM
        llm_output = self.llm_runner.invoke(prompt_output)

        # Step 3: Parse response
        parsed = self.parser.invoke(llm_output)

        # Insert original question
        parsed.question = question

        return parsed


# Create a global pipeline instance
pipeline = OrakletPipeline()
