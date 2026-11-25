from flask import Blueprint, jsonify, request, g
from app.services.auth_service import AuthService
from app.utils.auth import login_required, set_session_cookie, clear_session_cookie

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    try:
        user = AuthService.register_user(
            username=data.get("username", ""),
            email=data.get("email", ""),
            password=data.get("password", ""),
            full_name=data.get("full_name", ""),
            programme=data.get("programme", "General"),
            academic_year=data.get("academic_year", 1),
            skills=data.get("skills", []),
            bio=data.get("bio", None),
        )
        # Automatically create session so user is logged in
        raw_token, _ = AuthService.login(user["username"], data.get("password", ""))
        user_info = {
            "id": user["user_id"],
            "user_id": user["user_id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "email": user["email"],
        }
        resp = jsonify({
            "success": True,
            "message": "Account created successfully",
            "data": {
                **user_info,
                "user": user_info,
            }
        })
        return set_session_cookie(resp, raw_token), 201
    except ValueError as e:
        msg = str(e)
        is_conflict = "already" in msg.lower() or "taken" in msg.lower() or "registered" in msg.lower()
        return jsonify({
            "success": False,
            "message": msg,
            "error": {
                "code": "DUPLICATE_RESOURCE" if is_conflict else "VALIDATION_ERROR",
                "details": {}
            }
        }), 409 if is_conflict else 400


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    identifier = data.get("username") or data.get("email") or data.get("identifier") or ""
    password = data.get("password", "")
    try:
        token, user = AuthService.login(
            username_or_email=identifier,
            password=password,
        )
        user_info = {
            "id": user["user_id"],
            "user_id": user["user_id"],
            "username": user["username"],
            "full_name": user["full_name"],
        }
        resp = jsonify({
            "success": True,
            "message": "Login successful",
            "data": {
                **user_info,
                "user": user_info,
            }
        })
        return set_session_cookie(resp, token), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "error": {
                "code": "AUTHENTICATION_FAILED",
                "details": {}
            }
        }), 401


@auth_bp.route("/logout", methods=["POST"])
def logout():
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
    if token:
        try:
            AuthService.logout(token)
        except Exception:
            pass
    resp = jsonify({
        "success": True,
        "message": "Logged out successfully"
    })
    return clear_session_cookie(resp), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    user_info = {
        "id": g.current_user["user_id"],
        "user_id": g.current_user["user_id"],
        "username": g.current_user["username"],
        "full_name": g.current_user["full_name"],
        "email": g.current_user["email"],
        "programme": g.current_user["programme"],
        "academic_year": g.current_user["academic_year"],
    }
    return jsonify({
        "success": True,
        "data": {
            **user_info,
            "user": user_info,
        }
    }), 200
