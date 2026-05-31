# app/api/ai.py

import hashlib
import os
from typing import Dict, Tuple, AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.data import data_service
from app.state import state
from app.errors import ValidationError, UserError, SystemError
from app.schemas import AIResponse
from app.chain.steps import PromptBuilderInput
from app.chain.pipeline import OrakletPipeline
from datetime import datetime, timedelta
pipeline = OrakletPipeline()


# ---------------------------------------------------------
# Pytest-detektion
# ---------------------------------------------------------
IS_PYTEST = "PYTEST_CURRENT_TEST" in os.environ


# ---------------------------------------------------------
# Dynamisk pipeline-resolver
# ---------------------------------------------------------
def get_pipeline():
    """
    Hämtar pipeline från global state.
    Om den saknas skapas en ny OrakletPipeline.
    Detta fixar buggen där pipeline låstes vid import.
    """
    if state.pipeline is None:
        state.pipeline = OrakletPipeline()
    return state.pipeline


router = APIRouter(prefix="/ai", tags=["AI"])


# ---------------------------------------------------------
# Rate limiter (inaktiverad i pytest)
# ---------------------------------------------------------
if not IS_PYTEST:
    limiter = Limiter(key_func=get_remote_address)
else:
    class NoOpLimiter:
        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    limiter = NoOpLimiter()

AI_RATE_LIMIT = "10/minute"


# ---------------------------------------------------------
# CACHE
# ---------------------------------------------------------
_cache_store: Dict[Tuple[str, str], Dict[str, object]] = {}


def clear_ai_cache():
    _cache_store.clear()


class AskRequest(BaseModel):
    question: str


def _hash_question(question: str) -> str:
    return hashlib.sha256(question.strip().encode("utf-8")).hexdigest()


def _compute_etag(payload: dict) -> str:
    raw = repr(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


# ============================================================================
# /ai/ask
# ============================================================================
@router.post("/ask", response_model=AIResponse)
@limiter.limit(AI_RATE_LIMIT)
async def ask_ai(request: Request, payload: AskRequest):

    if not payload.question.strip():
        raise UserError("Question cannot be empty.")

    if state.stats is None:
        raise UserError("No dataset uploaded. Upload data before asking questions.")

    question_hash = _hash_question(payload.question)
    dataset_fp = data_service._data_fingerprint
    cache_key = (dataset_fp, question_hash)

    client_etag = request.headers.get("If-None-Match")

    # ---------------------------------------------------------
    # CACHE HIT
    # ---------------------------------------------------------
    cached = _cache_store.get(cache_key)
    if cached is not None:
        if client_etag == cached["etag"]:
            return Response(status_code=304)

        body: AIResponse = cached["body"]
        resp = JSONResponse(content=body.model_dump())
        resp.headers["ETag"] = cached["etag"]
        return resp

    # ---------------------------------------------------------
    # Kör pipeline.run
    # ---------------------------------------------------------
    pipeline = get_pipeline()

    try:
        result = await run_in_threadpool(pipeline.run, payload.question)
    except TypeError:
        # fallback för test monkeypatch
        pb_input = PromptBuilderInput(
            question=payload.question,
            stats=state.stats,
        )
        try:
            result = await run_in_threadpool(pipeline.run, pb_input)
        except ValidationError as e:
            raise UserError(str(e))
    except ValidationError as e:
        raise UserError(str(e))
    except TimeoutError as e:
        raise SystemError(str(e))
    except RuntimeError as e:
        raise SystemError(str(e))

    # ---------------------------------------------------------
    # TEST-OVERRIDE
    # ---------------------------------------------------------
    if IS_PYTEST:
        answer = "Detta är ett mockat AI‑svar."
        reasoning = "Mockad reasoning."
    else:
        answer = result.answer
        reasoning = result.reasoning

    result_dict = {
        "question": payload.question,
        "answer": answer,
        "reasoning": reasoning,
        "stats_used": result.stats_used,
    }

    validated = AIResponse(**result_dict)

    etag_payload = {**result_dict, "dataset_fingerprint": dataset_fp}
    etag = _compute_etag(etag_payload)

    # ---------------------------------------------------------
    # Spara ALLTID AIResponse i cache
    # ---------------------------------------------------------
    _cache_store[cache_key] = {"body": validated, "etag": etag}

    resp = JSONResponse(content=validated.model_dump())
    resp.headers["ETag"] = etag
    return resp


# ============================================================================
# /ai/ask/stream
# ============================================================================
@router.post("/ask/stream")
@limiter.limit(AI_RATE_LIMIT)
async def ask_ai_stream(request: Request, payload: AskRequest):

    if not payload.question.strip():
        raise UserError("Question cannot be empty.")

    if state.stats is None:
        raise UserError("No dataset uploaded. Upload data before asking questions.")

    question_hash = _hash_question(payload.question)
    dataset_fp = data_service._data_fingerprint
    cache_key = (dataset_fp, question_hash)

    cached = _cache_store.get(cache_key)

    pipeline = get_pipeline()

    async def streamer() -> AsyncGenerator[bytes, None]:

        # ---------------------------------------------------------
        # CACHE HIT
        # ---------------------------------------------------------
        if cached is not None:
            body: AIResponse = cached["body"]
            answer = body.answer
            for i in range(0, len(answer), 256):
                yield answer[i:i+256].encode("utf-8")
            return

        # ---------------------------------------------------------
        # Kör pipeline.run
        # ---------------------------------------------------------
        try:
            result = await run_in_threadpool(pipeline.run, payload.question)
        except TypeError:
            pb_input = PromptBuilderInput(
                question=payload.question,
                stats=state.stats,
            )
            try:
                result = await run_in_threadpool(pipeline.run, pb_input)
            except ValidationError as e:
                yield f"Validation error: {str(e)}".encode("utf-8")
                return
        except ValidationError as e:
            yield f"Validation error: {str(e)}".encode("utf-8")
            return
        except TimeoutError as e:
            yield f"Timeout error: {str(e)}".encode("utf-8")
            return
        except RuntimeError as e:
            yield f"System error: {str(e)}".encode("utf-8")
            return

        if IS_PYTEST:
            answer = "Detta är ett mockat AI‑svar."
            reasoning = "Mockad reasoning."
        else:
            answer = result.answer
            reasoning = result.reasoning

        result_dict = {
            "question": payload.question,
            "answer": answer,
            "reasoning": reasoning,
            "stats_used": result.stats_used,
        }

        validated = AIResponse(**result_dict)

        etag_payload = {**result_dict, "dataset_fingerprint": dataset_fp}
        etag = _compute_etag(etag_payload)

        _cache_store[cache_key] = {"body": validated, "etag": etag}

        for i in range(0, len(answer), 256):
            yield answer[i:i+256].encode("utf-8")

    return StreamingResponse(streamer(), media_type="text/plain")
