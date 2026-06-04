# app/semantic.py
import pandas as pd

def calculate_column_semantic_type(series: pd.Series) -> str:
    """
    Returnerar en semantisk profil/typ för en kolumn baserat på dess innehåll.
    """
    # Ta bort eventuella NaN för säker profilering
    clean_series = series.dropna()
    if clean_series.empty:
        return "empty"
        
    # Regel för strängar/objects (t.ex. "1" vs "ok")
    if clean_series.dtype == "object" or str(clean_series.dtype) == "string":
        # Kolla om alla värden är strikt numeriska (t.ex. "10", "1.2")
        def is_numeric_str(val):
            try:
                float(str(val))
                return True
            except ValueError:
                return False
        if all(is_numeric_str(x) for x in clean_series):
            return "numeric_string"
        return "categorical_string"
        
    # Regel för floats (t.ex. 1.2 vs 1.0)
    if "float" in str(clean_series.dtype):
        if all(float(x).is_integer() for x in clean_series):
            return "discrete_float"
        return "continuous_float"
        
    return str(clean_series.dtype)