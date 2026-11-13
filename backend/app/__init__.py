from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from app.db.connection import close_db, get_connection
from app.db.schema import migrate_db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(
        app,
        origins=[config_class.FRONTEND_ORIGIN],
        supports_credentials=True,
        allow_headers=["Content-Type", "Accept", "X-Requested-With"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    app.teardown_appcontext(close_db)

    # Auto-migrate database on application startup if configured
    if app.config.get("AUTO_MIGRATE", True):
        db_path = app.config.get("DATABASE_PATH")
        conn = get_connection(db_path)
        try:
            migrate_db(conn)
        finally:
            conn.close()

    from app.routes.health import health_bp
    app.register_blueprint(health_bp, url_prefix="/api/v1")

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

    return app
