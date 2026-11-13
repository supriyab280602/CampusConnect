import os
import sqlite3
from contextlib import contextmanager
from flask import current_app, g


def get_connection(db_path: str = None) -> sqlite3.Connection:
    """
    Create and configure an isolated SQLite database connection.
    Enforces foreign keys, WAL mode (for file databases), busy timeout,
    and returns rows with dict-like attribute access.
    """
    if db_path is None:
        if current_app:
            db_path = current_app.config.get("DATABASE_PATH")
        else:
            db_path = os.getenv(
                "DATABASE_PATH",
                os.path.join(os.path.dirname(__file__), "..", "..", "instance", "campusconnect.db")
            )

    # Ensure parent directory exists for file-backed databases
    if db_path != ":memory:" and not db_path.startswith("file:"):
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    # isolation_level=None enables explicit transaction management (BEGIN, COMMIT, ROLLBACK)
    conn = sqlite3.connect(db_path, timeout=5.0, isolation_level=None)
    conn.row_factory = sqlite3.Row

    # Enforce mandatory PRAGMAs per database specification CC-DAT-004 v1.2
    conn.execute("PRAGMA foreign_keys = ON;")
    if db_path != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")

    return conn


def get_db() -> sqlite3.Connection:
    """
    Retrieve or create a request-scoped database connection stored in Flask's g context.
    """
    if "db" not in g:
        g.db = get_connection()
    return g.db


def close_db(e=None) -> None:
    """
    Close the request-scoped database connection during Flask app context teardown.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


@contextmanager
def transaction(conn: sqlite3.Connection, immediate: bool = False):
    """
    Context manager for atomic transaction management.
    Uses BEGIN IMMEDIATE when immediate=True to acquire a write lock immediately,
    preventing concurrent write conflicts.
    Automatically commits on normal completion or rolls back on exception.
    """
    already_in_tx = conn.in_transaction
    if not already_in_tx:
        if immediate:
            conn.execute("BEGIN IMMEDIATE;")
        else:
            conn.execute("BEGIN;")
    try:
        yield conn
        if not already_in_tx and conn.in_transaction:
            conn.execute("COMMIT;")
    except Exception:
        if not already_in_tx and conn.in_transaction:
            conn.execute("ROLLBACK;")
        raise
