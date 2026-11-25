"""
Integration tests for user profile API endpoints and user_service.
"""

import pytest


def test_get_user_profile(client):
    # Register user (auto-logs in)
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "username": "clarkkent",
            "email": "clark@dailyplanet.edu",
            "password": "Password123!",
            "full_name": "Clark Kent",
            "programme": "Journalism",
            "academic_year": 2,
        },
    )
    user_id = reg.get_json()["data"]["user_id"]

    # Public fetch by ID
    res = client.get(f"/api/v1/users/{user_id}")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["user_id"] == user_id
    assert data["username"] == "clarkkent"
    assert data["full_name"] == "Clark Kent"
    assert data["programme"] == "Journalism"
    assert data["academic_year"] == 2


def test_get_user_not_found(client):
    # Register & login first
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "tester1",
            "email": "t1@uni.edu",
            "password": "Password123!",
            "full_name": "Tester One",
        },
    )
    res = client.get("/api/v1/users/nonexistent-id")
    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_update_profile_and_trie_sync(client):
    # Register
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "username": "batman",
            "email": "batman@wayne.edu",
            "password": "Password123!",
            "full_name": "Bruce Wayne",
        },
    )
    user_id = reg.get_json()["data"]["user_id"]

    # Search for old name
    res_search1 = client.get("/api/v1/search/users?q=Bruce")
    assert res_search1.status_code == 200
    results1 = res_search1.get_json()["data"]["results"]
    assert any(u["user_id"] == user_id for u in results1)

    # Update profile
    res_update = client.put(
        "/api/v1/users/me",
        json={
            "full_name": "The Dark Knight",
            "bio": "I am vengeance",
            "skills": ["Martial Arts", "Investigation"],
            "academic_year": 4,
        },
    )
    assert res_update.status_code == 200
    updated_user = res_update.get_json()["data"]["user"]
    assert updated_user["full_name"] == "The Dark Knight"
    assert updated_user["bio"] == "I am vengeance"
    assert updated_user["skills"] == ["Martial Arts", "Investigation"]
    assert updated_user["academic_year"] == 4

    # Search for old name: should NOT return user anymore
    res_search_old = client.get("/api/v1/search/users?q=Bruce")
    results_old = res_search_old.get_json()["data"]["results"]
    assert not any(u["user_id"] == user_id for u in results_old)

    # Search for new name: should return user immediately
    res_search_new = client.get("/api/v1/search/users?q=Dark")
    results_new = res_search_new.get_json()["data"]["results"]
    assert any(u["user_id"] == user_id for u in results_new)
