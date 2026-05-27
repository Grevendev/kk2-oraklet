# app/api/ai.py

import time
import hashlib
from typing import Dict, Tuple

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.state import state
from app.chain.pipeline import pipeline
from app.config import logger

# Justera denna import till din faktiska auth-funktion
from app.auth import get_current_user  # t.ex. returnerar User-objekt eller liknande


router = APIRouter(prefix="/ai", tags=["AI"])


# ------------------------------------------------------------
# In-memory rate limiting & caching (per process)
# ------------------------------------------------------------

# session_id -> list of timestamps (seconds)
_rate_limit_window_seconds = 60
_rate_limit_max_requests = 10
_rate_limit_store: Dict[str, list[float]] = {}

# (session_id, question_hash, stats_hash) -> cached response
_cache_store: Dict[Tuple[str, str, str], dict] = {}


# ------------------------------------------------------------
# Request model
# ------------------------------------------------------------

class AskRequest(BaseModel):
    question: str


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _hash_stats(stats) -> str:
    """
    Create a stable hash of the current stats object.
    This ensures cache invalidation when dataset changes.
    """
    raw = repr(stats).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _hash_question(question: str) -> str:
    return hashlib.sha256(question.strip().encode("utf-8")).hexdigest()


def _enforce_rate_limit(session_id: str):
    """
    Simple in-memory rate limiting per session.
    Allows _rate_limit_max_requests per _rate_limit_window_seconds.
    """
    now = time.time()
    window_start = now - _rate_limit_window_seconds

    timestamps = _rate_limit_store.get(session_id, [])
    # behåll bara de som ligger inom fönstret
    timestamps = [t for t in timestamps if t >= window_start]

    if len(timestamps) >= _rate_limit_max_requests:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded for /ai/ask. Try again later."
        )

    timestamps.append(now)
    _rate_limit_store[session_id] = timestamps


# ------------------------------------------------------------
# /ai/ask endpoint
# ------------------------------------------------------------

@router.post("/ask")
def ask_ai(
    request: AskRequest,
    user=Depends(get_current_user),  # auth
):
    """
    Executes the full Oraklet pipeline with:
    - Auth (session-based)
    - Rate limiting per session
    - Caching per (session, question, stats)
    """

    # 0. Validate question
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    # 1. Ensure stats exist
    if state.stats is None:
        raise HTTPException(
            status_code=400,
            detail="No dataset uploaded. Upload data before asking questions."
        )

    # 2. Identify session (justera efter din auth-modell)
    #    Här antar vi att user har ett unikt id eller session_id
    session_id = str(getattr(user, "id", "anonymous"))

    # 3. Enforce rate limiting
    _enforce_rate_limit(session_id)

    # 4. Build cache key
    stats_hash = _hash_stats(state.stats)
    question_hash = _hash_question(request.question)
    cache_key = (session_id, question_hash, stats_hash)

    # 5. Check cache
    if cache_key in _cache_store:
        logger.info("Cache hit for /ai/ask (session=%s)", session_id)
        return _cache_store[cache_key]

    logger.info("Cache miss for /ai/ask (session=%s)", session_id)

    # 6. Run pipeline with robust error mapping
    try:
        result = pipeline.run(request.question)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 7. Convert to dict for caching/response
    result_dict = result.model_dump()

    # 8. Store in cache
    _cache_store[cache_key] = result_dict

    return result_dict
