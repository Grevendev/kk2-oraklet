from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ============================================================
# Expected Security Headers
# ============================================================

EXPECTED_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "X-XSS-Protection": "1; mode=block",
}


# ============================================================
# Security Header Tests
# ============================================================

def test_security_headers_on_health():
    """Ensure security headers are applied to the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    for header, expected_value in EXPECTED_HEADERS.items():
        assert header in response.headers
        assert response.headers[header] == expected_value


def test_security_headers_on_data_endpoint():
    """Ensure security headers are applied to a typical data endpoint."""
    response = client.get("/data/stats")  # may return 200, 422, or 400
    assert response.status_code in (200, 422, 400)

    for header, expected_value in EXPECTED_HEADERS.items():
        assert header in response.headers
        assert response.headers[header] == expected_value
