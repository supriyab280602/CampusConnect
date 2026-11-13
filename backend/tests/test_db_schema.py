import sqlite3
import pytest


def test_tables_created(db_conn):
    """Verify all five approved core tables exist in the database."""
    cursor = db_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
    )
    tables = {row["name"] for row in cursor.fetchall()}
    expected_tables = {
        "users",
        "connection_requests",
        "connections",
        "posts",
        "user_sessions",
    }
    assert expected_tables.issubset(tables)


def test_users_table_columns(db_conn):
    """Verify users table column structure and constraints."""
    cursor = db_conn.execute("PRAGMA table_info(users);")
    columns = {row["name"]: row for row in cursor.fetchall()}

    expected_cols = [
        "user_id",
        "username",
        "username_key",
        "email",
        "email_key",
        "password_hash",
        "full_name",
        "programme",
        "academic_year",
        "bio",
        "skills",
        "created_at",
        "updated_at",
    ]
    for col in expected_cols:
        assert col in columns, f"Missing column {col} in users table"

    # user_id must be PK
    assert columns["user_id"]["pk"] == 1
    # NOT NULL columns
    for col in ["username", "username_key", "email", "email_key", "password_hash", "full_name", "programme", "academic_year", "skills", "created_at", "updated_at"]:
        assert columns[col]["notnull"] == 1


def test_indexes_exist(db_conn):
    """Verify all 9 approved indexes exist."""
    cursor = db_conn.execute("SELECT name FROM sqlite_master WHERE type='index';")
    indexes = {row["name"] for row in cursor.fetchall() if row["name"]}

    expected_indexes = {
        "idx_connection_requests_pending",
        "idx_connection_requests_receiver",
        "idx_connection_requests_sender",
        "idx_connections_low",
        "idx_connections_high",
        "idx_posts_user_created",
        "idx_posts_created",
        "idx_user_sessions_user",
        "idx_user_sessions_expires",
    }
    for idx in expected_indexes:
        assert idx in indexes, f"Missing index: {idx}"


def test_foreign_key_enforcement(db_conn):
    """Verify foreign keys are enforced by attempting to insert orphaned child records."""
    # Insert post for non-existent user must fail with IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            """
            INSERT INTO posts (post_id, user_id, content, created_at, updated_at)
            VALUES ('p1', 'nonexistent_user', 'hello', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z')
            """
        )


def test_connection_request_self_request_check_constraint(db_conn):
    """Verify CHECK(sender_id != receiver_id) prevents self-requests at database level."""
    # Insert dummy user
    db_conn.execute(
        """
        INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
        VALUES ('u1', 'alice', 'alice', 'a@u.edu', 'a@u.edu', 'hash', 'Alice S', 'CS', 3, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z')
        """
    )
    # Attempt request where sender_id == receiver_id
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            """
            INSERT INTO connection_requests (request_id, sender_id, receiver_id, status, created_at, updated_at)
            VALUES ('req1', 'u1', 'u1', 'pending', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z')
            """
        )


def test_connection_request_status_check_constraint(db_conn):
    """Verify CHECK constraint on connection_requests status column."""
    db_conn.execute(
        """
        INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
        VALUES
            ('u1', 'alice', 'alice', 'a@u.edu', 'a@u.edu', 'h', 'Alice S', 'CS', 3, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z'),
            ('u2', 'bob', 'bob', 'b@u.edu', 'b@u.edu', 'h', 'Bob T', 'EE', 2, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z')
        """
    )
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            """
            INSERT INTO connection_requests (request_id, sender_id, receiver_id, status, created_at, updated_at)
            VALUES ('req1', 'u1', 'u2', 'INVALID_STATUS', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z')
            """
        )


def test_connection_canonical_order_check_constraint(db_conn):
    """Verify CHECK(user_id_low < user_id_high) rejects invalid or reverse ordering."""
    db_conn.execute(
        """
        INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
        VALUES
            ('u_a', 'alice', 'alice', 'a@u.edu', 'a@u.edu', 'h', 'Alice S', 'CS', 3, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z'),
            ('u_b', 'bob', 'bob', 'b@u.edu', 'b@u.edu', 'h', 'Bob T', 'EE', 2, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z')
        """
    )
    # Valid canonical order
    db_conn.execute(
        """
        INSERT INTO connections (connection_id, user_id_low, user_id_high, created_at)
        VALUES ('c1', 'u_a', 'u_b', '2026-11-13T00:00:00.000000Z')
        """
    )

    # Inverted order must fail check constraint
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            """
            INSERT INTO connections (connection_id, user_id_low, user_id_high, created_at)
            VALUES ('c2', 'u_b', 'u_a', '2026-11-13T00:00:00.000000Z')
            """
        )

    # Equal low and high (self-connection) must fail check constraint
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            """
            INSERT INTO connections (connection_id, user_id_low, user_id_high, created_at)
            VALUES ('c3', 'u_a', 'u_a', '2026-11-13T00:00:00.000000Z')
            """
        )


def test_cascade_deletion(db_conn):
    """Verify that deleting a user cascades to connection_requests, connections, posts, and sessions."""
    # Seed 2 users
    db_conn.execute(
        """
        INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
        VALUES
            ('u1', 'alice', 'alice', 'a@u.edu', 'a@u.edu', 'h', 'Alice S', 'CS', 3, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z'),
            ('u2', 'bob', 'bob', 'b@u.edu', 'b@u.edu', 'h', 'Bob T', 'EE', 2, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z')
        """
    )
    # Add request, connection, post, and session
    db_conn.execute(
        """
        INSERT INTO connection_requests (request_id, sender_id, receiver_id, status, created_at, updated_at)
        VALUES ('req1', 'u1', 'u2', 'accepted', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z')
        """
    )
    db_conn.execute(
        """
        INSERT INTO connections (connection_id, user_id_low, user_id_high, created_at)
        VALUES ('c1', 'u1', 'u2', '2026-11-13T00:00:00.000000Z')
        """
    )
    db_conn.execute(
        """
        INSERT INTO posts (post_id, user_id, content, created_at, updated_at)
        VALUES ('p1', 'u1', 'Alice post', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z')
        """
    )
    db_conn.execute(
        """
        INSERT INTO user_sessions (session_id, user_id, created_at, expires_at)
        VALUES ('s1', 'u1', '2026-11-13T00:00:00.000000Z', '2026-11-14T00:00:00.000000Z')
        """
    )

    # Delete u1
    db_conn.execute("DELETE FROM users WHERE user_id = 'u1';")

    # Verify cascades
    assert db_conn.execute("SELECT COUNT(*) FROM connection_requests;").fetchone()[0] == 0
    assert db_conn.execute("SELECT COUNT(*) FROM connections;").fetchone()[0] == 0
    assert db_conn.execute("SELECT COUNT(*) FROM posts;").fetchone()[0] == 0
    assert db_conn.execute("SELECT COUNT(*) FROM user_sessions;").fetchone()[0] == 0
