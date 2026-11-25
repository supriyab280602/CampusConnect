"""
Integration and persistence tests: verifying in-memory graph and Trie reconstruction across restarts.
"""

from app.db.connection import get_connection
from app.db.schema import migrate_db
from app.dsa.manager import DSAManager


def test_dsa_reconstruction_across_process_restart(tmp_path):
    """
    Verify that in-memory graph and Trie are completely and accurately
    reconstructed from persistent SQLite records upon application restart.
    """
    db_file = str(tmp_path / "restart_test.db")

    # Step 1: Session 1 - Seed database
    conn1 = get_connection(db_file)
    migrate_db(conn1)

    # Insert 3 users
    conn1.execute(
        """
        INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
        VALUES
        ('u1', 'alice', 'alice', 'a@u.edu', 'a@u.edu', 'h', 'Alice Cooper', 'CS', 3, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z'),
        ('u2', 'bob', 'bob', 'b@u.edu', 'b@u.edu', 'h', 'Bob Marley', 'CS', 3, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z'),
        ('u3', 'charlie', 'charlie', 'c@u.edu', 'c@u.edu', 'h', 'Charlie Chaplin', 'CS', 3, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z');
        """
    )
    # Insert connection: u1 - u2, u2 - u3
    conn1.execute(
        """
        INSERT INTO connections (connection_id, user_id_low, user_id_high, created_at)
        VALUES
        ('c1', 'u1', 'u2', '2026-11-13T00:00:00.000000Z'),
        ('c2', 'u2', 'u3', '2026-11-13T00:00:00.000000Z');
        """
    )

    # Step 2: "Process Shutdown" - Close connection
    conn1.close()

    # Step 3: "Process Restart" - Fresh DSAManager and fresh database connection
    manager = DSAManager()
    assert manager.is_ready() is False

    conn2 = get_connection(db_file)
    manager.initialize(conn2)
    assert manager.is_ready() is True

    # Step 4: Verify reconstructed graph state
    assert manager.get_degree("u1") == 1
    assert manager.get_degree("u2") == 2
    assert manager.get_degree("u3") == 1

    path, dist = manager.get_shortest_path("u1", "u3")
    assert path == ["u1", "u2", "u3"]
    assert dist == 2

    assert manager.get_mutual_connections("u1", "u3") == ["u2"]

    # Step 5: Verify reconstructed Trie state
    assert manager.search_prefix("ali") == ["u1"]
    assert manager.search_prefix("coop") == ["u1"]
    assert manager.search_prefix("bob") == ["u2"]
    assert manager.search_prefix("marl") == ["u2"]
    assert manager.search_prefix("chap") == ["u3"]

    conn2.close()
