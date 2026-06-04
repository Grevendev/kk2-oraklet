# app/semantic.py
import pandas as pd

def calculate_column_semantic_type(series: pd.Series) -> str:
    """
    Returnerar en semantisk profil för en kolumn baserat på dess faktiska innehåll.
    Särskiljer numeriska strängar, kategoriska strängar, diskreta och kontinuerliga floats.
    """
    clean_series = series.dropna()
    if clean_series.empty:
        return "empty"

    dtype_str = str(clean_series.dtype)
    
    # Inspektera object, string och kategorier på djupet
    if dtype_str == "object" or "string" in dtype_str or "category" in dtype_str:
        def is_numeric_str(val):
            try:
                float(str(val).strip())
                return True
            except (ValueError, TypeError):
                return False
                
        if all(is_numeric_str(x) for x in clean_series):
            return "numeric_string"
        return "categorical_string"

    # Regel för floats (t.ex. 1.2 vs 1.0)
    if "float" in dtype_str:
        if all(float(x).is_integer() for x in clean_series):
            return "discrete_float"
        return "continuous_float"

    return dtype_str