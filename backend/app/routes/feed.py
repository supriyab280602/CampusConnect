from flask import Blueprint, jsonify, request, g
from app.services.feed_service import FeedService
from app.utils.auth import login_required

feed_bp = Blueprint("feed", __name__)


@feed_bp.route("", methods=["GET"])
@login_required
def get_feed():
    limit = request.args.get("limit", default=10, type=int)
    cursor = request.args.get("cursor", default=None, type=str)

    try:
        feed_data = FeedService.get_feed(
            user_id=g.current_user["user_id"],
            limit=limit,
            cursor_str=cursor,
        )
        return jsonify({
            "success": True,
            "data": feed_data
        }), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {"code": "VALIDATION_ERROR", "details": {}}
        }), 400
