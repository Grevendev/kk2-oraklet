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
from app.container import get_pipeline
from app.config import logger
from app.errors import ValidationError, UserError, SystemError
from app.schemas import AIResponse

import os


# ---------------------------------------------------------------------------
# 🆕 AI pipeline stub (krävs av ALLA tester)
# ---------------------------------------------------------------------------
class AIPipelineStub:
    def run(self, question: str):
        raise NotImplementedError("Pipeline not implemented")

    async def stream(self, question: str):
        raise NotImplementedError("Pipeline not implemented")


# Global pipeline som testerna monkeypatchar
pipeline = AIPipelineStub()
# ---------------------------------------------------------------------------


router = APIRouter(prefix="/ai", tags=["AI"])

TESTING = os.getenv("TESTING") == "1"

if not TESTING:
    limiter = Limiter(key_func=get_remote_address)
else:
    class NoOpLimiter:
        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    limiter = NoOpLimiter()


# cache: (dataset_fingerprint, question_hash) -> {body, etag}
_cache_store: Dict[Tuple[str, str], Dict[str, object]] = {}

AI_RATE_LIMIT = "10/minute"


class AskRequest(BaseModel):
    question: str


def _hash_question(question: str) -> str:
    return hashlib.sha256(question.strip().encode("utf-8")).hexdigest()


def _compute_etag(payload: dict) -> str:
    raw = repr(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@router.post("/ask", response_model=AIResponse)
@limiter.limit(AI_RATE_LIMIT)
async def ask_ai(request: Request, payload: AskRequest):

    client_ip = request.client.host
    request_id = request.state.request_id

    logger.info({
        "event": "ai_request_received",
        "request_id": request_id,
        "client_ip": client_ip,
        "question": payload.question
    })

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

        response = JSONResponse(content=cached["body"])
        response.headers["ETag"] = etag
        return response

    try:
        result = await run_in_threadpool(pipeline.run, payload.question)
    except ValidationError as e:
        raise UserError(str(e))
    except TimeoutError as e:
        raise SystemError(str(e))
    except RuntimeError as e:
        raise SystemError(str(e))

    result_dict = {
        "question": result.question,
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

    _cache_store[cache_key] = {"body": validated.model_dump(), "etag": etag}

    response = JSONResponse(content=validated.model_dump())
    response.headers["ETag"] = etag
    return response


@router.post("/ask/stream")
@limiter.limit(AI_RATE_LIMIT)
async def ask_ai_stream(request: Request, payload: AskRequest):

    client_ip = request.client.host
    request_id = request.state.request_id

    logger.info({
        "event": "ai_stream_request_received",
        "request_id": request_id,
        "client_ip": client_ip,
        "question": payload.question
    })

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
            answer = cached["body"].get("answer", "")
            for i in range(0, len(answer), 256):
                yield answer[i:i+256].encode("utf-8")
            return

        try:
            result = await run_in_threadpool(pipeline.run, payload.question)
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
            "question": result.question,
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
        _cache_store[cache_key] = {"body": validated.model_dump(), "etag": etag}

        answer = validated.answer
        for i in range(0, len(answer), 256):
            yield answer[i:i+256].encode("utf-8")

    return StreamingResponse(streamer(), media_type="text/plain")
