"""
Unit and integration tests for DSAManager: locking, synchronization, recovery, and rebuild.
"""

import sqlite3
import threading
from unittest.mock import patch
import pytest

from app.db.connection import get_connection
from app.db.schema import init_db
from app.dsa.exceptions import IndexUnavailableError, IndexDegradedCommittedError
from app.dsa.manager import DSAManager


def seed_test_database(conn: sqlite3.Connection):
    """Seed database with 4 users and 2 connections."""
    conn.execute(
        """
        INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
        VALUES
        ('u1', 'alice', 'alice', 'a@u.edu', 'a@u.edu', 'h', 'Alice Smith', 'CS', 3, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z'),
        ('u2', 'bob', 'bob', 'b@u.edu', 'b@u.edu', 'h', 'Bob Jones', 'CS', 3, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z'),
        ('u3', 'charlie', 'charlie', 'c@u.edu', 'c@u.edu', 'h', 'Charlie Brown', 'CS', 3, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z'),
        ('u4', 'david', 'david', 'd@u.edu', 'd@u.edu', 'h', 'David Miller', 'CS', 3, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z');
        """
    )
    # Connections: u1 - u2, u2 - u3 (u1 -> u2 -> u3)
    conn.execute(
        """
        INSERT INTO connections (connection_id, user_id_low, user_id_high, created_at)
        VALUES
        ('c1', 'u1', 'u2', '2026-11-13T00:00:00.000000Z'),
        ('c2', 'u2', 'u3', '2026-11-13T00:00:00.000000Z');
        """
    )


def test_manager_initialization_and_read_queries():
    conn = get_connection(":memory:")
    init_db(":memory:")
    # Build schema in conn
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    assert manager.is_ready() is False

    manager.initialize(conn)
    assert manager.is_ready() is True

    # 1. Shortest path: u1 -> u2 -> u3 (dist 2)
    path, dist = manager.get_shortest_path("u1", "u3")
    assert path == ["u1", "u2", "u3"]
    assert dist == 2

    # 2. Degree: u2 has degree 2 (u1, u3), u4 is isolated (degree 0)
    assert manager.get_degree("u2") == 2
    assert manager.get_degree("u4") == 0

    # 3. Mutual connections: u1 and u3 have mutual u2
    assert manager.get_mutual_connections("u1", "u3") == ["u2"]

    # 4. Search prefix: "ali" -> u1, "smi" -> u1
    assert manager.search_prefix("ali") == ["u1"]
    assert manager.search_prefix("smi") == ["u1"]
    assert manager.search_prefix("dav") == ["u4"]

    conn.close()


def test_manager_query_while_unavailable_raises_error():
    manager = DSAManager()
    assert manager.is_ready() is False

    with pytest.raises(IndexUnavailableError):
        manager.get_shortest_path("u1", "u2")

    with pytest.raises(IndexUnavailableError):
        manager.get_degree("u1")

    with pytest.raises(IndexUnavailableError):
        manager.get_mutual_connections("u1", "u2")

    with pytest.raises(IndexUnavailableError):
        manager.search_prefix("ali")


def test_manager_rebuild_commit_failure_preserves_unavailable_state():
    """Verify forced failure during rebuild prevents manager from becoming ready."""
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)

    manager = DSAManager()
    # Drop required table so rebuild query fails inside transaction
    conn.execute("DROP TABLE users;")

    with pytest.raises(sqlite3.OperationalError):
        manager.rebuild(conn)

    assert manager.is_ready() is False
    with pytest.raises(IndexUnavailableError):
        manager.get_degree("u1")
    conn.close()


def test_state_a_database_rollback_leaves_memory_untouched():
    """State A: If DB transaction fails before commit, memory remains untouched."""
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    initial_degree = manager.get_degree("u1")

    with pytest.raises(sqlite3.IntegrityError):
        with manager.synchronized_mutation(conn) as sync:
            sync.on_commit(lambda: manager._graph.add_edge("u1", "u4"))
            # Trigger DB integrity error (duplicate primary key)
            conn.execute("INSERT INTO users (user_id) VALUES ('u1');")

    # In-memory graph must not have added the edge
    assert manager.get_degree("u1") == initial_degree
    assert manager.is_ready() is True
    conn.close()


def test_state_b_clean_commit_and_memory_success():
    """State B: DB commit and memory update both succeed."""
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    with manager.synchronized_mutation(conn) as sync:
        conn.execute("INSERT INTO connections (connection_id, user_id_low, user_id_high, created_at) VALUES ('c3', 'u1', 'u4', '2026-11-13T00:00:00.000000Z');")
        sync.on_commit(lambda: manager._graph.add_edge("u1", "u4"))

    assert manager.get_degree("u1") == 2
    assert manager.get_degree("u4") == 1
    assert manager.is_ready() is True
    conn.close()


