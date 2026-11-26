import os

from flask import Flask, jsonify
from flask_cors import CORS

from app.db.connection import close_db, get_connection
from app.db.schema import migrate_db
from app.dsa import get_dsa_manager
from app.dsa.exceptions import IndexDegradedCommittedError, IndexUnavailableError
from app.repositories.session_repository import SessionRepository
from config import Config, validate_production_secret


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Validate production secret hardening (unless in test mode)
    env = (app.config.get("ENV") or os.getenv("FLASK_ENV") or os.getenv("ENV") or "development").lower()
    if not app.config.get("TESTING", False):
        validate_production_secret(str(app.config.get("SECRET_KEY") or ""), env)

    # Configure CORS origins: strict allowlist. Dev origins only in non-production.
    cors_origins = set()

    # Localhost origins only in development/test environments
    if env not in ("production", "prod"):
        dev_origins = {
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        }
        cors_origins.update(dev_origins)

    # Explicit origin(s) from configuration / environment (CORS_ORIGINS takes precedence over FRONTEND_ORIGIN)
    raw_origin = (
        getattr(config_class, "CORS_ORIGINS", None)
        or os.getenv("CORS_ORIGINS", "")
        or getattr(config_class, "FRONTEND_ORIGIN", None)
        or os.getenv("FRONTEND_ORIGIN", "")
    )
    if isinstance(raw_origin, list):
        origin_items = raw_origin
    elif isinstance(raw_origin, str) and raw_origin.strip():
        origin_items = [o.strip() for o in raw_origin.split(",") if o.strip()]
    else:
        origin_items = []

    for item in origin_items:
        clean = item.strip().rstrip("/")
        if clean:
            cors_origins.add(clean)

    CORS(
        app,
        origins=sorted(cors_origins),
        supports_credentials=True,
        allow_headers=["Content-Type", "Accept", "X-Requested-With", "Authorization"],
        expose_headers=["X-Session-Token"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    app.teardown_appcontext(close_db)

    # Auto-migrate database on application startup if configured
    if app.config.get("AUTO_MIGRATE", True):
        db_path = app.config.get("DATABASE_PATH")
        conn = get_connection(db_path)
        try:
            migrate_db(conn)
            SessionRepository.delete_expired_sessions(conn)
            # Reconstruct in-memory Graph and Trie indices from persistent SQLite
            get_dsa_manager().initialize(conn)
        finally:
            conn.close()

    # Register API Blueprints
    from app.routes.auth import auth_bp
    from app.routes.connections import connections_bp
    from app.routes.feed import feed_bp
    from app.routes.health import health_bp
    from app.routes.network import network_bp
    from app.routes.posts import posts_bp
    from app.routes.search import search_bp
    from app.routes.users import users_bp

    app.register_blueprint(health_bp, url_prefix="/api/v1")
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(users_bp, url_prefix="/api/v1/users")
    app.register_blueprint(connections_bp, url_prefix="/api/v1/connections")
    app.register_blueprint(posts_bp, url_prefix="/api/v1/posts")
    app.register_blueprint(feed_bp, url_prefix="/api/v1/feed")
    app.register_blueprint(search_bp, url_prefix="/api/v1/search")
    app.register_blueprint(network_bp, url_prefix="/api/v1/network")

    @app.errorhandler(IndexUnavailableError)
    def handle_index_unavailable(e):
        return jsonify({
            "success": False,
            "message": "Search and network indices are temporarily unavailable",
            "error": {
                "code": "INDEX_UNAVAILABLE",
                "details": {}
            }
        }), 503

    @app.errorhandler(IndexDegradedCommittedError)
    def handle_index_degraded_committed(e):
        return jsonify({
            "success": False,
            "message": "Data was saved, but in-memory index synchronization failed",
            "error": {
                "code": "INDEX_DEGRADED_COMMITTED",
                "details": {}
            }
        }), 500

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "success": False,
            "message": "Resource not found",
            "error": {
                "code": "RESOURCE_NOT_FOUND",
                "details": {}
            }
        }), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({
            "success": False,
            "message": "An internal server error occurred",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "details": {}
            }
        }), 500

    return app
