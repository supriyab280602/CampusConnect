from functools import wraps
from flask import g, jsonify, request
from app.db.connection import get_db
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.utils.helpers import hash_session_token

SESSION_COOKIE_NAME = "session_token"


def login_required(f):
    """
    Decorator for protected endpoints.
    Extracts session token from HttpOnly cookie or Authorization Bearer header,
    verifies active unexpired session, and attaches current user to Flask g.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get(SESSION_COOKIE_NAME)
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:].strip()

        if not token:
            return jsonify({
                "success": False,
                "message": "Authentication required. Please log in.",
                "error": {
                    "code": "UNAUTHORIZED",
                    "details": {}
                }
            }), 401

        conn = get_db()
        session_id = hash_session_token(token)
        session_record = SessionRepository.get_active_session(conn, session_id)
        if not session_record:
            return jsonify({
                "success": False,
                "message": "Invalid or expired session. Please log in again.",
                "error": {
                    "code": "SESSION_EXPIRED",
                    "details": {}
                }
            }), 401

        user = UserRepository.get_by_id(conn, session_record["user_id"])
        if not user:
            return jsonify({
                "success": False,
                "message": "User account no longer exists.",
                "error": {
                    "code": "USER_NOT_FOUND",
                    "details": {}
                }
            }), 401

        g.current_user = user
        g.session_token = token
        return f(*args, **kwargs)

    return decorated_function


def set_session_cookie(response, raw_token: str, max_age: int = 86400 * 7):
    """Set secure HttpOnly session cookie on the response."""
    import os
    is_prod = os.getenv("FLASK_ENV") == "production" or os.getenv("ENV") == "production"
    secure = is_prod or (request.is_secure if request else False)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        raw_token,
        max_age=max_age,
        httponly=True,
        samesite="Lax",
        secure=secure,
        path="/"
    )
    return response


def clear_session_cookie(response):
    """Clear session cookie from the client matching set_session_cookie attributes."""
    import os
    is_prod = os.getenv("FLASK_ENV") == "production" or os.getenv("ENV") == "production"
    secure = is_prod or (request.is_secure if request else False)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        "",
        expires=0,
        max_age=0,
        httponly=True,
        samesite="Lax",
        secure=secure,
        path="/"
    )
    return response
