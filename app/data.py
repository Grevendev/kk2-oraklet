import pandas as pd
from typing import Optional
from app.config import logger


class DataService:
    """Service responsible for storing and validating uploaded datasets."""

    def __init__(self):
        self._df: Optional[pd.DataFrame] = None

    def set_dataset(self, df: pd.DataFrame) -> None:
        """Store the cleaned dataset in memory."""
        logger.info(f"Dataset stored with {df.shape[0]} rows and {df.shape[1]} columns.")
        self._df = df

    def get_dataset(self) -> pd.DataFrame:
        """Return the stored dataset or raise an error if none exists."""
        if self._df is None:
            raise ValueError("No dataset has been uploaded yet.")
        return self._df

    def get_stats(self) -> dict:
        """Return descriptive statistics for the stored dataset."""
        if self._df is None:
            raise ValueError("No dataset has been uploaded yet.")
        return self._df.describe(include="all").to_dict()


# Singleton instance used by the application
data_service = DataService()
