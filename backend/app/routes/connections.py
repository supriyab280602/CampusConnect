from flask import Blueprint, jsonify, request, g
from app.services.connection_service import ConnectionService
from app.utils.auth import login_required

connections_bp = Blueprint("connections", __name__)


@connections_bp.route("/requests", methods=["POST"])
@login_required
def send_request():
    data = request.get_json() or {}
    receiver_id = data.get("receiver_id") or data.get("recipient_id")
    if not receiver_id:
        return jsonify({
            "success": False,
            "message": "receiver_id is required",
            "error": {"code": "VALIDATION_ERROR", "details": {}}
        }), 400

    if receiver_id == g.current_user["user_id"]:
        return jsonify({
            "success": False,
            "message": "Cannot send connection request to self",
            "error": {"code": "VALIDATION_ERROR", "details": {}}
        }), 400

    try:
        result = ConnectionService.send_request(
            sender_id=g.current_user["user_id"],
            receiver_id=receiver_id,
        )
        req_data = {
            "id": result["request_id"],
            "request_id": result["request_id"],
            "status": result["status"],
        }
        return jsonify({
            "success": True,
            "message": "Connection request sent",
            "data": {
                **req_data,
                "request": req_data,
            }
        }), 201
    except ValueError as e:
        msg = str(e)
        is_conflict = "already" in msg.lower() or "pending" in msg.lower() or "exists" in msg.lower()
        return jsonify({
            "success": False,
            "message": msg,
            "error": {"code": "CONFLICT" if is_conflict else "VALIDATION_ERROR", "details": {}}
        }), 409 if is_conflict else 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {"code": "CONFLICT", "details": {}}
        }), 409


@connections_bp.route("/requests/received", methods=["GET"])
@login_required
def received_requests():
    requests = ConnectionService.get_received_requests(g.current_user["user_id"])
    formatted = []
    for r in requests:
        item = dict(r)
        item["id"] = r["request_id"]
        formatted.append(item)
    return jsonify({
        "success": True,
        "data": {
            "requests": formatted
        }
    }), 200


@connections_bp.route("/requests/sent", methods=["GET"])
@login_required
def sent_requests():
    requests = ConnectionService.get_sent_requests(g.current_user["user_id"])
    formatted = []
    for r in requests:
        item = dict(r)
        item["id"] = r["request_id"]
        formatted.append(item)
    return jsonify({
        "success": True,
        "data": {
            "requests": formatted
        }
    }), 200


@connections_bp.route("/requests/<request_id>/accept", methods=["POST"])
@login_required
def accept_request(request_id):
    try:
        ConnectionService.accept_request(
            request_id=request_id,
            receiver_id=g.current_user["user_id"]
        )
        return jsonify({
            "success": True,
            "message": "Connection accepted"
        }), 200
    except LookupError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {"code": "RESOURCE_NOT_FOUND", "details": {}}
        }), 404
    except PermissionError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {"code": "FORBIDDEN", "details": {}}
        }), 403
    except ValueError as e:
        msg = str(e)
        is_conflict = "status" in msg.lower() or "pending" in msg.lower() or "already" in msg.lower()
        return jsonify({
            "success": False,
            "message": msg,
            "error": {"code": "CONFLICT" if is_conflict else "BAD_REQUEST", "details": {}}
        }), 409 if is_conflict else 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {"code": "CONFLICT", "details": {}}
        }), 409


@connections_bp.route("/requests/<request_id>/reject", methods=["POST"])
@login_required
def reject_request(request_id):
    try:
        ConnectionService.reject_request(
            request_id=request_id,
            receiver_id=g.current_user["user_id"]
        )
        return jsonify({
            "success": True,
            "message": "Connection request rejected"
        }), 200
    except LookupError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {"code": "RESOURCE_NOT_FOUND", "details": {}}
        }), 404
    except PermissionError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {"code": "FORBIDDEN", "details": {}}
        }), 403
    except ValueError as e:
        msg = str(e)
        is_conflict = "status" in msg.lower() or "pending" in msg.lower() or "already" in msg.lower()
        return jsonify({
            "success": False,
            "message": msg,
            "error": {"code": "CONFLICT" if is_conflict else "BAD_REQUEST", "details": {}}
        }), 409 if is_conflict else 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {"code": "CONFLICT", "details": {}}
        }), 409


@connections_bp.route("/requests/<request_id>/cancel", methods=["POST"])
@login_required
def cancel_request(request_id):
    try:
        ConnectionService.cancel_request(
            request_id=request_id,
            sender_id=g.current_user["user_id"]
        )
        return jsonify({
            "success": True,
            "message": "Connection request cancelled"
        }), 200
    except LookupError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {"code": "RESOURCE_NOT_FOUND", "details": {}}
        }), 404
    except PermissionError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {"code": "FORBIDDEN", "details": {}}
        }), 403
    except ValueError as e:
        msg = str(e)
        is_conflict = "status" in msg.lower() or "pending" in msg.lower() or "already" in msg.lower()
        return jsonify({
            "success": False,
            "message": msg,
            "error": {"code": "CONFLICT" if is_conflict else "BAD_REQUEST", "details": {}}
        }), 409 if is_conflict else 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {"code": "CONFLICT", "details": {}}
        }), 409


@connections_bp.route("", methods=["GET"])
@login_required
def list_connections():
    conns = ConnectionService.list_connections(g.current_user["user_id"])
    formatted = []
    for c in conns:
        item = dict(c)
        user_info = c.get("user", {})
        item["user_id"] = user_info.get("user_id")
        item["id"] = user_info.get("user_id")
        formatted.append(item)
    return jsonify({
        "success": True,
        "data": {
            "connections": formatted
        }
    }), 200


@connections_bp.route("/<user_id>", methods=["DELETE"])
@login_required
def remove_connection(user_id):
    try:
        ConnectionService.remove_connection(g.current_user["user_id"], user_id)
        return jsonify({
            "success": True,
            "message": "Connection removed successfully"
        }), 200
    except LookupError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {"code": "RESOURCE_NOT_FOUND", "details": {}}
        }), 404
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {"code": "BAD_REQUEST", "details": {}}
        }), 400
