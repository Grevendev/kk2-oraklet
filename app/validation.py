# app/validation.py
from app.errors import ValidationError
import pandas as pd

def run_data_validation(df: pd.DataFrame):
    """
    Kör alla tekniska valideringar på ett DataFrame.
    Om något är fel, kasta ValidationError.
    """
    for col in df.columns:
        # Check 1: Namnvalidering
        col_str = str(col).strip()
        if col is None or col_str in ["None", "", "nan", "null"] or "unnamed" in col_str.lower():
            raise ValidationError("Invalid file format: Column name cannot be null or empty.")
    
    # Här kan du enkelt lägga till fler regler i framtiden utan att ändra main.py