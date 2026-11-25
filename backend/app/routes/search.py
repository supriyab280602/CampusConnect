from flask import Blueprint, jsonify, request, g
from app.services.search_service import SearchService
from app.utils.auth import login_required

search_bp = Blueprint("search", __name__)


@search_bp.route("/users", methods=["GET"])
@login_required
def search_users():
    q = request.args.get("q", default=None, type=str)
    limit = request.args.get("limit", default=10, type=int)

    if q is None:
        return jsonify({
            "success": False,
            "message": "Query parameter 'q' is required",
            "error": {"code": "VALIDATION_ERROR", "details": {}}
        }), 400

    if not q.strip():
        return jsonify({
            "success": True,
            "data": {
                "results": []
            }
        }), 200

    results = SearchService.search_users(query=q, limit=limit)
    return jsonify({
        "success": True,
        "data": {
            "results": results
        }
    }), 200
