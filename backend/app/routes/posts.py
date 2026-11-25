from flask import Blueprint, jsonify, request, g
from app.services.post_service import PostService
from app.utils.auth import login_required

posts_bp = Blueprint("posts", __name__)


@posts_bp.route("", methods=["POST"])
@login_required
def create_post():
    data = request.get_json() or {}
    content = data.get("content", "")
    try:
        post = PostService.create_post(
            user_id=g.current_user["user_id"],
            content=content,
        )
        return jsonify({
            "success": True,
            "message": "Post created successfully",
            "data": {
                "post_id": post["post_id"],
                "content": post["content"],
                "created_at": post["created_at"],
            }
        }), 201
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {"code": "VALIDATION_ERROR", "details": {}}
        }), 400


@posts_bp.route("/<post_id>", methods=["GET"])
@login_required
def get_post(post_id):
    post = PostService.get_post(post_id)
    if not post:
        return jsonify({
            "success": False,
            "message": "Post not found",
            "error": {"code": "NOT_FOUND", "details": {}}
        }), 404

    return jsonify({
        "success": True,
        "data": post
    }), 200


@posts_bp.route("/<post_id>", methods=["DELETE"])
@login_required
def delete_post(post_id):
    try:
        PostService.delete_post(post_id, user_id=g.current_user["user_id"])
        return jsonify({
            "success": True,
            "message": "Post deleted successfully"
        }), 200
    except PermissionError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {"code": "FORBIDDEN", "details": {}}
        }), 403
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {"code": "NOT_FOUND", "details": {}}
        }), 404

