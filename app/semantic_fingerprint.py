def build_semantic_fingerprint(df):
    fp = {}

    for col in df.columns:
        series = df[col]

        fp[col] = {
            "dtype": str(series.dtype),
            "unique_values": sorted(series.dropna().unique().tolist()),
            "min": float(series.min()) if series.dtype.kind in "if" else None,
            "max": float(series.max()) if series.dtype.kind in "if" else None,
            "is_continuous": series.dtype.kind in "if",
            "value_count": int(series.count()),
        }

    return fp
