"""
Integration tests for authentication API endpoints and auth_service.
"""


def test_register_success(client):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "username": "johndoe",
            "email": "john@university.edu",
            "password": "SecurePassword123!",
            "full_name": "John Doe",
            "programme": "Computer Science",
            "academic_year": 3,
        },
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["user"]["username"] == "johndoe"
    assert data["data"]["user"]["full_name"] == "John Doe"
    assert data["data"]["user"]["programme"] == "Computer Science"
    assert data["data"]["user"]["academic_year"] == 3
    # Check session cookie set
    cookies = res.headers.get_all("Set-Cookie")
    assert any("session_token=" in c for c in cookies)


def test_register_validation_errors(client):
    # Missing required field
    res = client.post(
        "/api/v1/auth/register",
        json={
            "username": "short",
            "email": "not-an-email",
            "password": "123",
            "full_name": "",
        },
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False


def test_register_duplicate_username_and_email(client):
    payload = {
        "username": "alice99",
        "email": "alice99@university.edu",
        "password": "Password123!",
        "full_name": "Alice Smith",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Duplicate username
    res2 = client.post(
        "/api/v1/auth/register",
        json={**payload, "email": "other@university.edu"},
    )
    assert res2.status_code == 409
    assert res2.get_json()["error"]["code"] == "DUPLICATE_RESOURCE"

    # Duplicate email
    res3 = client.post(
        "/api/v1/auth/register",
        json={**payload, "username": "otheralice"},
    )
    assert res3.status_code == 409
    assert res3.get_json()["error"]["code"] == "DUPLICATE_RESOURCE"


def test_login_success_and_logout(client):
    # Register
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "bobmarley",
            "email": "bob@university.edu",
            "password": "Password123!",
            "full_name": "Bob Marley",
        },
    )

    # Login
    res = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "bobmarley",
            "password": "Password123!",
        },
    )
    assert res.status_code == 200
    login_data = res.get_json()
    assert login_data["success"] is True
    assert login_data["data"]["user"]["username"] == "bobmarley"
    assert "programme" in login_data["data"]["user"]
    assert "academic_year" in login_data["data"]["user"]

    # Test me endpoint
    res_me = client.get("/api/v1/auth/me")
    assert res_me.status_code == 200
    assert res_me.get_json()["data"]["user"]["username"] == "bobmarley"

    # Logout
    res_logout = client.post("/api/v1/auth/logout")
    assert res_logout.status_code == 200

    # Me after logout is unauthorized
    res_me2 = client.get("/api/v1/auth/me")
    assert res_me2.status_code == 401


def test_login_invalid_credentials(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "nonexistent", "password": "wrong"},
    )
    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "AUTHENTICATION_FAILED"


def test_cross_site_bearer_auth_fallback_and_logout(client):
    """
    Regression test for cross-site third-party cookie blocking:
    When a browser blocks cross-site cookies, authentication must succeed via
    the exposed X-Session-Token and Authorization: Bearer header fallback.
    """
    # 1. Register a test user
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "username": "crosssiteuser",
            "email": "crosssite@university.edu",
            "password": "Password123!",
            "full_name": "Cross Site User",
        },
    )
    assert reg_res.status_code == 201
    token = reg_res.headers.get("X-Session-Token")
    assert token, "X-Session-Token header must be present on register"

    # 2. Simulate browser blocking cross-site cookies completely
    client.delete_cookie("session_token")

    # Protected GET /auth/me without cookies or header must fail with 401
    res_no_auth = client.get("/api/v1/auth/me")
    assert res_no_auth.status_code == 401
    assert res_no_auth.get_json()["message"] == "Authentication required. Please log in."

    # 3. Protected GET /auth/me with Bearer token must succeed even with zero cookies
    res_bearer = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_bearer.status_code == 200
    assert res_bearer.get_json()["data"]["user"]["username"] == "crosssiteuser"

    # 4. Protected POST /posts with Bearer token must succeed (reproducing the exact reported bug)
    res_post = client.post(
        "/api/v1/posts",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Requested-With": "XMLHttpRequest",
        },
        json={"content": "Regression verification post via Bearer token without cookies"},
    )
    assert res_post.status_code == 201
    assert res_post.get_json()["success"] is True

    # 5. Logout using Bearer header must invalidate session
    res_logout = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_logout.status_code == 200

    # 6. Subsequent requests with the logged-out token must be rejected
    res_after_logout = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_after_logout.status_code == 401


def test_register_null_optional_fields_handled_cleanly(client):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "username": "nulloptuser",
            "email": "nullopt@university.edu",
            "password": "Password123!",
            "full_name": "Null Opt User",
            "programme": None,
            "academic_year": None,
            "bio": None,
        },
    )
    assert res.status_code == 201
    user = res.get_json()["data"]["user"]
    assert user["programme"] == "General"
    assert user["academic_year"] == 1

    res_bad_year = client.post(
        "/api/v1/auth/register",
        json={
            "username": "badyearuser",
            "email": "badyear@university.edu",
            "password": "Password123!",
            "full_name": "Bad Year User",
            "academic_year": "not-a-number",
        },
    )
    assert res_bad_year.status_code == 400
    assert res_bad_year.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_cookie_mutation_without_csrf_header_rejected(app):
    raw_client = app.test_client()
    reg_res = raw_client.post(
        "/api/v1/auth/register",
        headers={"X-Requested-With": "XMLHttpRequest"},
        json={
            "username": "csrfuser",
            "email": "csrf@university.edu",
            "password": "Password123!",
            "full_name": "CSRF User",
        },
    )
    assert reg_res.status_code == 201

    # Cookie-only POST without X-Requested-With must be rejected with 403
    res_no_csrf = raw_client.post(
        "/api/v1/posts",
        json={"content": "Blocked CSRF attempt"},
    )
    assert res_no_csrf.status_code == 403
    assert res_no_csrf.get_json()["error"]["code"] == "FORBIDDEN"

