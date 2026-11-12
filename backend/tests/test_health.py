def test_health_check_status_code(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200

def test_health_check_payload_contract(client):
    response = client.get("/api/v1/health")
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["message"] == "CampusConnect API is healthy"
    assert payload["data"]["status"] == "healthy"
    assert payload["data"]["service"] == "campusconnect-backend"
    assert payload["data"]["version"] == "1.0.0"

def test_404_handler(client):
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "RESOURCE_NOT_FOUND"

