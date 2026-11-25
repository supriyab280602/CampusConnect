"""
Integration tests for posts and heap-based k-way feed merging with cursor pagination.
"""

import pytest


def test_posts_and_feed_merge(client):
    # User 1 registers and logs in
    res1 = client.post(
        "/api/v1/auth/register",
        json={
            "username": "feed_author1",
            "email": "fa1@uni.edu",
            "password": "Password123!",
            "full_name": "Feed Author One",
        },
    )
    u1_id = res1.get_json()["data"]["user_id"]

    # Create post 1 as u1
    p1_res = client.post("/api/v1/posts", json={"content": "Author 1 First Post"})
    assert p1_res.status_code == 201
    p1_id = p1_res.get_json()["data"]["post_id"]

    client.post("/api/v1/auth/logout")

    # User 2 registers
    res2 = client.post(
        "/api/v1/auth/register",
        json={
            "username": "feed_author2",
            "email": "fa2@uni.edu",
            "password": "Password123!",
            "full_name": "Feed Author Two",
        },
    )
    u2_id = res2.get_json()["data"]["user_id"]

    # Create post 2 as u2
    p2_res = client.post("/api/v1/posts", json={"content": "Author 2 Post"})
    assert p2_res.status_code == 201
    p2_id = p2_res.get_json()["data"]["post_id"]

    # Connect u2 and u1
    req_id = client.post("/api/v1/connections/requests", json={"recipient_id": u1_id}).get_json()["data"]["request_id"]
    client.post("/api/v1/auth/logout")

    client.post("/api/v1/auth/login", json={"identifier": "feed_author1", "password": "Password123!"})
    client.post(f"/api/v1/connections/requests/{req_id}/accept")

    # Author 1 creates post 3
    p3_res = client.post("/api/v1/posts", json={"content": "Author 1 Second Post"})
    assert p3_res.status_code == 201
    p3_id = p3_res.get_json()["data"]["post_id"]

    # Now get feed for Author 1: should contain p3, p2, p1 in reverse chronological order
    feed_res = client.get("/api/v1/feed?limit=10")
    assert feed_res.status_code == 200
    feed_posts = feed_res.get_json()["data"]["posts"]
    post_ids = [p["post_id"] for p in feed_posts]
    assert post_ids == [p3_id, p2_id, p1_id]

    # Test pagination: limit = 2
    feed_p1 = client.get("/api/v1/feed?limit=2")
    data_p1 = feed_p1.get_json()["data"]
    assert len(data_p1["posts"]) == 2
    assert data_p1["has_more"] is True
    assert data_p1["next_cursor"] is not None

    # Fetch next page using cursor
    cursor = data_p1["next_cursor"]
    feed_p2 = client.get(f"/api/v1/feed?limit=2&cursor={cursor}")
    data_p2 = feed_p2.get_json()["data"]
    assert len(data_p2["posts"]) == 1
    assert data_p2["posts"][0]["post_id"] == p1_id
    assert data_p2["has_more"] is False


def test_post_deletion_authorization(client):
    # User 1 registers
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "poster1",
            "email": "p1@uni.edu",
            "password": "Password123!",
            "full_name": "Poster One",
        },
    )
    p_res = client.post("/api/v1/posts", json={"content": "Post to delete"})
    p_id = p_res.get_json()["data"]["post_id"]
    client.post("/api/v1/auth/logout")

    # User 2 registers
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "poster2",
            "email": "p2@uni.edu",
            "password": "Password123!",
            "full_name": "Poster Two",
        },
    )

    # User 2 attempts to delete User 1's post -> 403 Forbidden
    del_res = client.delete(f"/api/v1/posts/{p_id}")
    assert del_res.status_code == 403

    client.post("/api/v1/auth/logout")

    # User 1 logs in and deletes post -> 200 OK
    client.post("/api/v1/auth/login", json={"identifier": "poster1", "password": "Password123!"})
    del_res_ok = client.delete(f"/api/v1/posts/{p_id}")
    assert del_res_ok.status_code == 200

    # Post now 404
    get_res = client.get(f"/api/v1/posts/{p_id}")
    assert get_res.status_code == 404


def test_feed_post_author_identity_independence(client):
    """Verify post author identity in feed reflects the author, not the viewing user."""
    # User A registers
    reg_a = client.post(
        "/api/v1/auth/register",
        json={
            "username": "auth_test_a",
            "email": "author_a@uni.edu",
            "password": "Password123!",
            "full_name": "Author Alpha",
            "programme": "Computer Science",
            "academic_year": 3,
        },
    )
    assert reg_a.status_code == 201
    user_a_id = reg_a.get_json()["data"]["user_id"]

    # User A creates a post
    post_res = client.post("/api/v1/posts", json={"content": "Alpha post content for feed"})
    assert post_res.status_code == 201
    post_id = post_res.get_json()["data"]["post_id"]

    # User A logs out
    logout_res = client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200

    # User B registers
    reg_b = client.post(
        "/api/v1/auth/register",
        json={
            "username": "auth_test_b",
            "email": "viewer_b@uni.edu",
            "password": "Password123!",
            "full_name": "Viewer Beta",
            "programme": "Information Technology",
            "academic_year": 2,
        },
    )
    assert reg_b.status_code == 201
    user_b_id = reg_b.get_json()["data"]["user_id"]

    # Connect User B and User A
    req_res = client.post("/api/v1/connections/requests", json={"recipient_id": user_a_id})
    assert req_res.status_code == 201
    request_id = req_res.get_json()["data"]["request_id"]

    client.post("/api/v1/auth/logout")

    # User A logs in and accepts connection
    client.post("/api/v1/auth/login", json={"identifier": "auth_test_a", "password": "Password123!"})
    client.post(f"/api/v1/connections/requests/{request_id}/accept")
    client.post("/api/v1/auth/logout")

    # User B logs in and views feed
    login_b = client.post("/api/v1/auth/login", json={"identifier": "auth_test_b", "password": "Password123!"})
    assert login_b.status_code == 200

    feed_res = client.get("/api/v1/feed")
    assert feed_res.status_code == 200
    feed_data = feed_res.get_json()["data"]
    feed_posts = feed_data["posts"]

    alpha_posts = [p for p in feed_posts if p["post_id"] == post_id]
    assert len(alpha_posts) == 1
    alpha_post = alpha_posts[0]

    # Verify author identity is strictly Author Alpha, never Viewer Beta
    assert alpha_post["user_id"] == user_a_id
    assert alpha_post["user_id"] != user_b_id
    assert alpha_post["author"] is not None
    assert alpha_post["author"]["user_id"] == user_a_id
    assert alpha_post["author"]["user_id"] != user_b_id
    assert alpha_post["author"]["username"] == "auth_test_a"
    assert alpha_post["author"]["full_name"] == "Author Alpha"
    assert alpha_post["author"]["programme"] == "Computer Science"
    assert alpha_post["author"]["academic_year"] == 3

