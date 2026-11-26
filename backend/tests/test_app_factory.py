from app import create_app
from app.db.connection import get_connection
from app.db.schema import migrate_db
from app.dsa.exceptions import IndexDegradedCommittedError, IndexUnavailableError
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository


def test_production_cors_excludes_hardcoded_render_origin(temp_db_path, monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://custom.example.com")

    class ProdConfig:
        ENV = "production"
        TESTING = False
        SECRET_KEY = "a" * 32
        FRONTEND_ORIGIN = "http://localhost:5173"
        DATABASE_PATH = temp_db_path
        AUTO_MIGRATE = True

    app = create_app(ProdConfig)
    client = app.test_client()

    disallowed = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://campusconnect-frontend-bzwf.onrender.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert disallowed.headers.get("Access-Control-Allow-Origin") is None

    allowed = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://custom.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert allowed.headers.get("Access-Control-Allow-Origin") == "https://custom.example.com"


def test_dsa_error_handlers_return_structured_responses(app):
    @app.route("/test-index-unavailable")
    def raise_unavailable():
        raise IndexUnavailableError("index rebuilding")

    @app.route("/test-index-degraded")
    def raise_degraded():
        raise IndexDegradedCommittedError("db committed, index failed")

    client = app.test_client()

    resp_503 = client.get("/test-index-unavailable")
    assert resp_503.status_code == 503
    data_503 = resp_503.get_json()
    assert data_503["success"] is False
    assert data_503["error"]["code"] == "INDEX_UNAVAILABLE"

    resp_500 = client.get("/test-index-degraded")
    assert resp_500.status_code == 500
    data_500 = resp_500.get_json()
    assert data_500["success"] is False
    assert data_500["error"]["code"] == "INDEX_DEGRADED_COMMITTED"


def test_startup_purges_expired_sessions(temp_db_path):
    conn = get_connection(temp_db_path)
    try:
        migrate_db(conn)
        user = UserRepository.create_user(
            conn,
            username="expireduser",
            email="expired@example.edu",
            password_hash="hashed",
            full_name="Test User",
            programme="CS",
            academic_year=2,
            skills=["Python"],
        )
        SessionRepository.create_session(
            conn,
            user_id=user["user_id"],
            session_id="expired-session-hash",
            expires_at="2000-01-01T00:00:00Z",
        )
        SessionRepository.create_session(
            conn,
            user_id=user["user_id"],
            session_id="active-session-hash",
            expires_at="2099-01-01T00:00:00Z",
        )
    finally:
        conn.close()

    class TestConfig:
        TESTING = True
        SECRET_KEY = "test-secret-key"
        FRONTEND_ORIGIN = "http://localhost:5173"
        DATABASE_PATH = temp_db_path
        AUTO_MIGRATE = True

    create_app(TestConfig)

    verify_conn = get_connection(temp_db_path)
    try:
        assert SessionRepository.get_by_id(verify_conn, "expired-session-hash") is None
        assert SessionRepository.get_by_id(verify_conn, "active-session-hash") is not None
    finally:
        verify_conn.close()
