from app.data import data_service


class GlobalState:
    def __init__(self):
        # dataset & stats
        self.stats = None
        self.dataset = None

        # Parquet schema governance
        self.schema_fingerprint = None
        self.column_lineage = {}
        self.semantic_fingerprint = {}

        # Drift policies
        self.schema_drift_blocking = True
        self.semantic_drift_blocking = True

        # AI pipeline / data service
        self.data_service = data_service

    def reset(self):
        """
        Reset all global ingestion + AI state.
        Testsviten anropar detta i nästan alla Parquet‑tester.
        """
        self.stats = None
        self.dataset = None

        self.schema_fingerprint = None
        self.column_lineage = {}
        self.semantic_fingerprint = {}

        self.schema_drift_blocking = True
        self.semantic_drift_blocking = True


state = GlobalState()
