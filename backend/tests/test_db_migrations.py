import sqlite3
import pytest
from app.db.connection import get_connection
from app.db.schema import (
    _split_sql_statements,
    apply_migration,
    get_schema_version,
    migrate_db,
    set_schema_version,
    TARGET_SCHEMA_VERSION,
)


def test_fresh_migration_sets_version():
    """Verify fresh in-memory database migrates to TARGET_SCHEMA_VERSION."""
    conn = sqlite3.connect(":memory:", isolation_level=None)
    assert get_schema_version(conn) == 0

    version = migrate_db(conn)
    assert version == TARGET_SCHEMA_VERSION
    assert get_schema_version(conn) == TARGET_SCHEMA_VERSION
    conn.close()


def test_repeated_migration_is_idempotent():
    """Verify calling migrate_db repeatedly on an existing database is safe and does not alter data."""
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON;")

    # First migration
    migrate_db(conn)
    assert get_schema_version(conn) == TARGET_SCHEMA_VERSION

    # Insert a user
    conn.execute(
        """
        INSERT INTO users (user_id, username, username_key, email, email_key, password_hash, full_name, programme, academic_year, skills, created_at, updated_at)
        VALUES ('u1', 'alice', 'alice', 'a@u.edu', 'a@u.edu', 'h', 'Alice S', 'CS', 3, '[]', '2026-11-13T00:00:00.000000Z', '2026-11-13T00:00:00.000000Z')
        """
    )

    # Second migration must be a no-op
    version = migrate_db(conn)
    assert version == TARGET_SCHEMA_VERSION

    # User record must still exist
    row = conn.execute("SELECT username FROM users WHERE user_id = 'u1';").fetchone()
    assert row[0] == "alice"
    conn.close()


def test_schema_version_getter_setter():
    """Verify get_schema_version and set_schema_version work with SQLite PRAGMA."""
    conn = sqlite3.connect(":memory:", isolation_level=None)
    assert get_schema_version(conn) == 0
    set_schema_version(conn, 42)
    assert get_schema_version(conn) == 42
    conn.close()


def test_migration_failure_atomicity_and_rollback(tmp_path):
    """
    Verify migration atomicity on a fresh SQLite database:
    A deliberately failing migration that creates at least one table and one index
    before failing on a subsequent DDL statement must:
    1. Roll back completely.
    2. Leave PRAGMA user_version at 0.
    3. Leave zero tables or indexes in sqlite_master.
    4. Keep the connection usable, and safe when closed and reopened.
    """
    db_file = str(tmp_path / "failing_migration.db")
    conn = get_connection(db_file)

    assert get_schema_version(conn) == 0

    failing_script = """
    -- Table 1: created successfully before subsequent error
    CREATE TABLE canary_table (
        id TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );

    -- Index 1: created successfully before subsequent error
    CREATE INDEX idx_canary_value ON canary_table(value);

    -- Subsequent DDL statement with deliberate syntax error
    FAILING_INVALID_SQL_STATEMENT_THAT_CAUSES_ERROR;
    """

    with pytest.raises(sqlite3.OperationalError):
        apply_migration(conn, 1, failing_script)

    # 1. PRAGMA user_version must remain 0
    assert get_schema_version(conn) == 0

    # 2. No tables or indexes from the failed migration remain in sqlite_master
    rows = conn.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'index');").fetchall()
    assert len(rows) == 0, f"Expected 0 schema objects remaining, found: {[dict(r) for r in rows]}"

    # 3. Database connection remains usable
    conn.execute("CREATE TABLE usable_probe (id INT PRIMARY KEY);")
    probe_row = conn.execute("SELECT name FROM sqlite_master WHERE name = 'usable_probe';").fetchone()
    assert probe_row is not None
    assert probe_row[0] == "usable_probe"

    # 4. Safe close and reopen verification
    conn.close()
    reopened_conn = get_connection(db_file)
    assert get_schema_version(reopened_conn) == 0
    reopened_rows = reopened_conn.execute("SELECT name FROM sqlite_master WHERE name = 'canary_table';").fetchall()
    assert len(reopened_rows) == 0
    reopened_conn.close()


def test_split_sql_statements_handles_quoted_strings_and_escapes():
    """Verify parser preserves semicolons inside single quotes, escaped quotes, and double quotes."""
    sql = """
    CREATE TABLE sample (
        id TEXT PRIMARY KEY,
        default_val TEXT DEFAULT 'prefix;middle;suffix'
    );
    INSERT INTO sample (id, default_val) VALUES ('1', 'it''s a ; complex; string');
    CREATE INDEX "idx;with;semicolons" ON sample(default_val);
    """
    stmts = _split_sql_statements(sql)
    assert len(stmts) == 3
    assert "default_val TEXT DEFAULT 'prefix;middle;suffix'" in stmts[0]
    assert "'it''s a ; complex; string'" in stmts[1]
    assert '"idx;with;semicolons"' in stmts[2]


