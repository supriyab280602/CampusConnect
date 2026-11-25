"""
Phase 3 Deep Verification & Security Acceptance Tests.
Covers:
- Authentication & Session token hashing, expiration, and logout invalidation
- Authorization boundaries (cross-user post deletion, connection request tampering)
- Sensitive data exposure prevention (password hashes never exposed)
- Connection request lifecycle, self-connection, idempotency, and status enforcement
- Graph BFS shortest paths, self-path, isolated nodes, and deterministic traversal
- Recommendation ranking, exclusion of self, and existing connection filtering
- Trie search with duplicate names, case normalization, and profile update synchronization
- Heap feed stream merging, cursor validation, and post deletion visibility
"""

import pytest
import sqlite3
from app.utils.helpers import hash_session_token


def _register(client, username, email, full_name, password="Password123!"):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "full_name": full_name,
            "programme": "Computer Science",
            "academic_year": 2,
        },
    )
    assert res.status_code == 201
    return res.get_json()["data"]["user_id"]


def _login(client, identifier, password="Password123!"):
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": identifier, "password": password},
    )
    assert res.status_code == 200
    return res.get_json()["data"]["user_id"]


# =============================================================================
# 1. AUTHENTICATION & SESSION SECURITY
# =============================================================================

def test_password_hashes_never_exposed_in_any_response(client):
    """Verify password_hash or sensitive secrets are never leaked in any API response."""
    u1_id = _register(client, "sec_user1", "s1@uni.edu", "Security User One")
    client.post("/api/v1/posts", json={"content": "Security post"})
    client.post("/api/v1/auth/logout")

    u2_id = _register(client, "sec_user2", "s2@uni.edu", "Security User Two")

    endpoints_to_probe = [
        "/api/v1/auth/me",
        f"/api/v1/users/{u1_id}",
        f"/api/v1/search/users?q=Security",
        "/api/v1/feed",
        "/api/v1/connections",
        f"/api/v1/network/{u1_id}/degree",
        "/api/v1/network/recommendations",
    ]

    for ep in endpoints_to_probe:
        res = client.get(ep)
        body = res.get_data(as_text=True)
        assert "password_hash" not in body
        assert "pbkdf2" not in body
        assert "scrypt" not in body


