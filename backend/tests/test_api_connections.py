"""
Integration tests for connection requests, connection lifecycle, and graph synchronization.
"""

import pytest


def _create_user(client, username, email, full_name):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "Password123!",
            "full_name": full_name,
        },
    )
    data = res.get_json()["data"]
    return data.get("user_id") or data["user"]["user_id"]


def test_connection_request_lifecycle(client):
    # Create user1 and user2
    u1_id = _create_user(client, "user_one", "u1@uni.edu", "User One")
    client.post("/api/v1/auth/logout")

    u2_id = _create_user(client, "user_two", "u2@uni.edu", "User Two")

    # user2 sends request to user1
    res_send = client.post(
        "/api/v1/connections/requests",
        json={"recipient_id": u1_id, "message": "Let's connect!"},
    )
    assert res_send.status_code == 201
    req_id = res_send.get_json()["data"]["request_id"]

    # user2 cannot send duplicate request
    res_dup = client.post(
        "/api/v1/connections/requests",
        json={"recipient_id": u1_id},
    )
    assert res_dup.status_code == 409

    # user2 cannot send request to self
    res_self = client.post(
        "/api/v1/connections/requests",
        json={"recipient_id": u2_id},
    )
    assert res_self.status_code == 400

    # Check sent requests for user2
    res_sent = client.get("/api/v1/connections/requests/sent")
    assert res_sent.status_code == 200
    sent_list = res_sent.get_json()["data"]["requests"]
    assert len(sent_list) == 1
    assert sent_list[0]["id"] == req_id

    # Login as user1
    client.post("/api/v1/auth/logout")
    client.post("/api/v1/auth/login", json={"identifier": "user_one", "password": "Password123!"})

    # Check received requests for user1
    res_rec = client.get("/api/v1/connections/requests/received")
    assert res_rec.status_code == 200
    rec_list = res_rec.get_json()["data"]["requests"]
    assert len(rec_list) == 1
    assert rec_list[0]["id"] == req_id

    # Check initial degree in graph is 0 for both
    res_deg1 = client.get(f"/api/v1/network/{u1_id}/degree")
    assert res_deg1.get_json()["data"]["degree"] == 0

    # Accept request
    res_accept = client.post(f"/api/v1/connections/requests/{req_id}/accept")
    assert res_accept.status_code == 200
    assert res_accept.get_json()["success"] is True

    # Graph edge synchronized! Degrees should now be 1
    res_deg_after1 = client.get(f"/api/v1/network/{u1_id}/degree")
    assert res_deg_after1.get_json()["data"]["degree"] == 1

    res_deg_after2 = client.get(f"/api/v1/network/{u2_id}/degree")
    assert res_deg_after2.get_json()["data"]["degree"] == 1

    # Check list connections
    res_conns = client.get("/api/v1/connections")
    conns = res_conns.get_json()["data"]["connections"]
    assert len(conns) == 1
    assert conns[0]["user_id"] == u2_id

    # Remove connection
    res_del = client.delete(f"/api/v1/connections/{u2_id}")
    assert res_del.status_code == 200

    # Degrees back to 0
    res_deg_zero = client.get(f"/api/v1/network/{u1_id}/degree")
    assert res_deg_zero.get_json()["data"]["degree"] == 0


def test_reject_and_cancel_request(client):
    u1_id = _create_user(client, "alice_c", "alice_c@uni.edu", "Alice C")
    client.post("/api/v1/auth/logout")

    u2_id = _create_user(client, "bob_c", "bob_c@uni.edu", "Bob C")

    # Bob sends request to Alice
    req_res = client.post("/api/v1/connections/requests", json={"recipient_id": u1_id})
    req_id = req_res.get_json()["data"]["request_id"]

    # Bob cancels request
    cancel_res = client.post(f"/api/v1/connections/requests/{req_id}/cancel")
    assert cancel_res.status_code == 200

    # Bob sends new request
    req2_res = client.post("/api/v1/connections/requests", json={"recipient_id": u1_id})
    req2_id = req2_res.get_json()["data"]["request_id"]

    # Alice logs in and rejects
    client.post("/api/v1/auth/logout")
    client.post("/api/v1/auth/login", json={"identifier": "alice_c", "password": "Password123!"})

    reject_res = client.post(f"/api/v1/connections/requests/{req2_id}/reject")
    assert reject_res.status_code == 200