def test_split_sql_statements_handles_comments_and_multiline():
    """Verify parser strips single-line and multiline comments, ignoring semicolons within comments."""
    sql = """
    -- Single line comment with semicolon; and details;
    /* Multiline block comment
       with multiple; semicolons; inside
    */
    CREATE TABLE multiline_demo (
        id TEXT PRIMARY KEY, -- inline comment with semicolon;
        description TEXT
    );
    /* Block comment at end of script */
    """
    stmts = _split_sql_statements(sql)
    assert len(stmts) == 1
    assert "CREATE TABLE multiline_demo" in stmts[0]
    assert "description TEXT" in stmts[0]


def test_split_sql_statements_end_to_end_execution():
    """Verify complex parsed statements execute cleanly against SQLite engine."""
    sql = """
    -- Setup table
    CREATE TABLE items (
        id TEXT PRIMARY KEY,
        tags TEXT DEFAULT 'tag1;tag2;tag3'
    );
    /* Insert data */
    INSERT INTO items (id, tags) VALUES ('i1', 'alpha;beta');
    INSERT INTO items (id, tags) VALUES ('i2', 'gamma;''delta'';epsilon');
    """
    conn = get_connection(":memory:")
    stmts = _split_sql_statements(sql)
    assert len(stmts) == 3
    with conn:
        for s in stmts:
            conn.execute(s)

    rows = conn.execute("SELECT id, tags FROM items ORDER BY id;").fetchall()
    assert len(rows) == 2
    assert rows[0]["tags"] == "alpha;beta"
    assert rows[1]["tags"] == "gamma;'delta';epsilon"
    conn.close()


def test_split_sql_statements_handles_escaped_double_quotes_and_brackets():
    """Verify parser preserves escaped double quotes, backticks, and square bracket identifiers."""
    sql = """
    CREATE TABLE "table""name;semi" (
        "col""1;semi" TEXT,
        `col;backtick` TEXT,
        [col;bracket] TEXT
    );
    CREATE INDEX [idx;bracket] ON "table""name;semi"([col;bracket]);
    """
    stmts = _split_sql_statements(sql)
    assert len(stmts) == 2
    assert '"table""name;semi"' in stmts[0]
    assert "[col;bracket]" in stmts[0]
    assert "[idx;bracket]" in stmts[1]

    # Verify execution against SQLite
    conn = get_connection(":memory:")
    with conn:
        for s in stmts:
            conn.execute(s)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    assert 'table"name;semi' in [t["name"] for t in tables]
    conn.close()


def test_split_sql_statements_handles_triggers_with_internal_semicolons():
    """Verify parser treats triggers with internal BEGIN...END; semicolons as atomic statements."""
    sql = """
    CREATE TABLE audit_source (id INT PRIMARY KEY, name TEXT);
    CREATE TABLE audit_log (log_msg TEXT);
    CREATE TRIGGER trg_audit AFTER INSERT ON audit_source
    BEGIN
        INSERT INTO audit_log VALUES ('new: ' || new.name);
        UPDATE audit_source SET name = UPPER(new.name) WHERE id = new.id;
    END;
    """
    stmts = _split_sql_statements(sql)
    assert len(stmts) == 3
    assert "CREATE TRIGGER trg_audit" in stmts[2]
    assert "END;" in stmts[2]

    # Verify end-to-end trigger execution in SQLite
    conn = get_connection(":memory:")
    with conn:
        for s in stmts:
            conn.execute(s)
        conn.execute("INSERT INTO audit_source VALUES (1, 'alice');")

    log_entry = conn.execute("SELECT log_msg FROM audit_log;").fetchone()[0]
    updated_name = conn.execute("SELECT name FROM audit_source WHERE id = 1;").fetchone()[0]
    assert log_entry == "new: alice"
    assert updated_name == "ALICE"
    conn.close()


def test_split_sql_statements_handles_multiple_statements_on_same_line():
    """Verify parser correctly separates multiple statements on a single line."""
    sql = "CREATE TABLE inline1 (id INT); CREATE TABLE inline2 (id INT); CREATE TABLE inline3 (id INT);"
    stmts = _split_sql_statements(sql)
    assert len(stmts) == 3
    assert "inline1" in stmts[0]
    assert "inline2" in stmts[1]
    assert "inline3" in stmts[2]
