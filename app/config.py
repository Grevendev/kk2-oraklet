# app/config.py
#
# Central configuration for the Oraklet application.
# Contains:
#   - application-wide logging
#   - system prompt for the LLM
#   - model configuration
#   - timeout settings for LLM calls
#   - stats cache TTL

import logging

# ============================================================
# Logging configuration
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger("oraklet")

# ============================================================
# System prompt for the LLM
# ============================================================

SYSTEM_PROMPT = (
    "You are Oraklet, a helpful data analysis assistant. "
    "You answer questions strictly based on the dataset statistics provided. "
    "If the question cannot be answered from the data, say so clearly."
)

# ============================================================
# Model configuration
# ============================================================

MODEL_NAME = "HuggingFaceTB/SmolLM2-135M-Instruct"

# ============================================================
# Timeout configuration for LLM calls
# ============================================================

LLM_TIMEOUT_SECONDS = 45
MAX_PROMPT_LENGTH = 8000

# Stats cache TTL (seconds)
STATS_CACHE_TTL_SECONDS = 60
