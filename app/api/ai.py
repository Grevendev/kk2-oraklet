# app/api/ai.py

import hashlib
from typing import Dict, Tuple, AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.state import state
from app.chain.pipeline import pipeline
from app.config import logger
from app.errors import ValidationError, UserError, SystemError
from app.schemas import AIResponse


router = APIRouter(prefix="/ai", tags=["AI"])

# SlowAPI limiter (same style as main.py)
limiter = Limiter(key_func=get_remote_address)

# Cache: (ip, question_hash, stats_hash) -> {"body": dict, "etag": str}
_cache_store: Dict[Tuple[str, str, str], Dict[str, object]] = {}

# Rate limit for AI
AI_RATE_LIMIT = "10/minute"


class AskRequest(BaseModel):
    question: str


def _hash_stats(stats) -> str:
    raw = repr(stats).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _hash_question(question: str) -> str:
    return hashlib.sha256(question.strip().encode("utf-8")).hexdigest()


def _compute_etag(payload: dict) -> str:
    raw = repr(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


# ------------------------------------------------------------
# /ai/ask – JSON + ETag + caching + async pipeline
# ------------------------------------------------------------

@router.post("/ask", response_model=AIResponse)
@limiter.limit(AI_RATE_LIMIT)
async def ask_ai(request: Request, payload: AskRequest):
    """
    AI endpoint with:
    - IP-based rate limiting (SlowAPI)
    - IP-based in-memory caching
    - ETag support (304 Not Modified)
    - Async model execution via threadpool
    """

    client_ip = request.client.host
    request_id = request.state.request_id

    logger.info({
        "event": "ai_request_received",
        "request_id": request_id,
        "client_ip": client_ip,
        "question": payload.question
    })

    # 1. Validate question
    if not payload.question.strip():
        raise UserError("Question cannot be empty.")

    # 2. Ensure dataset exists
    if state.stats is None:
        raise UserError("No dataset uploaded. Upload data before asking questions.")

    # 3. Build cache key
    stats_hash = _hash_stats(state.stats)
    question_hash = _hash_question(payload.question)
    cache_key = (client_ip, question_hash, stats_hash)

    client_etag = request.headers.get("If-None-Match")

    # 4. Cache lookup + ETag check
    cached = _cache_store.get(cache_key)
    if cached is not None:
        etag = cached["etag"]

        if client_etag == etag:
            logger.info({
                "event": "ai_not_modified",
                "request_id": request_id,
                "client_ip": client_ip,
                "etag": etag
            })
            return Response(status_code=304)

        logger.info({
            "event": "ai_cache_hit",
            "request_id": request_id,
            "client_ip": client_ip
        })

        response = JSONResponse(content=cached["body"])
        response.headers["ETag"] = etag
        return response

    logger.info({
        "event": "ai_cache_miss",
        "request_id": request_id,
        "client_ip": client_ip
    })

    # 5. Run pipeline asynchronously in threadpool
    try:
        result = await run_in_threadpool(pipeline.run, payload.question)

    except ValidationError as e:
        raise UserError(str(e))

    except TimeoutError as e:
        raise SystemError(str(e))

    except RuntimeError as e:
        raise SystemError(str(e))

    # 6. Convert to dict and compute ETag
    result_dict = result.model_dump()
    etag = _compute_etag(result_dict)

    # Validate against AIResponse schema
    validated = AIResponse(**result_dict)

    # 7. Store in cache
    _cache_store[cache_key] = {"body": validated.model_dump(), "etag": etag}

    logger.info({
        "event": "ai_response_generated",
        "request_id": request_id,
        "client_ip": client_ip,
        "etag": etag
    })

    # 8. Return JSON with ETag
    response = JSONResponse(content=validated.model_dump())
    response.headers["ETag"] = etag
    return response


# ------------------------------------------------------------
# /ai/ask/stream – streaming endpoint (chunked text)
# ------------------------------------------------------------

@router.post("/ask/stream")
@limiter.limit(AI_RATE_LIMIT)
async def ask_ai_stream(request: Request, payload: AskRequest):
    """
    Streaming variant of the AI endpoint.

    Currently:
    - Runs the same pipeline in threadpool
    - Streams the answer in text chunks
    - Ready for real token streaming when switching to a streaming-capable model
    """

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

    stats_hash = _hash_stats(state.stats)
    question_hash = _hash_question(payload.question)
    cache_key = (client_ip, question_hash, stats_hash)

    cached = _cache_store.get(cache_key)

    async def streamer() -> AsyncGenerator[bytes, None]:
        # 1. If cached, stream from cache
        if cached is not None:
            answer = cached["body"].get("answer", "")
            for i in range(0, len(answer), 256):
                yield answer[i:i+256].encode("utf-8")
            return

        # 2. Otherwise, run pipeline and stream result
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

        result_dict = result.model_dump()
        etag = _compute_etag(result_dict)

        # Validate and store
        validated = AIResponse(**result_dict)
        _cache_store[cache_key] = {"body": validated.model_dump(), "etag": etag}

        answer = validated.answer
        for i in range(0, len(answer), 256):
            yield answer[i:i+256].encode("utf-8")

    return StreamingResponse(streamer(), media_type="text/plain")
