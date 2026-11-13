import sqlite3
import pytest
from app.db.connection import get_connection, transaction
from app.db.schema import migrate_db
from app.repositories import (
    UserRepository,
    ConnectionRequestRepository,
    ConnectionRepository,
)


def test_transaction_rollback_on_failure(db_conn):
    """Verify that an exception inside a transaction block rolls back all statements."""
    UserRepository.create_user(
        db_conn, "alice", "alice@u.edu", "h", "Alice S", "CS", 1, []
    )

    with pytest.raises(RuntimeError):
        with transaction(db_conn, immediate=True):
            db_conn.execute(
                """
                INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
                VALUES ('u2', 'bob', 'bob', 'bob@u.edu', 'bob@u.edu', 'h', 'Bob', 'CS', 1, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z')
                """
            )
            # Simulated catastrophic error in business flow
            raise RuntimeError("Simulated failure after insert")

    # Bob must NOT exist in the database due to rollback
    assert UserRepository.get_by_id(db_conn, "u2") is None


def test_persistence_across_connection_restarts(temp_db_path):
    """Verify persisted data remains intact after closing connection and reconnecting."""
    # 1. Connect and initialize schema
    conn1 = get_connection(temp_db_path)
    migrate_db(conn1)

    # 2. Insert records
    user = UserRepository.create_user(
        conn1, "persist_user", "persist@u.edu", "hash123", "Persist User", "CS", 2, ["Python", "SQLite"]
    )
    user_id = user["user_id"]

    # 3. Close first connection (simulating server shutdown)
    conn1.close()

    # 4. Open fresh connection (simulating server restart)
    conn2 = get_connection(temp_db_path)
    try:
        retrieved = UserRepository.get_by_id(conn2, user_id)
        assert retrieved is not None
        assert retrieved["username"] == "persist_user"
        assert retrieved["email"] == "persist@u.edu"
        assert "SQLite" in retrieved["skills"]
    finally:
        conn2.close()


def test_accept_request_transactional_atomicity(db_conn):
    """Verify accept_request creates connection and updates status atomically."""
    u1 = UserRepository.create_user(db_conn, "sender", "s@u.edu", "h", "Sender", "CS", 1, [])
    u2 = UserRepository.create_user(db_conn, "receiver", "r@u.edu", "h", "Receiver", "CS", 1, [])

    req = ConnectionRequestRepository.create_request(db_conn, u1["user_id"], u2["user_id"])

    # Accept request
    result = ConnectionRequestRepository.accept_request(db_conn, req["request_id"], u2["user_id"])
    assert result["request"]["status"] == "accepted"
    assert result["connection"] is not None

    # Verify both records are committed
    saved_req = ConnectionRequestRepository.get_by_id(db_conn, req["request_id"])
    assert saved_req["status"] == "accepted"

    saved_conn = ConnectionRepository.get_connection(db_conn, u1["user_id"], u2["user_id"])
    assert saved_conn is not None
