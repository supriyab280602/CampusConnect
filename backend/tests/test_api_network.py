"""
Integration tests for network exploration: mutuals, degree, BFS shortest path, recommendations.
"""

import pytest


def test_network_bfs_and_recommendations(client):
    # Build graph:
    # A - B - C - D
    # A also connected to E, E connected to C (so A and C have two common friends: B and E!)

    # Create users
    u_ids = {}
    for name in ["A", "B", "C", "D", "E"]:
        res = client.post(
            "/api/v1/auth/register",
            json={
                "username": f"user_{name.lower()}",
                "email": f"{name.lower()}@uni.edu",
                "password": "Password123!",
                "full_name": f"User {name}",
            },
        )
        data = res.get_json()["data"]
        u_ids[name] = data.get("user_id") or data["user"]["user_id"]
        client.post("/api/v1/auth/logout")

    # Helper to connect two users
    def connect(user_from, user_to):
        client.post("/api/v1/auth/login", json={"identifier": f"user_{user_from.lower()}", "password": "Password123!"})
        req = client.post("/api/v1/connections/requests", json={"recipient_id": u_ids[user_to]}).get_json()["data"]["request_id"]
        client.post("/api/v1/auth/logout")

        client.post("/api/v1/auth/login", json={"identifier": f"user_{user_to.lower()}", "password": "Password123!"})
        client.post(f"/api/v1/connections/requests/{req}/accept")
        client.post("/api/v1/auth/logout")

    connect("A", "B")
    connect("B", "C")
    connect("C", "D")
    connect("A", "E")
    connect("E", "C")

    # Login as User A
    client.post("/api/v1/auth/login", json={"identifier": "user_a", "password": "Password123!"})

    # Degree of A: B and E -> 2
    res_deg_a = client.get(f"/api/v1/network/{u_ids['A']}/degree")
    assert res_deg_a.get_json()["data"]["degree"] == 2

    # Mutual connections between A and C: should be B and E (2 mutuals)
    res_mut = client.get(f"/api/v1/network/{u_ids['C']}/mutuals")
    assert res_mut.status_code == 200
    mutual_ids = [m["user_id"] for m in res_mut.get_json()["data"]["mutual_connections"]]
    assert len(mutual_ids) == 2
    assert u_ids["B"] in mutual_ids
    assert u_ids["E"] in mutual_ids

    # BFS shortest path from A to D:
    # A -> B -> C -> D (or A -> E -> C -> D), degree is 3
    res_path = client.get(f"/api/v1/network/path?targetUserId={u_ids['D']}")
    assert res_path.status_code == 200
    path_data = res_path.get_json()["data"]
    assert path_data["degree_of_separation"] == 3
    assert len(path_data["path"]) == 4
    assert path_data["path"][0]["id"] == u_ids["A"]
    assert path_data["path"][-1]["id"] == u_ids["D"]

    # Recommendations for A:
    # C has 2 mutuals (B, E), D has 0 mutuals with A directly.
    # C should be top recommendation!
    res_rec = client.get("/api/v1/network/recommendations")
    assert res_rec.status_code == 200
    recs = res_rec.get_json()["data"]["recommendations"]
    assert len(recs) >= 1
    assert recs[0]["user"]["user_id"] == u_ids["C"]
    assert recs[0]["mutual_count"] == 2


