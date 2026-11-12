from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def get_health():
    return jsonify({
        "success": True,
        "message": "CampusConnect API is healthy",
        "data": {
            "status": "healthy",
            "service": "campusconnect-backend",
            "version": "1.0.0"
        }
    }), 200

