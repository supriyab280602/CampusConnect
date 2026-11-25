"""
Integration tests for authentication API endpoints and auth_service.
"""

import json
import pytest


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
    assert res.get_json()["success"] is True

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
