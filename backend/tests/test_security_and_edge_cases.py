from unittest.mock import patch

import pytest

from app import create_app
from app.dsa.exceptions import IndexUnavailableError
from app.utils.rate_limit import auth_rate_limiter


def _register_user(app, username, email):
    user_client = app.test_client()
    resp = user_client.post(
        "/api/v1/auth/register",
        headers={"X-Requested-With": "XMLHttpRequest"},
        json={
            "username": username,
            "email": email,
            "password": "Password123!",
            "full_name": f"{username} Full",
            "programme": "Computer Science",
            "academic_year": 2,
            "skills": ["Python"],
        },
    )
    assert resp.status_code == 201, resp.get_json()
    token = resp.headers.get("X-Session-Token")
    user_id = resp.get_json()["data"]["user_id"]
    return user_id, user_client, {"Authorization": f"Bearer {token}", "X-Requested-With": "XMLHttpRequest"}


@pytest.mark.parametrize("bad_year", ["abc", 0, 11, -1, True])
def test_register_rejects_invalid_academic_year(client, bad_year):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "username": f"badyear_{str(bad_year).lower()}",
            "email": f"badyear_{str(bad_year).lower()}@example.edu",
            "password": "Password123!",
            "full_name": "Bad Year",
            "academic_year": bad_year,
        },
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_logout_enforces_csrf_for_cookie_auth(app):
    raw_client = app.test_client()
    reg = raw_client.post(
        "/api/v1/auth/register",
        json={
            "username": "csrfuser",
            "email": "csrfuser@example.edu",
            "password": "Password123!",
            "full_name": "CSRF User",
        },
    )
    assert reg.status_code == 201

    # Cookie-based logout without X-Requested-With must be rejected (403)
    blocked = raw_client.post("/api/v1/auth/logout")
    assert blocked.status_code == 403
    assert blocked.get_json()["error"]["code"] == "FORBIDDEN"

    # With X-Requested-With header, logout succeeds (200)
    ok = raw_client.post("/api/v1/auth/logout", headers={"X-Requested-With": "XMLHttpRequest"})
    assert ok.status_code == 200


def test_auth_rate_limiting_returns_429(temp_db_path):
    auth_rate_limiter.reset()

    class RateLimitedConfig:
        TESTING = True
        SECRET_KEY = "test-secret-key"
        FRONTEND_ORIGIN = "http://localhost:5173"
        DATABASE_PATH = temp_db_path
        AUTO_MIGRATE = True
        RATELIMIT_ENABLED = True
        RATELIMIT_MAX_REQUESTS = 2
        RATELIMIT_WINDOW_SECONDS = 60

    app = create_app(RateLimitedConfig)
    client = app.test_client()

    for _ in range(2):
        r = client.post("/api/v1/auth/login", json={"username": "nobody", "password": "wrong"})
        assert r.status_code == 401

    limited = client.post("/api/v1/auth/login", json={"username": "nobody", "password": "wrong"})
    assert limited.status_code == 429
    assert limited.get_json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    auth_rate_limiter.reset()


def test_remove_connection_double_delete_returns_404_not_500(app):
    uid_a, client_a, headers_a = _register_user(app, "alice_rm", "alice_rm@example.edu")
    uid_b, client_b, headers_b = _register_user(app, "bob_rm", "bob_rm@example.edu")

    req_resp = client_a.post(
        "/api/v1/connections/requests",
        json={"receiver_id": uid_b},
        headers=headers_a,
    )
    assert req_resp.status_code == 201
    req_id = req_resp.get_json()["data"]["request_id"]

    acc_resp = client_b.post(f"/api/v1/connections/requests/{req_id}/accept", headers=headers_b)
    assert acc_resp.status_code == 200

    first_del = client_a.delete(f"/api/v1/connections/{uid_b}", headers=headers_a)
    assert first_del.status_code == 200

    second_del = client_a.delete(f"/api/v1/connections/{uid_b}", headers=headers_a)
    assert second_del.status_code == 404
    assert second_del.get_json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_index_unavailable_surfaces_503_across_routes(app):
    uid_a, client_a, headers_a = _register_user(app, "idx_a", "idx_a@example.edu")
    uid_b, client_b, headers_b = _register_user(app, "idx_b", "idx_b@example.edu")

    req_resp = client_a.post(
        "/api/v1/connections/requests",
        json={"receiver_id": uid_b},
        headers=headers_a,
    )
    assert req_resp.status_code == 201
    req_id = req_resp.get_json()["data"]["request_id"]

    with patch("app.dsa.manager.DSAManager.get_neighbors", side_effect=IndexUnavailableError("rebuilding")):
        feed_resp = client_a.get("/api/v1/feed", headers=headers_a)
        assert feed_resp.status_code == 503
        assert feed_resp.get_json()["error"]["code"] == "INDEX_UNAVAILABLE"

        rec_resp = client_a.get("/api/v1/network/recommendations", headers=headers_a)
        assert rec_resp.status_code == 503
        assert rec_resp.get_json()["error"]["code"] == "INDEX_UNAVAILABLE"

    with patch("app.dsa.manager.DSAManager.synchronized_mutation", side_effect=IndexUnavailableError("rebuilding")):
        accept_resp = client_b.post(f"/api/v1/connections/requests/{req_id}/accept", headers=headers_b)
        assert accept_resp.status_code == 503
        assert accept_resp.get_json()["error"]["code"] == "INDEX_UNAVAILABLE"


def test_all_registered_api_endpoints_enforce_expected_auth(app):
    protected_routes = [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/users/usr_missing"),
        ("PUT", "/api/v1/users/me"),
        ("POST", "/api/v1/posts"),
        ("GET", "/api/v1/posts/pst_missing"),
        ("DELETE", "/api/v1/posts/pst_missing"),
        ("GET", "/api/v1/feed"),
        ("GET", "/api/v1/search/users?q=test"),
        ("POST", "/api/v1/connections/requests"),
        ("GET", "/api/v1/connections/requests/received"),
        ("GET", "/api/v1/connections/requests/sent"),
        ("POST", "/api/v1/connections/requests/req_missing/accept"),
        ("POST", "/api/v1/connections/requests/req_missing/reject"),
        ("POST", "/api/v1/connections/requests/req_missing/cancel"),
        ("GET", "/api/v1/connections"),
        ("DELETE", "/api/v1/connections/usr_missing"),
        ("GET", "/api/v1/network/usr_missing/mutuals"),
        ("GET", "/api/v1/network/usr_missing/degree"),
        ("GET", "/api/v1/network/path?targetUserId=usr_missing"),
        ("GET", "/api/v1/network/recommendations"),
    ]
    client = app.test_client()
    for method, path in protected_routes:
        resp = client.open(path, method=method, headers={"X-Requested-With": "XMLHttpRequest"})
        assert resp.status_code == 401, f"{method} {path} returned {resp.status_code}"
