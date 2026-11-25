from flask import Blueprint, jsonify, request, g
from app.services.user_service import UserService
from app.utils.auth import login_required

users_bp = Blueprint("users", __name__)


@users_bp.route("/<user_id>", methods=["GET"])
@login_required
def get_user(user_id):
    profile = UserService.get_public_profile(user_id)
    if not profile:
        return jsonify({
            "success": False,
            "message": "User not found",
            "error": {
                "code": "RESOURCE_NOT_FOUND",
                "details": {}
            }
        }), 404

    resp_data = dict(profile)
    resp_data["id"] = profile["user_id"]
    return jsonify({
        "success": True,
        "data": {
            **resp_data,
            "user": resp_data,
        }
    }), 200


@users_bp.route("/me", methods=["PUT"])
@login_required
def update_me():
    data = request.get_json() or {}
    try:
        updated = UserService.update_profile(
            user_id=g.current_user["user_id"],
            full_name=data.get("full_name"),
            programme=data.get("programme"),
            academic_year=data.get("academic_year"),
            bio=data.get("bio"),
            skills=data.get("skills"),
        )
        resp_data = dict(updated)
        resp_data["id"] = updated["user_id"]
        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "data": {
                **resp_data,
                "user": resp_data,
            }
        }), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {
                "code": "VALIDATION_ERROR",
                "details": {}
            }
        }), 400