def test_controlled_mutation_methods_encapsulate_internals():
    """Verify services use controlled record_* methods without accessing _graph or _trie."""
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    # 1. Accepted connection
    with manager.synchronized_mutation(conn) as sync:
        conn.execute("INSERT INTO connections (connection_id, user_id_low, user_id_high, created_at) VALUES ('c_test', 'u1', 'u4', '2026-11-13T00:00:00.000000Z');")
        sync.record_connection_accepted("u1", "u4")

    assert manager.get_degree("u1") == 2
    assert manager.get_degree("u4") == 1

    # 2. Removed connection
    with manager.synchronized_mutation(conn) as sync:
        conn.execute("DELETE FROM connections WHERE connection_id = 'c_test';")
        sync.record_connection_removed("u1", "u4")

    assert manager.get_degree("u1") == 1
    assert manager.get_degree("u4") == 0

    # 3. User registration
    with manager.synchronized_mutation(conn) as sync:
        conn.execute("INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at) VALUES ('u5', 'eve', 'eve', 'e@u.edu', 'e@u.edu', 'h', 'Eve Adams', 'CS', 1, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z');")
        sync.record_user_registered("u5", "eve", "Eve Adams")

    assert manager.get_degree("u5") == 0
    assert manager.search_prefix("eve") == ["u5"]
    assert manager.search_prefix("ada") == ["u5"]

    # 4. User profile update (read current profile INSIDE lock to prevent stale keys)
    with manager.synchronized_mutation(conn) as sync:
        # Read old state inside synchronized block
        old_user = conn.execute("SELECT username, full_name FROM users WHERE user_id = 'u5';").fetchone()
        conn.execute("UPDATE users SET username = 'evelyn', username_key = 'evelyn', full_name = 'Evelyn Taylor' WHERE user_id = 'u5';")
        sync.record_user_updated(
            "u5",
            old_username=old_user["username"],
            old_full_name=old_user["full_name"],
            new_username="evelyn",
            new_full_name="Evelyn Taylor"
        )

    assert manager.search_prefix("eve") == ["u5"]      # matches "evelyn"
    assert manager.search_prefix("ada") == []          # old name "Adams" purged
    assert manager.search_prefix("tay") == ["u5"]      # new name "Taylor" active

    # 5. User deletion
    with manager.synchronized_mutation(conn) as sync:
        cur_user = conn.execute("SELECT username, full_name FROM users WHERE user_id = 'u5';").fetchone()
        conn.execute("DELETE FROM users WHERE user_id = 'u5';")
        sync.record_user_deleted("u5", cur_user["username"], cur_user["full_name"])

    assert manager.search_prefix("eve") == []
    assert manager.search_prefix("tay") == []
    conn.close()


def test_state_c_commit_success_memory_failure_rebuild_success():
    """
    State C: DB commit succeeds, in-memory update fails, rebuild succeeds.
    Must return success to caller because SQLite is committed and memory was recovered!
    """
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    def failing_memory_hook():
        raise RuntimeError("Transient memory update failure!")

    # Synchronized mutation must succeed despite hook failure because rebuild recovers memory
    with manager.synchronized_mutation(conn) as sync:
        conn.execute("INSERT INTO connections (connection_id, user_id_low, user_id_high, created_at) VALUES ('c3', 'u1', 'u4', '2026-11-13T00:00:00.000000Z');")
        sync.on_commit(failing_memory_hook)

    # Manager must be ready and contain the edge rebuilt from SQLite
    assert manager.is_ready() is True
    assert manager.get_degree("u1") == 2
    assert manager.get_degree("u4") == 1
    conn.close()


def test_state_d_commit_success_memory_failure_rebuild_failure():
    """
    State D: DB commit succeeds, in-memory update fails, rebuild also fails.
    Must raise IndexDegradedCommittedError explicitly distinguishing committed DB from unavailable index.
    """
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    def failing_memory_hook():
        raise RuntimeError("Transient memory update failure!")

    with patch.object(manager, "rebuild", side_effect=sqlite3.OperationalError("Disk error during rebuild")):
        with pytest.raises(IndexDegradedCommittedError, match="Database mutation committed successfully"):
            with manager.synchronized_mutation(conn) as sync:
                conn.execute("INSERT INTO connections (connection_id, user_id_low, user_id_high, created_at) VALUES ('c3', 'u1', 'u4', '2026-11-13T00:00:00.000000Z');")
                sync.on_commit(failing_memory_hook)

    assert manager.is_ready() is False
    conn.close()


def test_missing_hook_rolls_back_database():
    """Verify omitting post-commit hook rolls back SQLite and raises RuntimeError."""
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    # Capture pre-mutation snapshot of connections table
    pre_snapshot = conn.execute("SELECT * FROM connections ORDER BY connection_id;").fetchall()

    with pytest.raises(RuntimeError, match="Missing mandatory post-commit synchronization hook"):
        with manager.synchronized_mutation(conn):
            # Insert row but deliberately omit sync.on_commit(...)
            conn.execute("INSERT INTO connections (connection_id, user_id_low, user_id_high, created_at) VALUES ('c_unhooked', 'u3', 'u4', '2026-11-13T00:00:00.000000Z');")

    # Assert database state matches pre-mutation snapshot exactly (row was rolled back)
    post_snapshot = conn.execute("SELECT * FROM connections ORDER BY connection_id;").fetchall()
    assert [dict(r) for r in post_snapshot] == [dict(r) for r in pre_snapshot]
    conn.close()