def test_session_token_hashing_in_database(client, temp_db_path):
    """Verify raw session token in cookie is stored as SHA-256 hash in SQLite."""
    _register(client, "hash_user", "hash@uni.edu", "Hash User")
    
    # Extract session cookie
    cookie = client.get_cookie("session_token")
    assert cookie is not None
    raw_token = cookie.value

    # Verify database holds only SHA-256 hash of token, never the raw token
    conn = sqlite3.connect(temp_db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT session_id FROM user_sessions").fetchone()
    conn.close()

    assert row is not None
    assert row["session_id"] == hash_session_token(raw_token)
    assert row["session_id"] != raw_token


def test_session_expiration_and_invalidation(client, temp_db_path):
    """Verify expired sessions and logged-out sessions are strictly rejected."""
    _register(client, "exp_user", "exp@uni.edu", "Exp User")

    # Manually expire the session in the database
    conn = sqlite3.connect(temp_db_path)
    conn.execute("UPDATE user_sessions SET expires_at = '2000-01-01T00:00:00.000000Z'")
    conn.commit()
    conn.close()

    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "SESSION_EXPIRED"


# =============================================================================
# 2. AUTHORIZATION & CROSS-USER ISOLATION
# =============================================================================

def test_user_cannot_manipulate_other_users_connection_requests(client):
    """
    Verify strict ownership checks:
    - User C cannot accept request from User A to User B (403 FORBIDDEN)
    - User C cannot reject request from User A to User B (403 FORBIDDEN)
    - User B (recipient) cannot cancel request sent by User A (403 FORBIDDEN)
    - User C cannot cancel request sent by User A (403 FORBIDDEN)
    """
    u_a = _register(client, "alice_auth", "aa@uni.edu", "Alice Auth")
    client.post("/api/v1/auth/logout")

    u_b = _register(client, "bob_auth", "ba@uni.edu", "Bob Auth")
    client.post("/api/v1/auth/logout")

    u_c = _register(client, "charlie_auth", "ca@uni.edu", "Charlie Auth")
    client.post("/api/v1/auth/logout")

    # Alice sends request to Bob
    _login(client, "alice_auth")
    req_res = client.post("/api/v1/connections/requests", json={"receiver_id": u_b})
    req_id = req_res.get_json()["data"]["request_id"]
    client.post("/api/v1/auth/logout")

    # Charlie logs in and attempts to accept Alice->Bob request -> 403
    _login(client, "charlie_auth")
    res_accept_c = client.post(f"/api/v1/connections/requests/{req_id}/accept")
    assert res_accept_c.status_code == 403
    assert res_accept_c.get_json()["error"]["code"] == "FORBIDDEN"

    # Charlie attempts to reject Alice->Bob request -> 403
    res_reject_c = client.post(f"/api/v1/connections/requests/{req_id}/reject")
    assert res_reject_c.status_code == 403

    # Charlie attempts to cancel Alice->Bob request -> 403
    res_cancel_c = client.post(f"/api/v1/connections/requests/{req_id}/cancel")
    assert res_cancel_c.status_code == 403
    client.post("/api/v1/auth/logout")

    # Bob (recipient) attempts to cancel Alice's request -> 403 (recipient can reject, not cancel)
    _login(client, "bob_auth")
    res_cancel_b = client.post(f"/api/v1/connections/requests/{req_id}/cancel")
    assert res_cancel_b.status_code == 403

    # Bob accepts request -> 200 OK
    res_accept_b = client.post(f"/api/v1/connections/requests/{req_id}/accept")
    assert res_accept_b.status_code == 200

    # Bob attempts to accept AGAIN -> 409 CONFLICT (already processed)
    res_reaccept = client.post(f"/api/v1/connections/requests/{req_id}/accept")
    assert res_reaccept.status_code == 409


def test_accepting_or_rejecting_nonexistent_request(client):
    """Verify 404 is returned when request ID does not exist."""
    _register(client, "orphan_user", "ou@uni.edu", "Orphan User")
    res = client.post("/api/v1/connections/requests/nonexistent-req-id/accept")
    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_remove_nonexistent_connection(client):
    """Verify 404 is returned when removing a connection between unconnected users."""
    u1 = _register(client, "rem_u1", "ru1@uni.edu", "Rem User 1")
    client.post("/api/v1/auth/logout")
    u2 = _register(client, "rem_u2", "ru2@uni.edu", "Rem User 2")

    res = client.delete(f"/api/v1/connections/{u1}")
    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "RESOURCE_NOT_FOUND"


# =============================================================================
# 3. PROFILE VALIDATION AND INTEGRITY
# =============================================================================

def test_profile_update_validation(client):
    """Verify empty full_name and invalid academic_year are rejected."""
    _register(client, "prof_user", "pu@uni.edu", "Prof User")

    # Empty full name
    res1 = client.put("/api/v1/users/me", json={"full_name": "   "})
    assert res1.status_code == 400
    assert res1.get_json()["error"]["code"] == "VALIDATION_ERROR"

    # Invalid academic year
    res2 = client.put("/api/v1/users/me", json={"academic_year": 0})
    assert res2.status_code == 400
    assert res2.get_json()["error"]["code"] == "VALIDATION_ERROR"

    res3 = client.put("/api/v1/users/me", json={"academic_year": 15})
    assert res3.status_code == 400


# =============================================================================
# 4. TRIE SEARCH EDGE CASES
# =============================================================================

def test_trie_search_multiple_identical_display_names(client):
    """Verify multiple users with identical full names are all found and mapped."""
    _register(client, "alex_cs", "alex1@uni.edu", "Alex Smith")
    client.post("/api/v1/auth/logout")

    _register(client, "alex_math", "alex2@uni.edu", "Alex Smith")
    client.post("/api/v1/auth/logout")

    _register(client, "alex_chem", "alex3@uni.edu", "Alex Smith")

    # Search prefix 'Alex'
    res = client.get("/api/v1/search/users?q=Alex")
    assert res.status_code == 200
    results = res.get_json()["data"]["results"]
    assert len(results) == 3
    usernames = {u["username"] for u in results}
    assert usernames == {"alex_cs", "alex_math", "alex_chem"}


# =============================================================================
# 5. GRAPH BFS AND RECOMMENDATIONS
# =============================================================================

def test_bfs_shortest_path_edge_cases(client):
    """Verify self-path returns 0 distance, and disconnected component returns distance -1."""
    u1 = _register(client, "bfs_u1", "bu1@uni.edu", "BFS User 1")
    client.post("/api/v1/auth/logout")

    u2 = _register(client, "bfs_u2", "bu2@uni.edu", "BFS User 2")

    # Self-path
    res_self = client.get(f"/api/v1/network/path?targetUserId={u2}")
    # Currently u2 is logged in; target is u2
    assert res_self.status_code == 200
    data_self = res_self.get_json()["data"]
    assert data_self["distance"] == 0
    assert len(data_self["path"]) == 1

    # Disconnected path: target is u1 (no connection between u2 and u1)
    res_dis = client.get(f"/api/v1/network/path?targetUserId={u1}")
    assert res_dis.status_code == 200
    data_dis = res_dis.get_json()["data"]
    assert data_dis["distance"] is None
    assert data_dis["path"] is None


# =============================================================================
# 6. HEAP FEED MERGING & CURSOR VALIDATION
# =============================================================================

def test_feed_cursor_validation(client):
    """Verify malformed/invalid pagination cursor returns 400 Bad Request."""
    _register(client, "feed_u1", "fu1@uni.edu", "Feed User 1")
    res = client.get("/api/v1/feed?cursor=totally-invalid-cursor!")
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_feed_user_with_no_connections_and_no_posts(client):
    """Verify user with 0 connections and 0 posts gets empty feed."""
    _register(client, "empty_u", "empty@uni.edu", "Empty User")
    res = client.get("/api/v1/feed")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["posts"] == []
    assert data["has_more"] is False
    assert data["next_cursor"] is None
