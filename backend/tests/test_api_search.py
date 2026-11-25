"""
Integration tests for search API endpoint and search_service.
"""

import pytest


def test_trie_prefix_search(client):
    # Register 3 users with different prefixes
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "sarah_connor",
            "email": "sarah@resistance.edu",
            "password": "Password123!",
            "full_name": "Sarah Connor",
        },
    )
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "sam_altman",
            "email": "sam@openai.edu",
            "password": "Password123!",
            "full_name": "Sam Altman",
        },
    )
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "john_connor",
            "email": "john_c@resistance.edu",
            "password": "Password123!",
            "full_name": "John Connor",
        },
    )

    # Search prefix 'sa' -> should find Sarah and Sam
    res_sa = client.get("/api/v1/search/users?q=sa")
    assert res_sa.status_code == 200
    results_sa = res_sa.get_json()["data"]["results"]
    usernames_sa = [u["username"] for u in results_sa]
    assert "sarah_connor" in usernames_sa
    assert "sam_altman" in usernames_sa
    assert "john_connor" not in usernames_sa

    # Search prefix 'connor' (token prefix) -> should find Sarah and John
    res_con = client.get("/api/v1/search/users?q=connor")
    assert res_con.status_code == 200
    results_con = res_con.get_json()["data"]["results"]
    usernames_con = [u["username"] for u in results_con]
    assert "sarah_connor" in usernames_con
    assert "john_connor" in usernames_con
    assert "sam_altman" not in usernames_con

    # Search empty query
    res_empty = client.get("/api/v1/search/users?q=")
    assert res_empty.status_code == 200
    assert res_empty.get_json()["data"]["results"] == []
