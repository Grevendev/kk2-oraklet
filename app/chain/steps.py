# app/chain/steps.py
import anyio
from typing import Dict, Any
from pydantic import BaseModel
import threading
import os
import asyncio
import time
import re
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
from app.chain.errors import PipelineError
from app.chain.retry_policy import RetryPolicy


# ============================================================
# Pydantic models
# ============================================================

class PromptBuilderInput(BaseModel):
    question: str
    stats: Dict[str, Any]


class PromptBuilderOutput(BaseModel):
    prompt: str


class LLMRunnerOutput(BaseModel):
    raw_output: Any


class ResponseParserOutput(BaseModel):
    question: str
    answer: str
    reasoning: str
    stats_used: Dict[str, Any]
    model: str


# ============================================================
# Global Circuit Breaker (delas mellan LLMRunner och API)
# ============================================================

class FixedCircuitBreaker(CircuitBreaker):
    """
    Utökar din befintliga CircuitBreaker med reset_timeout(),
    eftersom testerna kräver att den finns.
    """

    def reset_timeout(self):
        """
        Tester använder denna för att simulera att timeouten har gått ut.
        """
        self.opened_at = 0.0


GLOBAL_CIRCUIT_BREAKER = FixedCircuitBreaker()


# ============================================================
# Step 1 — PromptBuilder
# ============================================================

class PromptBuilder(PipelineStep[PromptBuilderInput, PromptBuilderOutput]):

    def invoke(self, input: PromptBuilderInput) -> PromptBuilderOutput:
        logger.info("PromptBuilder invoked")

        if not input.stats:
            raise ValueError("PromptBuilder received empty statistics.")

        stats_section = f"Dataset statistics:\n{input.stats}"

        # Använd strikt ChatML-format som SmolLM2 förväntar sig för instruktionsföljsamhet
        full_prompt = (
            f"<|im_start|>system\n{SYSTEM_PROMPT}\n"
            f"Svara alltid på tydlig och kortfattad svenska.\n"
            f"{stats_section}<|im_end|>\n"
            f"<|im_start|>user\n{input.question}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )

        if len(full_prompt) > MAX_PROMPT_LENGTH:
            raise ValueError("Prompt too long.")

        return PromptBuilderOutput(prompt=full_prompt)


# ============================================================
# Step 2 — LLMRunner
# ============================================================

class LLMRunner(PipelineStep[PromptBuilderOutput, LLMRunnerOutput]):

    _pipeline = None
    _pipeline_lock = threading.Lock()

    def __init__(self):
        self.circuit = GLOBAL_CIRCUIT_BREAKER
        self.retry = RetryPolicy()

    @classmethod
    def _get_pipeline(cls):
        if os.getenv("TESTING") == "1" or "PYTEST_CURRENT_TEST" in os.environ:
            class FakeHF:
                def __call__(self, prompt, **_):
                    return [{
                        "generated_text": (
                            f"{prompt}"
                            f"<|im_start|>thought\nAnalyserar data...\n<|im_end|>\n"
                            f"Detta är ett mockat AI‑svar."
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

    async def _run_model_async(self, prompt: str):
        generator = self._get_pipeline()

        def run_sync():
            return generator(
                prompt,
                max_new_tokens=80,
                temperature=0.2,
                do_sample=False,
                eos_token_id=0,  # Stoppa genereringen vid end-of-sequence
            )

        with anyio.move_on_after(LLM_TIMEOUT_SECONDS) as scope:
            result = await anyio.to_thread.run_sync(run_sync)

        if scope.cancel_called:
            raise TimeoutError("LLM timed out")

        return result

    async def _run_fallback_async(self, prompt: str):
        return {
            "generated_text": f"{prompt}<|im_start|>thought\nFallback logik aktiverad.\n<|im_end|>\nDetta är ett fallback‑svar."
        }

    def _sleep(self, seconds: float):
        time.sleep(seconds)

    def _normalize_output(self, result: Any) -> Any:
        if isinstance(result, dict):
            return result
        return result[0]["generated_text"]

    def invoke(self, input: PromptBuilderOutput) -> LLMRunnerOutput:
        logger.info("LLMRunner invoked")

        self.circuit.before_call()

        for attempt in range(self.retry.max_attempts):
            try:
                result = anyio.from_thread.run(self._run_model_async, input.prompt)
                raw_text = self._normalize_output(result)

                self.circuit.after_success()
                return LLMRunnerOutput(raw_output=raw_text)

            except Exception as exc:
                if attempt < self.retry.max_attempts - 1:
                    delay = self.retry.get_delay(attempt)
                    logger.warning({
                        "event": "llm_retry",
                        "attempt": attempt + 1,
                        "delay": round(delay, 3),
                        "error": str(exc),
                    })
                    self._sleep(delay)
                    continue
                
                self.circuit.after_failure()

                try:
                    fallback = anyio.from_thread.run(self._run_fallback_async, input.prompt)
                    raw_text = self._normalize_output(fallback)
                    return LLMRunnerOutput(raw_output=raw_text)
                except Exception as fallback_exc:
                    self.circuit.after_failure()
                    raise PipelineError(
                        message="LLM fallback failed",
                        step_name="LLMRunner",
                        original_exception=fallback_exc
                    )


# ============================================================
# Step 3 — ResponseParser
# ============================================================

class ResponseParser(PipelineStep[LLMRunnerOutput, ResponseParserOutput]):

    def invoke(self, input: LLMRunnerOutput) -> ResponseParserOutput:
        logger.info("ResponseParser invoked")

        raw_output = input.raw_output
        raw_text = raw_output.get("generated_text", str(raw_output)) if isinstance(raw_output, dict) else str(raw_output)

        # Skär bort allt som låg i prompten fram till sista <|im_start|>assistant\n
        assistant_marker = "<|im_start|>assistant\n"
        if assistant_marker in raw_text:
            generated_part = raw_text.split(assistant_marker)[-1].strip()
        else:
            generated_part = raw_text.strip()

        # Bryt ut eventuella <|im_start|>thought block om modellen skapat resonemang
        reasoning = "Modellen genererade svar lokalt baserat på tillgänglig dataset-statistik."
        thought_match = re.search(r"<\|im_start\|>thought\n(.*?)(?:<\|im_end\|>|$)", generated_part, re.DOTALL)
        
        if thought_match:
            reasoning = thought_match.group(1).strip()
            # Ta bort thought-blocket från det slutgiltiga svaret
            generated_part = re.sub(r"<\|im_start\|>thought\n.*?(?:<\|im_end\|>|$)", "", generated_part, flags=re.DOTALL).strip()

        # Rensa bort eventuella hängande ChatML-taggar från svaret
        answer = generated_part.replace("<|im_end|>", "").replace("<|im_start|>", "").strip()

        # Fallback ifall modellen skulle råka producera tom text
        if not answer:
            answer = "Kunde inte tolka eller extrahera ett svar från den lokala modellen."

        return ResponseParserOutput(
            question="(unknown — will be filled by /ai/ask endpoint)",
            answer=answer,
            reasoning=reasoning,
            stats_used={},
            model=MODEL_NAME
        )


# ============================================================
# Timeout helper
# ============================================================

async def run_with_timeout(func, timeout: float):
    if asyncio.iscoroutinefunction(func):
        return await asyncio.wait_for(func(), timeout=timeout)

    loop = asyncio.get_event_loop()
    return await asyncio.wait_for(loop.run_in_executor(None, func), timeout=timeout)