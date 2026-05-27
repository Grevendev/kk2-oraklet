# app/chain/steps.py
#
# This file contains the Runnable steps used in the AI pipeline.
# Step 1: PromptBuilder — builds the LLM prompt from question + dataset statistics.
#
# Additional steps (LLMRunner, ResponseParser) will be added later in the same file.


from typing import Dict, Any
from pydantic import BaseModel

from app.chain.runnable import Runnable  # Your generic Runnable[I, O]
from app.config import SYSTEM_PROMPT, logger


# ============================================================
# Pydantic models for PromptBuilder input and output
# ============================================================

class PromptBuilderInput(BaseModel):
    """
    Input model for the PromptBuilder step.
    Contains:
    - question: the user's natural-language question
    - stats: the dataset statistics (df.describe().to_dict())
    """
    question: str
    stats: Dict[str, Any]


class PromptBuilderOutput(BaseModel):
    """
    Output model for the PromptBuilder step.
    Contains:
    - prompt: the fully constructed prompt string to send to the LLM
    """
    prompt: str


# ============================================================
# PromptBuilder — Step 1 in the Runnable chain
# ============================================================

class PromptBuilder(Runnable[PromptBuilderInput, PromptBuilderOutput]):
    """
    Builds a structured prompt for the LLM.

    Responsibilities:
    - Combine system instructions (from config)
    - Insert dataset statistics
    - Insert the user's question
    - Produce a clean, deterministic prompt string

    This step is intentionally simple and deterministic so it can be
    easily unit-tested in isolation.
    """

    def invoke(self, input: PromptBuilderInput) -> PromptBuilderOutput:
        # Log the incoming question for traceability
        logger.info("PromptBuilder invoked with question='%s'", input.question)

        # Sanity check — statistics must exist
        if not input.stats:
            raise ValueError("PromptBuilder received empty statistics.")

        # Format statistics section
        stats_section = f"Dataset statistics:\n{input.stats}\n"

        # Build the final prompt
        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"{stats_section}\n"
            f"User question: {input.question}\n"
            f"Answer in clear and concise Swedish."
        )

        return PromptBuilderOutput(prompt=full_prompt)
