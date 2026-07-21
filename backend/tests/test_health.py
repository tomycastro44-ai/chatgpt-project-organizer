def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_system_endpoint_does_not_expose_secrets(client):
    response = client.get("/api/v1/system")
    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "api_version": "v1",
        "database": "sqlite",
        "demo_mode": True,
        "openai_configured": False,
        "originals_immutable": True,
    }
    assert "api_key" not in response.text.lower()
