from app.data import data_service

class GlobalState:
    def __init__(self):
        self.stats = None
        self.dataset = None
        self.data_service = data_service  # <-- lägg till detta

state = GlobalState()
