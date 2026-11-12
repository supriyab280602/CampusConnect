from flask import Flask, jsonify
from flask_cors import CORS
from config import Config

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

