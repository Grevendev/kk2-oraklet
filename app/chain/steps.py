# app/chain/steps.py
#
# This file contains all Runnable steps used in the AI pipeline.
# Implemented:
#   - PromptBuilder (Step 1)
#   - LLMRunner (Step 2)
#
# Placeholder:
#   - ResponseParser (Step 3)


from typing import Dict, Any
from pydantic import BaseModel

from app.chain.runnable import Runnable
from app.config import (
    SYSTEM_PROMPT,
    logger,
    MAX_PROMPT_LENGTH,
    MODEL_NAME,
    LLM_TIMEOUT_SECONDS,
)

# HuggingFace + timeout utilities
from transformers import pipeline
import threading
import concurrent.futures


# ============================================================
# Pydantic models for PromptBuilder input and output
# ============================================================

class PromptBuilderInput(BaseModel):
    """Input model for the PromptBuilder step."""
    question: str
    stats: Dict[str, Any]


class PromptBuilderOutput(BaseModel):
    """Output model for the PromptBuilder step."""
    prompt: str


# ============================================================
# PromptBuilder — Step 1 in the Runnable chain
# ============================================================

class PromptBuilder(Runnable[PromptBuilderInput, PromptBuilderOutput]):
    """
    Builds a structured prompt for the LLM.
    """

    def invoke(self, input: PromptBuilderInput) -> PromptBuilderOutput:
        logger.info("PromptBuilder invoked with question='%s'", input.question)

        if not input.stats:
            raise ValueError("PromptBuilder received empty statistics.")

        stats_section = f"Dataset statistics:\n{input.stats}\n"

        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"{stats_section}\n"
            f"User question: {input.question}\n"
            f"Answer in clear and concise Swedish."
        )

        # Prevent oversized prompts
        if len(full_prompt) > MAX_PROMPT_LENGTH:
            logger.warning(
                "PromptBuilder aborted: prompt length %s exceeds limit %s",
                len(full_prompt),
                MAX_PROMPT_LENGTH
            )
            raise ValueError(
                f"Prompt too long ({len(full_prompt)} chars). "
                f"Maximum allowed is {MAX_PROMPT_LENGTH}."
            )

        return PromptBuilderOutput(prompt=full_prompt)


# ============================================================
# Typed output model for LLMRunner (Step 2)
# ============================================================

class LLMRunnerOutput(BaseModel):
    """Raw text output from the LLM."""
    raw_output: str


# ============================================================
# Typed output model for ResponseParser (Step 3)
# ============================================================

class ResponseParserOutput(BaseModel):
    """Final structured output returned by /ai/ask."""
    question: str
    answer: str
    model: str


# ============================================================
# LLMRunner — Step 2 in the Runnable chain
# ============================================================

class LLMRunner(Runnable[PromptBuilderOutput, LLMRunnerOutput]):
    """
    Executes the LLM using HuggingFace transformers.pipeline.

    Features:
    - Thread-safe lazy loading of the model (loaded once)
    - Timeout protection for model execution
    - Robust error handling
    """

    _pipeline = None
    _pipeline_lock = threading.Lock()

    @classmethod
    def _get_pipeline(cls):
        """
        Lazily initializes the model pipeline.
        Ensures the model is only loaded once, even under concurrency.
        """
        if cls._pipeline is None:
            with cls._pipeline_lock:
                if cls._pipeline is None:
                    logger.info("Loading LLM model: %s", MODEL_NAME)
                    cls._pipeline = pipeline(
                        "text-generation",
                        model=MODEL_NAME,
                        device_map="cpu"
                    )
        return cls._pipeline

    def invoke(self, input: PromptBuilderOutput) -> LLMRunnerOutput:
        logger.info("LLMRunner invoked")

        generator = self._get_pipeline()

        # Function executed inside thread pool for timeout control
        def run_model():
            return generator(
                input.prompt,
                max_new_tokens=200,
                temperature=0.3,
                do_sample=False
            )

        # Timeout wrapper
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_model)

            try:
                result = future.result(timeout=LLM_TIMEOUT_SECONDS)
            except concurrent.futures.TimeoutError:
                logger.error("LLMRunner timed out after %s seconds", LLM_TIMEOUT_SECONDS)
                raise TimeoutError(
                    f"LLM call exceeded timeout of {LLM_TIMEOUT_SECONDS} seconds"
                )
            except Exception as e:
                logger.error("LLMRunner failed: %s", str(e))
                raise RuntimeError(f"LLM execution failed: {str(e)}")

        # Extract raw text
        try:
            raw_text = result[0]["generated_text"]
        except Exception:
            raise RuntimeError("Unexpected LLM output format")

        return LLMRunnerOutput(raw_output=raw_text)


# ============================================================
# Placeholder for ResponseParser — Step 3
# ============================================================

class ResponseParser(Runnable[LLMRunnerOutput, ResponseParserOutput]):
    """
    Placeholder implementation.
    The real implementation will parse the model's raw output.
    """
    def invoke(self, input: LLMRunnerOutput) -> ResponseParserOutput:
        raise NotImplementedError("ResponseParser not implemented yet.")
