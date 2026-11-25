import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config, validate_production_secret
from app.db.connection import close_db, get_connection
from app.db.schema import migrate_db
from app.dsa import get_dsa_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Validate production secret hardening (unless in test mode)
    env = (app.config.get("ENV") or os.getenv("FLASK_ENV") or os.getenv("ENV") or "development").lower()
    if not app.config.get("TESTING", False):
        validate_production_secret(str(app.config.get("SECRET_KEY") or ""), env)

    # Configure CORS origins: strict allowlist of explicit production origins and local dev
    cors_origins = set()

    # Preserve local development origins
    dev_origins = {
        "http://localhost:5173",
        "http://localhost:5173/",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5173/",
        "http://localhost:3000",
        "http://localhost:3000/",
    }
    cors_origins.update(dev_origins)

    # Explicit production frontend origin(s) from configuration / environment
    raw_origin = getattr(config_class, "FRONTEND_ORIGIN", None) or os.getenv("FRONTEND_ORIGIN", "")
    if isinstance(raw_origin, list):
        origin_items = raw_origin
    elif isinstance(raw_origin, str) and raw_origin.strip():
        origin_items = [o.strip() for o in raw_origin.split(",") if o.strip()]
    else:
        origin_items = []

    for item in origin_items:
        clean = item.rstrip("/")
        if clean:
            cors_origins.add(clean)
            cors_origins.add(f"{clean}/")

    CORS(
        app,
        origins=sorted(list(cors_origins)),
        supports_credentials=True,
        allow_headers=["Content-Type", "Accept", "X-Requested-With", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    app.teardown_appcontext(close_db)

    # Auto-migrate database on application startup if configured
    if app.config.get("AUTO_MIGRATE", True):
        db_path = app.config.get("DATABASE_PATH")
        conn = get_connection(db_path)
        try:
            migrate_db(conn)
            # Reconstruct in-memory Graph and Trie indices from persistent SQLite
            get_dsa_manager().initialize(conn)
        finally:
            conn.close()

    # Register API Blueprints
    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.connections import connections_bp
    from app.routes.posts import posts_bp
    from app.routes.feed import feed_bp
    from app.routes.search import search_bp
    from app.routes.network import network_bp

    app.register_blueprint(health_bp, url_prefix="/api/v1")
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(users_bp, url_prefix="/api/v1/users")
    app.register_blueprint(connections_bp, url_prefix="/api/v1/connections")
    app.register_blueprint(posts_bp, url_prefix="/api/v1/posts")
    app.register_blueprint(feed_bp, url_prefix="/api/v1/feed")
    app.register_blueprint(search_bp, url_prefix="/api/v1/search")
    app.register_blueprint(network_bp, url_prefix="/api/v1/network")

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
