import re
import sqlite3
from typing import Optional
from app.db.connection import get_connection, transaction

TARGET_SCHEMA_VERSION = 1

V1_SCHEMA_SQL = """
-- 1. Users table (CC-DAT-004 v1.2 Section 4.1)
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    username_key TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    email_key TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    programme TEXT NOT NULL,
    academic_year INTEGER NOT NULL,
    bio TEXT,
    skills TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 2. Connection requests table (CC-DAT-004 v1.2 Section 4.2)
CREATE TABLE IF NOT EXISTS connection_requests (
    request_id TEXT PRIMARY KEY,
    sender_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    receiver_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK(status IN ('pending', 'accepted', 'rejected', 'cancelled')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (sender_id != receiver_id)
);

-- Partial index for pending requests (only one pending request per direction)
CREATE UNIQUE INDEX IF NOT EXISTS idx_connection_requests_pending
    ON connection_requests(sender_id, receiver_id)
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_connection_requests_receiver
    ON connection_requests(receiver_id, status, created_at);

CREATE INDEX IF NOT EXISTS idx_connection_requests_sender
    ON connection_requests(sender_id, status, created_at);

-- 3. Accepted connections table (CC-DAT-004 v1.2 Section 4.3)
CREATE TABLE IF NOT EXISTS connections (
    connection_id TEXT PRIMARY KEY,
    user_id_low TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    user_id_high TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    CHECK (user_id_low < user_id_high),
    UNIQUE (user_id_low, user_id_high)
);

CREATE INDEX IF NOT EXISTS idx_connections_low
    ON connections(user_id_low);

CREATE INDEX IF NOT EXISTS idx_connections_high
    ON connections(user_id_high);

-- 4. Posts table (CC-DAT-004 v1.2 Section 4.4)
CREATE TABLE IF NOT EXISTS posts (
    post_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_posts_user_created
    ON posts(user_id, created_at, post_id);

CREATE INDEX IF NOT EXISTS idx_posts_created
    ON posts(created_at, post_id);

-- 5. User sessions table (CC-DAT-004 v1.2 Section 4.5)
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    csrf_token_hash TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user
    ON user_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_user_sessions_expires
    ON user_sessions(expires_at);
"""


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Retrieve the current schema version from SQLite PRAGMA user_version."""
    cursor = conn.execute("PRAGMA user_version;")
    row = cursor.fetchone()
    return int(row[0]) if row else 0


def set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    """Update SQLite PRAGMA user_version."""
    conn.execute(f"PRAGMA user_version = {int(version)};")


def _is_comment_only(text: str) -> bool:
    """Check if a string contains only whitespace and/or SQL comments."""
    cleaned = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"--[^\n]*", "", cleaned)
    return len(cleaned.strip()) == 0


def _split_sql_statements(sql: str) -> list[str]:
    """
    Split a SQL script into individual executable statements using Python's
    built-in `sqlite3.complete_statement()` interface (backed by the SQLite
    C library's `sqlite3_complete()` API).

    Accurately handles all SQLite statement boundary constructs:
    - Semicolons inside single-quoted strings ('...') and escaped quotes ('')
    - Semicolons inside double-quoted identifiers ("...") including escaped quotes ("")
    - SQLite backtick-quoted identifiers (`...`)
    - SQLite square-bracket quoted identifiers ([...])
    - Single-line (--) and multi-line (/* ... */) comments containing semicolons
    - Multi-line statements spanning arbitrary newlines
    - Multi-statement lines (multiple statements on a single line)
    - Full support for CREATE TRIGGER statements containing internal semicolons
      between BEGIN and END;
    """
    statements = []
    buffer = ""

    for char in sql:
        buffer += char
        if char == ";" and sqlite3.complete_statement(buffer):
            stmt = buffer.strip()
            if stmt and not _is_comment_only(stmt):
                statements.append(stmt)
            buffer = ""

    leftover = buffer.strip()
    if leftover and not _is_comment_only(leftover):
        statements.append(leftover)

    return statements


def apply_migration(conn: sqlite3.Connection, target_version: int, sql_script: str) -> None:
    """
    Atomically apply a versioned migration script.
    Executes all DDL statements in an immediate write transaction.
    If any statement fails, the transaction is rolled back, leaving
    no partial tables or indexes in sqlite_master, and preserving the
    previous PRAGMA user_version.
    """
    with transaction(conn, immediate=True):
        statements = _split_sql_statements(sql_script)
        for stmt in statements:
            conn.execute(stmt)
        set_schema_version(conn, target_version)


def migrate_db(conn: sqlite3.Connection) -> int:
    """
    Apply versioned migrations up to TARGET_SCHEMA_VERSION.
    Idempotent and safe to rerun on an existing database.
    Returns the final schema version.
    """
    current_version = get_schema_version(conn)

    if current_version < 1:
        apply_migration(conn, 1, V1_SCHEMA_SQL)
        current_version = 1

    return current_version


def init_db(db_path: Optional[str] = None) -> int:
    """
    Open connection, apply required migrations, and return the schema version.
    """
    conn = get_connection(db_path)
    try:
        version = migrate_db(conn)
        return version
    finally:
        conn.close()
