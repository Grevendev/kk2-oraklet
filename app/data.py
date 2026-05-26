import pandas as pd
from typing import Optional

# In-memory storage for the uploaded dataset
# This keeps teh dataset available between requests during runtime.
DATAFRAME: Optional[pd.DataFrame] = None

def set_dataset(df: pd.DataFrame) -> None:
  """Store the uploaded dataset in memory."""
  global DATAFRAME
  DATAFRAME = df

def get_dataset() -> pd.DataFrame:
  """Return the stored dataset or raise an error of none exists."""
  if DATAFRAME in None:
    raise ValueError("No dataset has been uploaded yet.")
  return DATAFRAME