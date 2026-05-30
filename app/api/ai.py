from app.data import data_service

import hashlib
from typing import Dict, Tuple, AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.state import state
from app.config import logger
from app.errors import ValidationError, UserError, SystemError
from app.schemas import AIResponse

from app.chain.steps import PromptBuilderInput  # <-- VIKTIGT

import os
TESTING = os.getenv("TESTING") == "1"


# ---------------------------------------------------------------------------
# AI pipeline stub (krävs av tester)
# ---------------------------------------------------------------------------
class AIPipelineStub:
    def run(self, question: str):
        raise NotImplementedError("Pipeline not implemented")

    async def stream(self, question: str):
        raise NotImplementedError("Pipeline not implemented")


pipeline = AIPipelineStub()
# ---------------------------------------------------------------------------


router = APIRouter(prefix="/ai", tags=["AI"])

if not TESTING:
    limiter = Limiter(key_func=get_remote_address)
else:
    class NoOpLimiter:
        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    limiter = NoOpLimiter()


_cache_store: Dict[Tuple[str, str], Dict[str, object]] = {}

AI_RATE_LIMIT = "10/minute"


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

    cached = _cache_store.get(cache_key)
    if cached is not None:
        etag = cached["etag"]

        if client_etag == etag:
            return Response(status_code=304)

        response = JSONResponse(content=cached["body"].model_dump())
        response.headers["ETag"] = etag
        return response

    # ----------------------------------------------------------------------
    # KORREKT pipeline-anrop (fungerar för både OrakletPipeline och Orchestrator)
    # ----------------------------------------------------------------------
    try:
        result = await run_in_threadpool(pipeline.run, payload.question, state)

    except TypeError:
        pb_input = PromptBuilderInput(
            question=payload.question,
            stats=state.stats
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

    # ----------------------------------------------------------------------

    result_dict = {
        "question": payload.question,   # <-- TESTKRAV
        "answer": result.answer,
        "reasoning": result.reasoning,
        "stats_used": result.stats_used,
    }

    etag_payload = {
        **result_dict,
        "dataset_fingerprint": dataset_fp,
    }
    etag = _compute_etag(etag_payload)

    validated = AIResponse(**result_dict)

    _cache_store[cache_key] = {"body": validated, "etag": etag}

    response = JSONResponse(content=validated.model_dump())
    response.headers["ETag"] = etag
    return response


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

    async def streamer() -> AsyncGenerator[bytes, None]:

        if cached is not None:
            answer = cached["body"].answer
            for i in range(0, len(answer), 256):
                yield answer[i:i+256].encode("utf-8")
            return

        try:
            result = await run_in_threadpool(pipeline.run, payload.question, state)

        except TypeError:
            pb_input = PromptBuilderInput(
                question=payload.question,
                stats=state.stats
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

        result_dict = {
            "question": payload.question,   # <-- TESTKRAV
            "answer": result.answer,
            "reasoning": result.reasoning,
            "stats_used": result.stats_used,
        }

        etag_payload = {
            **result_dict,
            "dataset_fingerprint": dataset_fp,
        }
        etag = _compute_etag(etag_payload)

        validated = AIResponse(**result_dict)
        _cache_store[cache_key] = {"body": validated, "etag": etag}

        answer = validated.answer
        for i in range(0, len(answer), 256):
            yield answer[i:i+256].encode("utf-8")

    return StreamingResponse(streamer(), media_type="text/plain")
