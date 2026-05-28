def test_security_headers_present_on_data_endpoint(client):
    resp = client.get("/data/stats")
    # Kan vara error, men headers ska ändå finnas
    assert "X-Frame-Options" in resp.headers
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-XSS-Protection"].startswith("1")
