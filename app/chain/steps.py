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

# Ändra Pydantic-modellen så den kan hantera strukturerad data
class PromptBuilderOutput(BaseModel):
    messages: list  # Ändrat från prompt: str


class PromptBuilder(PipelineStep[PromptBuilderInput, PromptBuilderOutput]):

    def _format_stats(self, stats: Dict[str, Any]) -> str:
        """
        Omvandlar rå describe()-JSON till en ren, textbaserad tabell/lista
        som en liten språkmodell lätt kan förstå och resonera kring.
        """
        lines = []
        for column, metrics in stats.items():
            lines.append(f"Kolumn: {column}")
            if isinstance(metrics, dict):
                for metric_name, value in metrics.items():
                    # Avrunda flyttal för att göra det mer läsbart för modellen
                    if isinstance(value, float):
                        value = round(value, 2)
                    lines.append(f"  - {metric_name}: {value}")
            else:
                lines.append(f"  - {metrics}")
        return "\n".join(lines)

    def invoke(self, input: PromptBuilderInput) -> PromptBuilderOutput:
        logger.info("PromptBuilder invoked")

        if not input.stats:
            raise ValueError("PromptBuilder received empty statistics.")

        # Transformera statistiken till ren text
        readable_stats = self._format_stats(input.stats)

        # Skapa meddelandestrukturen med den tvättade statistiken
        messages = [
            {
                "role": "system",
                "content": (
                    "Du är en dataanalytiker som bara svarar på svenska.\n"
                    "Analysera statistiken nedan och sammanfatta kort vad du ser.\n"
                    f"{readable_stats}"
                )
            },
            {
                "role": "user",
                "content": "Berätta kort om datasetet på svenska."
            }
        ]

        return PromptBuilderOutput(messages=messages)


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

    async def _run_model_async(self, messages: list):
        generator = self._get_pipeline()
        tokenizer = generator.tokenizer

        # Generera basprompten utan den sista automatiska generation-taggen
        raw_prompt = tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        # Tvinga modellen att starta sitt svar med en svensk mening!
        prompt = f"{raw_prompt}Baserat på statistiken kan vi se att datasetet innehåller"

        def run_sync():
            return generator(
                prompt,
                max_new_tokens=60, # Håll det kort och koncist
                do_sample=True,     
                temperature=0.2,     # Lägre temperatur = mer strikt faktabaserad
                top_k=30,            
                top_p=0.85,          
                repetition_penalty=1.3, 
                eos_token_id=tokenizer.eos_token_id,
            )

        with anyio.move_on_after(LLM_TIMEOUT_SECONDS) as scope:
            result = await anyio.to_thread.run_sync(run_sync)

        if scope.cancel_called:
            raise TimeoutError("LLM timed out")

        return result

    # Kom ihåg att uppdatera anropet i din `invoke`-metod i LLMRunner:
    # result = anyio.from_thread.run(self._run_model_async, input.messages)

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
                # ÄNDRAT: Skicka input.messages istället för input.prompt
                result = anyio.from_thread.run(self._run_model_async, input.messages)
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
                    # ÄNDRAT: Skicka input.messages även till fallbacken
                    fallback = anyio.from_thread.run(self._run_fallback_async, input.messages)
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
        # Snygga till så att den påbörjade meningen följer med i svaret
        if not answer.startswith("Baserat på"):
            answer = f"Baserat på statistiken kan vi se att datasetet innehåller {answer}"

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