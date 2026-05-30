# app/config.py
#
# Central configuration for the Oraklet application.
# Contains:
#   - application-wide logging
#   - system prompt for the LLM
#   - model configuration
#   - timeout settings for LLM calls
#
# This file ensures that all chain steps share the same configuration.


import logging


# ============================================================
# Logging configuration
# ============================================================

# Configure application-wide logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Create a named logger for the application
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

# HuggingFace model used by the LLMRunner
MODEL_NAME = "HuggingFaceTB/SmolLM2-135M-Instruct"


# ============================================================
# Timeout configuration for LLM calls
# ============================================================

# Maximum allowed time (in seconds) for the model to generate a response
LLM_TIMEOUT_SECONDS = 20


# Maximum allowed prompt length (characters)
MAX_PROMPT_LENGTH = 8000


STATS_CACHE_TTL_SECONDS = 60  # eller den TTL du använder i din cache