def test_unrecoverable_index_preserves_database_state():
    """Verify attempting mutation while index is unrecoverable aborts without altering database."""
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    # Capture initial database state snapshots
    pre_conns = conn.execute("SELECT * FROM connections ORDER BY connection_id;").fetchall()
    pre_users = conn.execute("SELECT * FROM users ORDER BY user_id;").fetchall()

    # Force index unavailable and make rebuild fail
    manager.mark_unavailable()
    with patch.object(manager, "rebuild", side_effect=sqlite3.OperationalError("Fatal storage failure")):
        with pytest.raises(IndexUnavailableError, match="DSA indices are unavailable"):
            with manager.synchronized_mutation(conn) as sync:
                conn.execute("INSERT INTO connections (connection_id, user_id_low, user_id_high, created_at) VALUES ('c_bad', 'u3', 'u4', '2026-11-13T00:00:00.000000Z');")
                sync.on_commit(lambda: None)

    # Database state must match initial snapshot exactly
    post_conns = conn.execute("SELECT * FROM connections ORDER BY connection_id;").fetchall()
    post_users = conn.execute("SELECT * FROM users ORDER BY user_id;").fetchall()
    assert [dict(r) for r in post_conns] == [dict(r) for r in pre_conns]
    assert [dict(r) for r in post_users] == [dict(r) for r in pre_users]
    assert conn.in_transaction is False
    conn.close()


