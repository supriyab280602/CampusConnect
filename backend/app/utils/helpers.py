import hashlib
import unicodedata
import uuid
from datetime import datetime, timezone
from werkzeug.security import check_password_hash, generate_password_hash


def utc_now_iso() -> str:
    """Return the current UTC timestamp formatted as ISO-8601 YYYY-MM-DDTHH:MM:SS.ffffffZ."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def normalize_key(text: str) -> str:
    """
    Produce a normalized key for case-insensitive and Unicode-aware uniqueness checks.
    Uses NFKC normalization, Unicode case folding, and whitespace trimming.
    """
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", text.strip())
    return normalized.casefold()


def generate_id(prefix: str = "") -> str:
    """Generate a collision-resistant unique identifier."""
    unique_part = uuid.uuid4().hex
    if prefix:
        return f"{prefix}_{unique_part}"
    return unique_part


def canonical_user_pair(user_a: str, user_b: str) -> tuple[str, str]:
    """
    Return a canonical undirected pair (user_id_low, user_id_high).
    Enforces user_id_low < user_id_high and prohibits self-connections.
    """
    if not user_a or not user_b:
        raise ValueError("Both user identifiers must be provided.")
    if user_a == user_b:
        raise ValueError("Self-connection is prohibited; user identifiers must be distinct.")
    return (user_a, user_b) if user_a < user_b else (user_b, user_a)


def hash_session_token(raw_token: str) -> str:
    """
    Produce a SHA-256 cryptographic hash of the session token.
    The raw token is returned to the client in an HttpOnly cookie and never stored in the database.
    """
    if not raw_token:
        raise ValueError("Raw token cannot be empty.")
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    """Hash password using Werkzeug's secure password hashing."""
    if not password:
        raise ValueError("Password cannot be empty.")
    return generate_password_hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Verify password against stored hash."""
    if not password_hash or not password:
        return False
    return check_password_hash(password_hash, password)
