import os

def pytest_configure():
    # Enable test mode before FastAPI app is imported
    os.environ["TESTING"] = "1"