def test_concurrency_and_read_synchronization(tmp_path):
    """Verify concurrent reads, writes, and rebuilds across threads without race conditions."""
    db_file = str(tmp_path / "concurrent_dsa.db")
    init_conn = get_connection(db_file)
    from app.db.schema import migrate_db
    migrate_db(init_conn)
    seed_test_database(init_conn)

    manager = DSAManager()
    manager.initialize(init_conn)
    init_conn.close()

    errors = []

    def reader_worker():
        try:
            for _ in range(50):
                manager.get_shortest_path("u1", "u3")
                manager.search_prefix("ali")
                manager.get_degree("u2")
        except Exception as e:
            errors.append(e)

    def writer_worker():
        worker_conn = get_connection(db_file)
        try:
            for _ in range(10):
                with manager.synchronized_mutation(worker_conn) as sync:
                    sync.on_commit(lambda: manager._graph.add_edge("u1", "u2"))
        except Exception as e:
            errors.append(e)
        finally:
            worker_conn.close()

    threads = [
        threading.Thread(target=reader_worker),
        threading.Thread(target=reader_worker),
        threading.Thread(target=writer_worker),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0


def test_commit_failure_rolls_back_and_protects_memory():
    """
    Verify that if SQLite transaction commit fails:
    1. The transaction is safely rolled back.
    2. conn.in_transaction is False (no dangling transaction).
    3. The registered post-commit memory hook is NEVER executed.
    4. In-memory indices remain clean and consistent with SQLite.
    5. The connection remains usable for subsequent queries.
    """
    real_conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(real_conn)
    seed_test_database(real_conn)

    class FailCommitConnection:
        def __init__(self, raw_conn):
            self._raw = raw_conn
            self.should_fail_commit = False

        def execute(self, sql, *args, **kwargs):
            if self.should_fail_commit and sql.strip() == "COMMIT;":
                raise sqlite3.OperationalError("Simulated disk I/O error on COMMIT")
            return self._raw.execute(sql, *args, **kwargs)

        def __getattr__(self, name):
            return getattr(self._raw, name)

    conn = FailCommitConnection(real_conn)

    manager = DSAManager()
    manager.initialize(conn)

    initial_degree = manager.get_degree("u1")
    hook_called = False

    def hook():
        nonlocal hook_called
        hook_called = True
        manager._graph.add_edge("u1", "u4")

    conn.should_fail_commit = True

    with pytest.raises(sqlite3.OperationalError, match="Simulated disk I/O error on COMMIT"):
        with manager.synchronized_mutation(conn) as sync:
            sync.on_commit(hook)
            conn.execute("INSERT INTO connections (connection_id, user_id_low, user_id_high, created_at) VALUES ('c_failed', 'u1', 'u4', '2026-11-13T00:00:00.000000Z');")

    conn.should_fail_commit = False

    # 1. Post-commit hook was never executed
    assert hook_called is False
    # 2. In-memory graph was not updated
    assert manager.get_degree("u1") == initial_degree
    # 3. No dangling open transaction
    assert conn.in_transaction is False
    # 4. Connection remains usable
    users = conn.execute("SELECT user_id FROM users;").fetchall()
    assert len(users) == 4
    # 5. Row was rolled back from SQLite
    failed_row = conn.execute("SELECT * FROM connections WHERE connection_id = 'c_failed';").fetchone()
    assert failed_row is None
    real_conn.close()


def test_controlled_mutation_methods_and_encapsulation():
    """
    Verify all 5 controlled mutation methods correctly register their post-commit
    hooks and update graph and Trie state upon successful SQLite commit.
    """
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    # 1. record_user_registered
    with manager.synchronized_mutation(conn) as sync:
        conn.execute(
            """
            INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
            VALUES ('u5', 'eve', 'eve', 'e@u.edu', 'e@u.edu', 'h', 'Eve Adams', 'CS', 3, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z');
            """
        )
        sync.record_user_registered("u5", "eve", "Eve Adams")

    assert manager.get_degree("u5") == 0
    assert manager.search_prefix("eve") == ["u5"]
    assert manager.search_prefix("ada") == ["u5"]

    # 2. record_connection_accepted
    with manager.synchronized_mutation(conn) as sync:
        conn.execute(
            """
            INSERT INTO connections (connection_id, user_id_low, user_id_high, created_at)
            VALUES ('c4', 'u1', 'u5', '2026-11-13T00:00:00.000000Z');
            """
        )
        sync.record_connection_accepted("u1", "u5")

    assert manager.get_degree("u1") == 2
    assert manager.get_degree("u5") == 1
    path, dist = manager.get_shortest_path("u5", "u3")
    assert path == ["u5", "u1", "u2", "u3"]
    assert dist == 3

    # 3. record_user_updated
    with manager.synchronized_mutation(conn) as sync:
        conn.execute("UPDATE users SET username = 'evelyn', full_name = 'Evelyn Taylor' WHERE user_id = 'u5';")
        sync.record_user_updated("u5", "eve", "Eve Adams", "evelyn", "Evelyn Taylor")

    assert manager.search_prefix("eve") == ["u5"]  # "evelyn" matches prefix "eve"
    assert manager.search_prefix("tay") == ["u5"]
    assert manager.search_prefix("ada") == []  # Old search key pruned

    # 4. record_connection_removed
    with manager.synchronized_mutation(conn) as sync:
        conn.execute("DELETE FROM connections WHERE connection_id = 'c4';")
        sync.record_connection_removed("u1", "u5")

    assert manager.get_degree("u5") == 0
    path, dist = manager.get_shortest_path("u5", "u3")
    assert path is None
    assert dist == -1

    # 5. record_user_deleted
    with manager.synchronized_mutation(conn) as sync:
        conn.execute("DELETE FROM users WHERE user_id = 'u5';")
        sync.record_user_deleted("u5", "evelyn", "Evelyn Taylor")

    assert manager.search_prefix("evelyn") == []
    assert manager.search_prefix("tay") == []
    # Vertex u5 has been removed from the graph
    with pytest.raises(KeyError):
        manager.get_degree("u5")
    path, dist = manager.get_shortest_path("u5", "u1")
    assert path is None
    assert dist == -1
    conn.close()


def test_controlled_mutation_validation_and_duplicate_prevention():
    """
    Verify input validation on all 5 controlled mutation methods:
    - Non-empty string checks for all arguments.
    - Distinct user identifiers for connection mutations.
    - Prevention of duplicate mutation operations on the same coordinator.
    """
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    # 1. Invalid input validation: record_connection_accepted
    with manager.synchronized_mutation(conn) as sync:
        with pytest.raises(ValueError, match="user_a"):
            sync.record_connection_accepted("", "u2")
        with pytest.raises(ValueError, match="user_b"):
            sync.record_connection_accepted("u1", "   ")
        with pytest.raises(ValueError, match="Self-connections are prohibited"):
            sync.record_connection_accepted("u1", "u1")
        # Provide valid call so exit doesn't fail on missing hook
        sync.record_connection_accepted("u1", "u4")

    # 2. Duplicate mutation prevention on single coordinator
    with manager.synchronized_mutation(conn) as sync:
        sync.record_connection_accepted("u3", "u4")
        with pytest.raises(ValueError, match="Only one post-commit hook"):
            sync.record_connection_accepted("u1", "u4")
        with pytest.raises(ValueError, match="Only one post-commit hook"):
            sync.record_user_registered("u10", "u10", "User 10")

    # 3. Invalid input validation: record_connection_removed
    with manager.synchronized_mutation(conn) as sync:
        with pytest.raises(ValueError, match="Vertices must be distinct"):
            sync.record_connection_removed("u1", "u1")
        with pytest.raises(ValueError, match="user_a"):
            sync.record_connection_removed("", "u2")
        sync.record_connection_removed("u1", "u2")

    # 4. Invalid input validation: record_user_registered
    with manager.synchronized_mutation(conn) as sync:
        with pytest.raises(ValueError, match="user_id"):
            sync.record_user_registered("", "usr", "Full Name")
        with pytest.raises(ValueError, match="username"):
            sync.record_user_registered("uid", "  ", "Full Name")
        with pytest.raises(ValueError, match="full_name"):
            sync.record_user_registered("uid", "usr", "")
        sync.record_user_registered("uid", "usr", "Full Name")

    # 5. Invalid input validation: record_user_updated
    with manager.synchronized_mutation(conn) as sync:
        with pytest.raises(ValueError, match="user_id"):
            sync.record_user_updated("", "old_u", "old_f", "new_u", "new_f")
        with pytest.raises(ValueError, match="old_username"):
            sync.record_user_updated("uid", " ", "old_f", "new_u", "new_f")
        with pytest.raises(ValueError, match="new_full_name"):
            sync.record_user_updated("uid", "old_u", "old_f", "new_u", "")
        sync.record_user_updated("uid", "old_u", "old_f", "new_u", "new_f")

    # 6. Invalid input validation: record_user_deleted
    with manager.synchronized_mutation(conn) as sync:
        with pytest.raises(ValueError, match="user_id"):
            sync.record_user_deleted("", "usr", "Full Name")
        with pytest.raises(ValueError, match="full_name"):
            sync.record_user_deleted("uid", "usr", "")
        sync.record_user_deleted("uid", "usr", "Full Name")

    conn.close()


def test_mutation_coordinator_rejects_existing_transaction():
    """
    Verify MutationCoordinator.__enter__ rejects an already-active SQLite transaction
    and raises RuntimeError without corrupting transaction state.
    """
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    # Start an outer transaction
    conn.execute("BEGIN;")
    assert conn.in_transaction is True

    # Attempting to enter MutationCoordinator must be rejected
    with pytest.raises(RuntimeError, match="existing active SQLite transaction"):
        with manager.synchronized_mutation(conn):
            pass

    # Outer transaction remains active and uncommitted
    assert conn.in_transaction is True
    conn.execute("ROLLBACK;")
    assert conn.in_transaction is False
    conn.close()


def test_rejected_nested_mutation_preserves_outer_transaction():
    """
    Verify rejection of nested mutation does not commit or roll back the caller's
    outer transaction, allowing caller to commit or roll back uncommitted changes.
    """
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    # Outer transaction with uncommitted work
    conn.execute("BEGIN;")
    conn.execute(
        """
        INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
        VALUES ('u_outer', 'outer', 'outer', 'outer@u.edu', 'outer@u.edu', 'h', 'Outer User', 'CS', 3, '[]', '2026-11-18T00:00:00.000000Z', '2026-11-18T00:00:00.000000Z');
        """
    )

    # Rejection of nested mutation
    with pytest.raises(RuntimeError, match="existing active SQLite transaction"):
        with manager.synchronized_mutation(conn):
            pass

    # Outer transaction is preserved and still in progress
    assert conn.in_transaction is True

    # Caller can successfully commit its own transaction
    conn.execute("COMMIT;")
    assert conn.in_transaction is False

    # Data from outer transaction was preserved and committed
    row = conn.execute("SELECT username FROM users WHERE user_id = 'u_outer';").fetchone()
    assert row is not None
    assert row["username"] == "outer"
    conn.close()


def test_nested_mutation_does_not_execute_memory_hook():
    """
    Verify that an attempt to open a nested synchronized mutation never executes
    any memory hook, preventing memory-database desynchronization.
    """
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    initial_degree = manager.get_degree("u1")
    hook_called = False

    def hook():
        nonlocal hook_called
        hook_called = True
        manager._graph.add_edge("u1", "u4")

    # Start outer transaction
    conn.execute("BEGIN;")

    coordinator = manager.synchronized_mutation(conn)
    with pytest.raises(RuntimeError, match="existing active SQLite transaction"):
        with coordinator as sync:
            sync.on_commit(hook)

    # Hook must never have executed
    assert hook_called is False
    assert manager.get_degree("u1") == initial_degree

    conn.execute("ROLLBACK;")
    conn.close()


def test_rebuild_rejects_existing_transaction():
    """
    Verify DSAManager.rebuild rejects a connection with an active transaction:
    - Existing readiness state remains unchanged (stays True).
    - In-memory index contents remain unchanged.
    - Outer transaction is neither committed nor rolled back.
    - Caller can continue and commit or roll back its outer transaction.
    """
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)
    assert manager.is_ready() is True

    # Capture initial index contents
    initial_path, initial_dist = manager.get_shortest_path("u1", "u3")
    initial_degree_u2 = manager.get_degree("u2")
    initial_search = manager.search_prefix("ali")

    # Open outer transaction
    conn.execute("BEGIN;")
    assert conn.in_transaction is True

    # Attempt rebuild - must be rejected BEFORE changing _is_ready or touching indices
    with pytest.raises(RuntimeError, match="connection with an active transaction"):
        manager.rebuild(conn)

    # 1. Readiness state is preserved
    assert manager.is_ready() is True

    # 2. Index contents are completely unchanged
    path, dist = manager.get_shortest_path("u1", "u3")
    assert path == initial_path
    assert dist == initial_dist
    assert manager.get_degree("u2") == initial_degree_u2
    assert manager.search_prefix("ali") == initial_search

    # 3. Outer transaction is preserved and still active
    assert conn.in_transaction is True

    # 4. Caller can roll back outer transaction cleanly
    conn.execute("ROLLBACK;")
    assert conn.in_transaction is False
    conn.close()


