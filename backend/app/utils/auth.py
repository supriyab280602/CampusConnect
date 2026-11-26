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

    CSRF mitigation: state-changing requests (POST, PUT, DELETE, PATCH) must include
    either an Authorization: Bearer token (which an attacker page cannot inject from
    a different origin) OR the X-Requested-With header (indicating a fetch/XHR call).
    Plain form-based cross-site requests cannot set custom headers.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get(SESSION_COOKIE_NAME)
        using_bearer = False
        if not token or token in ("undefined", "null", ""):
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:].strip()
                using_bearer = True

        if not token or token in ("undefined", "null", ""):
            return jsonify({
                "success": False,
                "message": "Authentication required. Please log in.",
                "error": {
                    "code": "UNAUTHORIZED",
                    "details": {}
                }
            }), 401

        # CSRF check: for cookie-based sessions on state-changing methods,
        # require X-Requested-With to confirm this is a programmatic fetch request.
        # Bearer-authenticated requests are exempt (token itself proves intent).
        if not using_bearer and request.method in ("POST", "PUT", "DELETE", "PATCH"):
            xrw = request.headers.get("X-Requested-With", "")
            if xrw.lower() != "xmlhttprequest":
                return jsonify({
                    "success": False,
                    "message": "CSRF validation failed.",
                    "error": {
                        "code": "FORBIDDEN",
                        "details": {}
                    }
                }), 403

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
    """Set secure HttpOnly session cookie and expose session token in header for cross-site fallbacks."""
    import os
    is_prod = os.getenv("FLASK_ENV") == "production" or os.getenv("ENV") == "production"
    secure = is_prod or (request.is_secure if request else False)
    # When deployed in production across subdomains/services (e.g. onrender.com),
    # SameSite must be "None" with secure=True so the browser includes credentials.
    samesite = "None" if is_prod else "Lax"
    response.set_cookie(
        SESSION_COOKIE_NAME,
        raw_token,
        max_age=max_age,
        httponly=True,
        samesite=samesite,
        secure=secure,
        path="/"
    )
    # Expose session token header for cross-site environments where 3rd-party cookies are blocked by browsers
    response.headers["X-Session-Token"] = raw_token
    return response


def clear_session_cookie(response):
    """Clear session cookie from the client matching set_session_cookie attributes."""
    import os
    is_prod = os.getenv("FLASK_ENV") == "production" or os.getenv("ENV") == "production"
    secure = is_prod or (request.is_secure if request else False)
    samesite = "None" if is_prod else "Lax"
    response.set_cookie(
        SESSION_COOKIE_NAME,
        "",
        expires=0,
        max_age=0,
        httponly=True,
        samesite=samesite,
        secure=secure,
        path="/"
    )
    response.headers["X-Session-Token"] = ""
    return response
