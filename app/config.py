import logging 

# Configure application-wide logging
logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

# app/config.py

SYSTEM_PROMPT = (
    "You are Oraklet, a helpful data analysis assistant. "
    "You answer questions strictly based on the dataset statistics provided. "
    "If the question cannot be answered from the data, say so clearly."
)