def test_rebuild_does_not_publish_uncommitted_data():
    """
    Verify rebuild rejection prevents uncommitted dirty database state from
    being read into or published to in-memory graph and Trie indices.
    """
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    # Insert uncommitted user and connection inside active transaction
    conn.execute("BEGIN;")
    conn.execute(
        """
        INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
        VALUES ('u_uncommitted', 'ghost', 'ghost', 'g@u.edu', 'g@u.edu', 'h', 'Ghost User', 'CS', 3, '[]', '2026-11-18T00:00:00.000000Z', '2026-11-18T00:00:00.000000Z');
        """
    )
    conn.execute(
        """
        INSERT INTO connections (connection_id, user_id_low, user_id_high, created_at)
        VALUES ('c_ghost', 'u1', 'u_uncommitted', '2026-11-18T00:00:00.000000Z');
        """
    )

    # Rebuild must reject this uncommitted connection
    with pytest.raises(RuntimeError, match="connection with an active transaction"):
        manager.rebuild(conn)

    # Uncommitted user must NOT appear in search index
    assert manager.search_prefix("ghost") == []
    # Uncommitted connection must NOT appear in graph
    assert "u_uncommitted" not in manager._graph.all_vertices()
    assert manager.get_degree("u1") == 1

    # Roll back dirty uncommitted changes
    conn.execute("ROLLBACK;")
    assert conn.in_transaction is False
    conn.close()


