# app/chain/steps.py

from pydantic import BaseModel
from typing import Dict, Any
from app.chain.runnable import Runnable  # Din Runnable-bas från lektionen


# ---------------------------------------------------------
# Pydantic-modeller för in- och utdata
# ---------------------------------------------------------

class PromptBuilderInput(BaseModel):
    """Input to the PromptBuilder step."""
    question: str
    stats: Dict[str, Any]


class PromptBuilderOutput(BaseModel):
    """Output from the PromptBuilder step."""
    prompt: str


# ---------------------------------------------------------
# Själva steget i kedjan
# ---------------------------------------------------------

class PromptBuilder(Runnable[PromptBuilderInput, PromptBuilderOutput]):
    """
    Builds a structured prompt for the LLM.
    This step combines:
    - system instructions
    - dataset statistics
    - the user's natural-language question
    """

    def invoke(self, input: PromptBuilderInput) -> PromptBuilderOutput:
        # Systeminstruktioner som ramar in modellens roll
        system_instructions = (
            "You are Oraklet, a helpful data analysis assistant. "
            "You answer questions strictly based on the dataset statistics provided. "
            "If the question cannot be answered from the data, say so clearly."
        )

        # Formatera statistikdelen
        stats_section = f"Dataset statistics:\n{input.stats}\n"

        # Bygg prompten
        full_prompt = (
            f"{system_instructions}\n\n"
            f"{stats_section}\n"
            f"User question: {input.question}\n"
            f"Answer in clear and concise Swedish."
        )

        return PromptBuilderOutput(prompt=full_prompt)
