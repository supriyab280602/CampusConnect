import os
import sqlite3
import sys
import tempfile

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app import create_app
from app.db.schema import migrate_db


@pytest.fixture
def temp_db_path():
    """Create a temporary SQLite database file for testing file-backed persistence and restarts."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    for ext in ["", "-wal", "-shm"]:
        p = path + ext
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass


@pytest.fixture
def db_conn():
    """Create an in-memory SQLite connection with foreign keys enabled and schema migrated."""
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    migrate_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def app(temp_db_path):
    """Create an isolated test Flask application with a dedicated temporary database."""
    class TestConfig:
        TESTING = True
        SECRET_KEY = "test-secret-key"
        FRONTEND_ORIGIN = "http://localhost:5173"
        PORT = 5000
        DATABASE_PATH = temp_db_path
        AUTO_MIGRATE = True

    app = create_app(TestConfig)
    yield app


@pytest.fixture
def client(app):
    """
    Test client for Flask application.
    Automatically injects X-Requested-With on all requests so that the CSRF
    middleware behaves the same as the real browser fetch (which always sends this
    header via api.js).
    """
    base_client = app.test_client()

    class CsrfAwareClient:
        """Wraps Flask test client to inject X-Requested-With on every mutating request."""

        def __getattr__(self, name):
            return getattr(base_client, name)

        def _inject(self, kwargs):
            headers = dict(kwargs.get("headers") or {})
            headers.setdefault("X-Requested-With", "XMLHttpRequest")
            kwargs["headers"] = headers
            return kwargs

        def post(self, *args, **kwargs):
            return base_client.post(*args, **self._inject(kwargs))

        def put(self, *args, **kwargs):
            return base_client.put(*args, **self._inject(kwargs))

        def delete(self, *args, **kwargs):
            return base_client.delete(*args, **self._inject(kwargs))

        def patch(self, *args, **kwargs):
            return base_client.patch(*args, **self._inject(kwargs))

        def get(self, *args, **kwargs):
            return base_client.get(*args, **kwargs)

        def get_cookie(self, name):
            return base_client.get_cookie(name)

        def delete_cookie(self, name):
            return base_client.delete_cookie(name)

        def __enter__(self):
            base_client.__enter__()
            return self

        def __exit__(self, *args):
            return base_client.__exit__(*args)

    return CsrfAwareClient()