def test_coordinator_cannot_be_reused():
    """
    Verify MutationCoordinator enforces strict lifecycle state:
    - A coordinator cannot be re-entered while active (preserving ACTIVE state).
    - A coordinator cannot be re-entered after successful or failed completion.
    """
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    from app.dsa.manager import CoordinatorState
    coordinator = manager.synchronized_mutation(conn)

    # First entry and active re-entry attempt
    with coordinator as sync:
        # Re-entering an active coordinator must raise without overwriting ACTIVE state
        with pytest.raises(RuntimeError, match="cannot be reused or re-entered"):
            coordinator.__enter__()
        assert coordinator._state == CoordinatorState.ACTIVE

        conn.execute(
            """
            INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
            VALUES ('u_reuse', 'reuse', 'reuse', 'r@u.edu', 'r@u.edu', 'h', 'Reuse User', 'CS', 3, '[]', '2026-11-18T00:00:00.000000Z', '2026-11-18T00:00:00.000000Z');
            """
        )
        sync.record_user_registered("u_reuse", "reuse", "Reuse User")

    # State is now COMPLETED
    assert coordinator._state == CoordinatorState.COMPLETED

    # Second entry on the completed coordinator instance must be rejected
    with pytest.raises(RuntimeError, match="cannot be reused or re-entered"):
        with coordinator:
            pass
    assert coordinator._state == CoordinatorState.COMPLETED

    conn.close()


def test_coordinator_rejects_hook_registration_outside_active_context():
    """
    Verify MutationCoordinator rejects hook registration outside the active
    context (before __enter__ or after __exit__), and rejects exiting an inactive coordinator.
    """
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    coordinator = manager.synchronized_mutation(conn)

    # 1. Registration before entry (state CREATED)
    with pytest.raises(RuntimeError, match="Hooks can only be registered while MutationCoordinator is active"):
        coordinator.record_user_registered("uX", "ux", "User X")
    with pytest.raises(RuntimeError, match="Hooks can only be registered while MutationCoordinator is active"):
        coordinator.on_commit(lambda: None)

    # 2. Exiting an inactive coordinator directly
    with pytest.raises(RuntimeError, match="Cannot exit an inactive"):
        coordinator.__exit__(None, None, None)

    # 3. Registration after exit (state COMPLETED)
    with coordinator as sync:
        conn.execute(
            """
            INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
            VALUES ('u_active', 'active', 'active', 'act@u.edu', 'act@u.edu', 'h', 'Active User', 'CS', 3, '[]', '2026-11-18T00:00:00.000000Z', '2026-11-18T00:00:00.000000Z');
            """
        )
        sync.record_user_registered("u_active", "active", "Active User")

    with pytest.raises(RuntimeError, match="Hooks can only be registered while MutationCoordinator is active"):
        coordinator.record_user_registered("uY", "uy", "User Y")
    with pytest.raises(RuntimeError, match="Hooks can only be registered while MutationCoordinator is active"):
        coordinator.on_commit(lambda: None)

    # Exiting already completed coordinator
    with pytest.raises(RuntimeError, match="Cannot exit an inactive"):
        coordinator.__exit__(None, None, None)

    conn.close()


def test_coordinator_releases_lock_after_failed_entry():
    """
    Verify that when MutationCoordinator.__enter__ fails (e.g. active transaction),
    the process-wide manager lock is released immediately on all failure paths.
    """
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    # Trigger failed entry via active transaction
    conn.execute("BEGIN;")
    with pytest.raises(RuntimeError, match="existing active SQLite transaction"):
        with manager.synchronized_mutation(conn):
            pass
    conn.execute("ROLLBACK;")

    # Verify another thread can acquire the lock without blocking
    lock_acquired = False

    def try_lock():
        nonlocal lock_acquired
        acquired = manager._lock.acquire(blocking=True, timeout=1.0)
        if acquired:
            lock_acquired = True
            manager._lock.release()

    t = threading.Thread(target=try_lock)
    t.start()
    t.join(timeout=2.0)

    assert lock_acquired is True, "Manager lock remained held after failed coordinator entry!"

    # Verify a subsequent valid mutation can proceed normally
    with manager.synchronized_mutation(conn) as sync:
        conn.execute(
            """
            INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
            VALUES ('u_lock_ok', 'lockok', 'lockok', 'lok@u.edu', 'lok@u.edu', 'h', 'Lock Ok', 'CS', 3, '[]', '2026-11-18T00:00:00.000000Z', '2026-11-18T00:00:00.000000Z');
            """
        )
        sync.record_user_registered("u_lock_ok", "lockok", "Lock Ok")

    assert manager.search_prefix("lockok") == ["u_lock_ok"]
    conn.close()


