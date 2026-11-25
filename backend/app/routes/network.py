from flask import Blueprint, jsonify, request, g
from app.db.connection import get_db
from app.services.network_service import NetworkService
from app.utils.auth import login_required

network_bp = Blueprint("network", __name__)


@network_bp.route("/<user_id>/mutuals", methods=["GET"])
@login_required
def get_mutuals(user_id):
    mutuals = NetworkService.get_mutual_connections(
        user_a=g.current_user["user_id"],
        user_b=user_id,
    )
    formatted_mutuals = []
    for m in mutuals:
        item = dict(m)
        item["id"] = m["user_id"]
        formatted_mutuals.append(item)
    return jsonify({
        "success": True,
        "data": {
            "user_id": user_id,
            "mutual_connections": formatted_mutuals,
            "count": len(mutuals),
        }
    }), 200


@network_bp.route("/<user_id>/degree", methods=["GET"])
@login_required
def get_degree(user_id):
    degree = NetworkService.get_degree(user_id)
    return jsonify({
        "success": True,
        "data": {
            "user_id": user_id,
            "degree": degree,
        }
    }), 200


@network_bp.route("/path", methods=["GET"])
@login_required
def get_path():
    target_user_id = request.args.get("targetUserId", type=str)
    if not target_user_id:
        return jsonify({
            "success": False,
            "message": "Query parameter 'targetUserId' is required",
            "error": {"code": "VALIDATION_ERROR", "details": {}}
        }), 400

    conn = get_db()
    canonical_target = NetworkService.resolve_canonical_user_id(target_user_id, conn)
    if not canonical_target:
        return jsonify({
            "success": False,
            "message": f"Student '{target_user_id}' not found.",
            "error": {"code": "RESOURCE_NOT_FOUND", "details": {}}
        }), 404

    path, distance = NetworkService.get_shortest_path(
        source_id=g.current_user["user_id"],
        target_id=canonical_target,
        conn=conn,
    )
    formatted_path = NetworkService.enrich_path(path, conn=conn)

    is_connected = path is not None and distance is not None and distance >= 0
    final_dist = distance if is_connected else None

    return jsonify({
        "success": True,
        "data": {
            "path": formatted_path if is_connected else None,
            "path_ids": path if is_connected else None,
            "distance": final_dist,
            "degree_of_separation": final_dist,
        }
    }), 200


@network_bp.route("/recommendations", methods=["GET"])
@login_required
def get_recommendations():
    limit = request.args.get("limit", default=10, type=int)
    recs = NetworkService.get_recommendations(
        user_id=g.current_user["user_id"],
        limit=limit,
    )
    formatted = []
    for r in recs:
        item = dict(r)
        item["id"] = r["user_id"]
        item["user"] = {**item}
        item["mutual_count"] = r["mutual_connections_count"]
        formatted.append(item)
    return jsonify({
        "success": True,
        "data": {
            "recommendations": formatted
        }
    }), 200