def test_network_bfs_comprehensive_regression(client):
    """
    Comprehensive regression suite for BFS traversal, identifier resolution,
    and connection consistency across database and in-memory graph.
    """
    # Register test users:
    # U1 (Alpha), U2 (Beta), U3 (Gamma), U4 (Delta), U5 (Isolated), U6 (Pending), U7 (Rejected)
    users = {}
    usernames = ["alpha", "beta", "gamma", "delta", "isolated", "pending_user", "rejected_user"]
    for uname in usernames:
        res = client.post(
            "/api/v1/auth/register",
            json={
                "username": f"bfs_{uname}",
                "email": f"bfs_{uname}@uni.edu",
                "password": "Password123!",
                "full_name": f"BFS {uname.title()}",
            },
        )
        assert res.status_code == 201
        data = res.get_json()["data"]
        users[uname] = data.get("user_id") or data["user"]["user_id"]
        client.post("/api/v1/auth/logout")

    def connect(user_a, user_b):
        client.post("/api/v1/auth/login", json={"identifier": f"bfs_{user_a}", "password": "Password123!"})
        req = client.post("/api/v1/connections/requests", json={"recipient_id": users[user_b]}).get_json()["data"]["request_id"]
        client.post("/api/v1/auth/logout")

        client.post("/api/v1/auth/login", json={"identifier": f"bfs_{user_b}", "password": "Password123!"})
        client.post(f"/api/v1/connections/requests/{req}/accept")
        client.post("/api/v1/auth/logout")

    # Connect linear path: Alpha - Beta - Gamma - Delta
    connect("alpha", "beta")
    connect("beta", "gamma")
    connect("gamma", "delta")

    # 5. Pending request: pending_user sends request to Alpha, left pending
    client.post("/api/v1/auth/login", json={"identifier": "bfs_pending_user", "password": "Password123!"})
    client.post("/api/v1/connections/requests", json={"recipient_id": users["alpha"]})
    client.post("/api/v1/auth/logout")

    # 6. Rejected request: rejected_user sends request to Alpha, Alpha rejects
    client.post("/api/v1/auth/login", json={"identifier": "bfs_rejected_user", "password": "Password123!"})
    req_rej = client.post("/api/v1/connections/requests", json={"recipient_id": users["alpha"]}).get_json()["data"]["request_id"]
    client.post("/api/v1/auth/logout")

    client.post("/api/v1/auth/login", json={"identifier": "bfs_alpha", "password": "Password123!"})
    client.post(f"/api/v1/connections/requests/{req_rej}/reject")

    # --- Begin Regression Assertions (Logged in as Alpha) ---

    # 1. Direct accepted connection -> degree 1
    res1 = client.get(f"/api/v1/network/path?targetUserId={users['beta']}")
    assert res1.status_code == 200
    data1 = res1.get_json()["data"]
    assert data1["distance"] == 1
    assert data1["degree_of_separation"] == 1
    assert len(data1["path"]) == 2
    assert data1["path"][0]["id"] == users["alpha"]
    assert data1["path"][1]["id"] == users["beta"]

    # 2. Two-hop connection -> degree 2 with correct intermediate node
    res2 = client.get(f"/api/v1/network/path?targetUserId={users['gamma']}")
    assert res2.status_code == 200
    data2 = res2.get_json()["data"]
    assert data2["distance"] == 2
    assert len(data2["path"]) == 3
    assert data2["path"][0]["id"] == users["alpha"]
    assert data2["path"][1]["id"] == users["beta"]  # Intermediate node is Beta
    assert data2["path"][2]["id"] == users["gamma"]

    # 3. Three-hop connection -> degree 3
    res3 = client.get(f"/api/v1/network/path?targetUserId={users['delta']}")
    assert res3.status_code == 200
    data3 = res3.get_json()["data"]
    assert data3["distance"] == 3
    assert len(data3["path"]) == 4
    assert [n["id"] for n in data3["path"]] == [users["alpha"], users["beta"], users["gamma"], users["delta"]]

    # 4. No path -> Disconnected (returns distance: null, path: null)
    res4 = client.get(f"/api/v1/network/path?targetUserId={users['isolated']}")
    assert res4.status_code == 200
    data4 = res4.get_json()["data"]
    assert data4["distance"] is None
    assert data4["path"] is None

    # 5. Pending request -> not treated as connected
    res5 = client.get(f"/api/v1/network/path?targetUserId={users['pending_user']}")
    assert res5.status_code == 200
    data5 = res5.get_json()["data"]
    assert data5["distance"] is None
    assert data5["path"] is None

    # 6. Rejected request -> not treated as connected
    res6 = client.get(f"/api/v1/network/path?targetUserId={users['rejected_user']}")
    assert res6.status_code == 200
    data6 = res6.get_json()["data"]
    assert data6["distance"] is None
    assert data6["path"] is None

    # 8. Username lookup resolves the correct target:
    # Plain username
    res8_plain = client.get("/api/v1/network/path?targetUserId=bfs_beta")
    assert res8_plain.status_code == 200
    assert res8_plain.get_json()["data"]["distance"] == 1
    assert res8_plain.get_json()["data"]["path"][1]["id"] == users["beta"]

    # Leading '@' handle
    res8_at = client.get("/api/v1/network/path?targetUserId=@bfs_beta")
    assert res8_at.status_code == 200
    assert res8_at.get_json()["data"]["distance"] == 1

    # Case-insensitive username
    res8_case = client.get("/api/v1/network/path?targetUserId=BFS_BETA")
    assert res8_case.status_code == 200
    assert res8_case.get_json()["data"]["distance"] == 1

    # Multi-hop via username
    res8_multi = client.get("/api/v1/network/path?targetUserId=bfs_delta")
    assert res8_multi.status_code == 200
    assert res8_multi.get_json()["data"]["distance"] == 3

    # Exact full name lookup
    res8_name = client.get("/api/v1/network/path?targetUserId=BFS Beta")
    assert res8_name.status_code == 200
    assert res8_name.get_json()["data"]["distance"] == 1

    # Non-existent username -> returns 404 RESOURCE_NOT_FOUND (CC-QA-001)
    res8_none = client.get("/api/v1/network/path?targetUserId=nonexistent_user_12345")
    assert res8_none.status_code == 404
    assert res8_none.get_json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    # 9. Connection list and graph contain consistent accepted connections
    res9_conns = client.get("/api/v1/connections")
    assert res9_conns.status_code == 200
    conn_list = res9_conns.get_json()["data"]["connections"]
    connected_user_ids = {c["user"]["user_id"] for c in conn_list}
    assert connected_user_ids == {users["beta"]}  # Only Beta is directly connected to Alpha

    res9_deg = client.get(f"/api/v1/network/{users['alpha']}/degree")
    assert res9_deg.status_code == 200
    assert res9_deg.get_json()["data"]["degree"] == len(connected_user_ids) == 1

    client.post("/api/v1/auth/logout")

    # 7. Bidirectional traversal works
    # Log in as Delta -> path to Alpha must be Delta -> Gamma -> Beta -> Alpha (distance 3)
    client.post("/api/v1/auth/login", json={"identifier": "bfs_delta", "password": "Password123!"})
    res7_rev = client.get(f"/api/v1/network/path?targetUserId={users['alpha']}")
    assert res7_rev.status_code == 200
    data7 = res7_rev.get_json()["data"]
    assert data7["distance"] == 3
    assert [n["id"] for n in data7["path"]] == [users["delta"], users["gamma"], users["beta"], users["alpha"]]

    # Reverse via username
    res7_rev_uname = client.get("/api/v1/network/path?targetUserId=bfs_alpha")
    assert res7_rev_uname.status_code == 200
    assert res7_rev_uname.get_json()["data"]["distance"] == 3