def test_coordinator_cannot_be_reused_after_transaction_begin_failure():
    """
    Inject a controlled failure during transaction entry (BEGIN IMMEDIATE) and verify:
    - The original entry raises the expected exception.
    - The manager lock is released.
    - The coordinator transitions to COMPLETED.
    - Reusing the same coordinator raises RuntimeError.
    - The database connection remains usable.
    """
    real_conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(real_conn)
    seed_test_database(real_conn)

    class FailBeginConnection:
        def __init__(self, raw_conn):
            self._raw = raw_conn
            self.fail_begin = False

        def execute(self, sql, *args, **kwargs):
            if self.fail_begin and "BEGIN" in sql:
                raise sqlite3.OperationalError("Simulated failure during BEGIN IMMEDIATE")
            return self._raw.execute(sql, *args, **kwargs)

        def __getattr__(self, name):
            return getattr(self._raw, name)

    conn = FailBeginConnection(real_conn)
    manager = DSAManager()
    manager.initialize(conn)

    coordinator = manager.synchronized_mutation(conn)
    conn.fail_begin = True

    # 1. The original entry raises the expected exception
    with pytest.raises(sqlite3.OperationalError, match="Simulated failure during BEGIN IMMEDIATE"):
        with coordinator:
            pass

    conn.fail_begin = False

    # 2. The manager lock is released
    lock_acquired = False

    def try_lock():
        nonlocal lock_acquired
        acquired = manager._lock.acquire(blocking=True, timeout=1.0)
        if acquired:
            lock_acquired = True
            manager._lock.release()

    t = threading.Thread(target=try_lock)
    t.start()
    t.join(timeout=2.0)
    assert lock_acquired is True, "Manager lock remained held after failed transaction begin!"

    # 3. The coordinator transitions to COMPLETED
    from app.dsa.manager import CoordinatorState
    assert coordinator._state == CoordinatorState.COMPLETED

    # 4. Reusing the same coordinator raises RuntimeError
    with pytest.raises(RuntimeError, match="cannot be reused or re-entered"):
        with coordinator:
            pass

    # 5. The database connection remains usable
    users = conn.execute("SELECT user_id FROM users;").fetchall()
    assert len(users) == 4

    # And a new coordinator works cleanly on the connection
    with manager.synchronized_mutation(conn) as sync:
        conn.execute(
            """
            INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
            VALUES ('u_new_ok', 'newok', 'newok', 'nok@u.edu', 'nok@u.edu', 'h', 'New Ok', 'CS', 3, '[]', '2026-11-18T00:00:00.000000Z', '2026-11-18T00:00:00.000000Z');
            """
        )
        sync.record_user_registered("u_new_ok", "newok", "New Ok")

    assert manager.search_prefix("newok") == ["u_new_ok"]
    real_conn.close()


def test_coordinator_releases_lock_and_completes_on_keyboard_interrupt():
    """
    Verify BaseException (KeyboardInterrupt) during transaction initialization:
    1. Injected KeyboardInterrupt during transaction entry raises KeyboardInterrupt.
    2. The manager lock is released immediately.
    3. The coordinator transitions to COMPLETED.
    4. Reusing that failed coordinator is rejected.
    5. The SQLite connection remains usable.
    6. A fresh coordinator can subsequently complete a valid mutation.
    """
    real_conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(real_conn)
    seed_test_database(real_conn)

    class InterruptBeginConnection:
        def __init__(self, raw_conn):
            self._raw = raw_conn
            self.trigger_interrupt = False

        def execute(self, sql, *args, **kwargs):
            if self.trigger_interrupt and "BEGIN" in sql:
                raise KeyboardInterrupt("Simulated Ctrl+C during BEGIN IMMEDIATE")
            return self._raw.execute(sql, *args, **kwargs)

        def __getattr__(self, name):
            return getattr(self._raw, name)

    conn = InterruptBeginConnection(real_conn)
    manager = DSAManager()
    manager.initialize(conn)

    coordinator = manager.synchronized_mutation(conn)
    conn.trigger_interrupt = True

    # 1. Injected KeyboardInterrupt during transaction initialization raises KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt, match="Simulated Ctrl\\+C during BEGIN IMMEDIATE"):
        with coordinator:
            pass

    conn.trigger_interrupt = False

    # 2. The manager lock is released
    lock_acquired = False

    def try_lock():
        nonlocal lock_acquired
        acquired = manager._lock.acquire(blocking=True, timeout=1.0)
        if acquired:
            lock_acquired = True
            manager._lock.release()

    t = threading.Thread(target=try_lock)
    t.start()
    t.join(timeout=2.0)
    assert lock_acquired is True, "Manager lock remained held after KeyboardInterrupt in __enter__!"

    # 3. The coordinator transitions to COMPLETED
    from app.dsa.manager import CoordinatorState
    assert coordinator._state == CoordinatorState.COMPLETED

    # 4. Reusing that failed coordinator is rejected
    with pytest.raises(RuntimeError, match="cannot be reused or re-entered"):
        with coordinator:
            pass

    # 5. The SQLite connection remains usable
    assert conn.in_transaction is False
    users = conn.execute("SELECT user_id FROM users;").fetchall()
    assert len(users) == 4

    # 6. A fresh coordinator can subsequently complete a valid mutation
    with manager.synchronized_mutation(conn) as sync:
        conn.execute(
            """
            INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
            VALUES ('u_ki_ok', 'kiok', 'kiok', 'ki@u.edu', 'ki@u.edu', 'h', 'KI Ok', 'CS', 3, '[]', '2026-11-18T00:00:00.000000Z', '2026-11-18T00:00:00.000000Z');
            """
        )
        sync.record_user_registered("u_ki_ok", "kiok", "KI Ok")

    assert manager.search_prefix("kiok") == ["u_ki_ok"]
    real_conn.close()


