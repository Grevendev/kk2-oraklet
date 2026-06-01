# app/state.py

from app.data import data_service


class GlobalState:
    def __init__(self):
        self.reset()

    def reset(self):
        """
        Reset all global ingestion + AI state.
        Testsviten kan anropa detta för att få en ren miljö.
        """

        # Dataset & stats
        self.dataset = None
        self.stats = None

        # Canonical schema fingerprint
        # (kolumnnamn sorterade + canonical dtypes)
        self.schema_fingerprint = None

        # Semantic fingerprint per kolumn
        # { column_name: semantic_fp_string }
        self.semantic_fingerprint = {}

        # Column lineage (dtype historik)
        # { column_name: dtype_string }
        self.column_lineage = {}

        # Drift policies
        self.schema_drift_blocking = True
        self.semantic_drift_blocking = True

        # Data service (behålls)
        self.data_service = data_service

        # Pipeline (sätts av main.py)
        self.pipeline = None


state = GlobalState()


class CircuitBreaker:
    def __init__(self):
        self.max_failures = 5
        self.failure_count = 0
        self.state = "closed"


breaker = CircuitBreaker()
