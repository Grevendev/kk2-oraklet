# app/state.py

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

        # Pipeline (sätts vid startup i app/main.py)
        self.pipeline = None

    def reset(self):
        """
        Reset all global ingestion + AI state.
        Testsviten kan anropa detta för att få en ren miljö.
        """
        self.stats = None
        self.dataset = None

        self.schema_fingerprint = None
        self.column_lineage = {}
        self.semantic_fingerprint = {}

        self.schema_drift_blocking = True
        self.semantic_drift_blocking = True

        # Pipeline lämnas orörd här; test kan sätta om den själva.


state = GlobalState()


class CircuitBreaker:
    def __init__(self):
        self.max_failures = 5
        self.failure_count = 0
        self.state = "closed"


breaker = CircuitBreaker()