def test_coordinator_releases_lock_and_completes_on_system_exit():
    """
    Verify BaseException (SystemExit) during transaction initialization:
    - Lock is released.
    - Coordinator transitions to COMPLETED.
    - Reusing is rejected.
    - Subsequent fresh mutations succeed.
    """
    real_conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(real_conn)
    seed_test_database(real_conn)

    class ExitBeginConnection:
        def __init__(self, raw_conn):
            self._raw = raw_conn
            self.trigger_exit = False

        def execute(self, sql, *args, **kwargs):
            if self.trigger_exit and "BEGIN" in sql:
                raise SystemExit("Simulated SystemExit during BEGIN IMMEDIATE")
            return self._raw.execute(sql, *args, **kwargs)

        def __getattr__(self, name):
            return getattr(self._raw, name)

    conn = ExitBeginConnection(real_conn)
    manager = DSAManager()
    manager.initialize(conn)

    coordinator = manager.synchronized_mutation(conn)
    conn.trigger_exit = True

    with pytest.raises(SystemExit, match="Simulated SystemExit during BEGIN IMMEDIATE"):
        with coordinator:
            pass

    conn.trigger_exit = False

    # Lock is released
    lock_acquired = False

    def try_lock():
        nonlocal lock_acquired
        acquired = manager._lock.acquire(blocking=True, timeout=1.0)
        if acquired:
            lock_acquired = True
            manager._lock.release()

    t = threading.Thread(target=try_lock)
    t.start()
    t.join(timeout=2.0)
    assert lock_acquired is True, "Manager lock remained held after SystemExit in __enter__!"

    from app.dsa.manager import CoordinatorState
    assert coordinator._state == CoordinatorState.COMPLETED

    with pytest.raises(RuntimeError, match="cannot be reused or re-entered"):
        with coordinator:
            pass

    real_conn.close()


def test_lock_acquisition_interruption_safety():
    """
    Deterministic test simulating KeyboardInterrupt directly from lock acquisition:
    1. The exception propagates cleanly.
    2. The coordinator transitions to COMPLETED.
    3. No unacquired lock is released (release calls == 0).
    4. Reusing the coordinator is rejected.
    5. The manager lock remains usable.
    6. A fresh coordinator can subsequently perform a valid mutation.
    """
    conn = get_connection(":memory:")
    from app.db.schema import migrate_db
    migrate_db(conn)
    seed_test_database(conn)

    manager = DSAManager()
    manager.initialize(conn)

    # Controlled wrapper around manager._lock to inject KeyboardInterrupt on acquire
    class InterruptedLock:
        def __init__(self, real_lock):
            self._real = real_lock
            self.raise_interrupt = False
            self.acquire_calls = 0
            self.release_calls = 0

        def acquire(self, *args, **kwargs):
            self.acquire_calls += 1
            if self.raise_interrupt:
                raise KeyboardInterrupt("Simulated Ctrl+C directly during lock acquisition")
            return self._real.acquire(*args, **kwargs)

        def release(self):
            self.release_calls += 1
            return self._real.release()

        def __enter__(self):
            return self.acquire()

        def __exit__(self, *args):
            return self.release()

    mock_lock = InterruptedLock(manager._lock)
    manager._lock = mock_lock

    coordinator = manager.synchronized_mutation(conn)
    from app.dsa.manager import CoordinatorState
    assert coordinator._state == CoordinatorState.CREATED

    # Inject KeyboardInterrupt on lock.acquire()
    mock_lock.raise_interrupt = True

    # 1. The exception propagates
    with pytest.raises(KeyboardInterrupt, match="Simulated Ctrl\\+C directly during lock acquisition"):
        with coordinator:
            pass

    mock_lock.raise_interrupt = False

    # 2. The coordinator transitions to COMPLETED
    assert coordinator._state == CoordinatorState.COMPLETED

    # 3. No unacquired lock is released
    assert mock_lock.acquire_calls == 1
    assert mock_lock.release_calls == 0

    # 4. Reusing the coordinator is rejected
    with pytest.raises(RuntimeError, match="cannot be reused or re-entered"):
        with coordinator:
            pass

    # 5. The manager lock remains usable
    assert manager._lock.acquire(blocking=True, timeout=1.0) is True
    manager._lock.release()

    # 6. A fresh coordinator can subsequently perform a valid mutation
    fresh_coord = manager.synchronized_mutation(conn)
    with fresh_coord as sync:
        conn.execute(
            """
            INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
            VALUES ('u_lock_test', 'locktest', 'locktest', 'lt@u.edu', 'lt@u.edu', 'h', 'Lock Test', 'CS', 3, '[]', '2026-11-18T00:00:00.000000Z', '2026-11-18T00:00:00.000000Z');
            """
        )
        sync.record_user_registered("u_lock_test", "locktest", "Lock Test")

    assert manager.search_prefix("locktest") == ["u_lock_test"]
    conn.close()





