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

    def run(self, question: str):
        """
        Executes the full chain and returns ResponseParserOutput.
        """

        # Step 1: Build prompt
        prompt_input = PromptBuilderInput(
            question=question,
            stats=state.stats
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
