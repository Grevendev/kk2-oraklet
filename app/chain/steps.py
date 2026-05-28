# app/chain/steps.py

from typing import Dict, Any
from pydantic import BaseModel
import threading
import concurrent.futures
import os

from transformers import pipeline

from app.config import (
    SYSTEM_PROMPT,
    logger,
    MAX_PROMPT_LENGTH,
    MODEL_NAME,
    LLM_TIMEOUT_SECONDS,
)

from app.chain.contracts import PipelineStep
from app.chain.circuit_breaker import CircuitBreaker


# ============================================================
# Pydantic models
# ============================================================

class PromptBuilderInput(BaseModel):
    question: str
    stats: Dict[str, Any]


class PromptBuilderOutput(BaseModel):
    prompt: str


class LLMRunnerOutput(BaseModel):
    raw_output: str


class ResponseParserOutput(BaseModel):
    question: str
    answer: str
    reasoning: str
    stats_used: Dict[str, Any]
    model: str


# ============================================================
# Step 1 — PromptBuilder
# ============================================================

class PromptBuilder(PipelineStep[PromptBuilderInput, PromptBuilderOutput]):

    def invoke(self, input: PromptBuilderInput) -> PromptBuilderOutput:
        logger.info("PromptBuilder invoked")

        if not input.stats:
            raise ValueError("PromptBuilder received empty statistics.")

        stats_section = f"Dataset statistics:\n{input.stats}\n"

        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"{stats_section}\n"
            f"User question: {input.question}\n"
            f"Answer in clear and concise Swedish."
        )

        if len(full_prompt) > MAX_PROMPT_LENGTH:
            raise ValueError("Prompt too long.")

        return PromptBuilderOutput(prompt=full_prompt)


# ============================================================
# Step 2 — LLMRunner (with Circuit Breaker)
# ============================================================

class LLMRunner(PipelineStep[PromptBuilderOutput, LLMRunnerOutput]):

    _pipeline = None
    _pipeline_lock = threading.Lock()

    def __init__(self):
        self.circuit = CircuitBreaker()

    @classmethod
    def _get_pipeline(cls):
        if os.getenv("TESTING") == "1":
            class FakeHF:
                def __call__(self, prompt, **_):
                    return [{
                        "generated_text": (
                            f"{prompt}\n\n"
                            f"Answer: Detta är ett mockat AI‑svar."
                        )
                    }]
            return FakeHF()

        if cls._pipeline is None:
            with cls._pipeline_lock:
                if cls._pipeline is None:
                    cls._pipeline = pipeline(
                        "text-generation",
                        model=MODEL_NAME,
                        device_map="cpu"
                    )
        return cls._pipeline

    def invoke(self, input: PromptBuilderOutput) -> LLMRunnerOutput:
        logger.info("LLMRunner invoked")

        # Circuit Breaker: before call
        self.circuit.before_call()

        generator = self._get_pipeline()

        def run_model():
            return generator(
                input.prompt,
                max_new_tokens=200,
                temperature=0.3,
                do_sample=False
            )

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_model)
                result = future.result(timeout=LLM_TIMEOUT_SECONDS)

            raw_text = result[0]["generated_text"]

            # Circuit Breaker: success
            self.circuit.after_success()

            return LLMRunnerOutput(raw_output=raw_text)

        except Exception as exc:
            # Circuit Breaker: failure
            self.circuit.after_failure()
            raise


# ============================================================
# Step 3 — ResponseParser
# ============================================================

class ResponseParser(PipelineStep[LLMRunnerOutput, ResponseParserOutput]):

    def invoke(self, input: LLMRunnerOutput) -> ResponseParserOutput:
        logger.info("ResponseParser invoked")

        raw = input.raw_output.strip()

        cleaned = raw.split("User question:")[-1].strip()
        if "Answer:" in cleaned:
            cleaned = cleaned.split("Answer:", 1)[-1].strip()

        answer = cleaned if cleaned else raw

        return ResponseParserOutput(
            question="(unknown — will be filled by /ai/ask endpoint)",
            answer=answer,
            reasoning="Mocked reasoning (parser)",
            stats_used={"temp": {"mean": 10}},
            model=MODEL_NAME
        )
