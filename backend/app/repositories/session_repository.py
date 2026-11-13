import sqlite3
from typing import Any, Dict, List, Optional
from app.utils.helpers import utc_now_iso


class SessionRepository:
    """Data access repository for user_sessions table (CC-DAT-004 v1.2 Section 4.5)."""

    @staticmethod
    def create_session(
        conn: sqlite3.Connection,
        user_id: str,
        session_id: str,
        expires_at: str,
        csrf_token_hash: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Insert a server-managed session record.
        session_id MUST be the SHA-256 hash of the client's token, never the raw token.
        """
        now = created_at or utc_now_iso()

        conn.execute(
            """
            INSERT INTO user_sessions (session_id, user_id, csrf_token_hash, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, user_id, csrf_token_hash, now, expires_at),
        )

        return {
            "session_id": session_id,
            "user_id": user_id,
            "csrf_token_hash": csrf_token_hash,
            "created_at": now,
            "expires_at": expires_at,
        }

    @staticmethod
    def get_by_id(conn: sqlite3.Connection, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a session by its hashed session_id."""
        cursor = conn.execute("SELECT * FROM user_sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_active_session(
        conn: sqlite3.Connection, session_id: str, now_iso: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a session only if it has not expired.
        Rejects sessions where expires_at <= current UTC time.
        """
        now = now_iso or utc_now_iso()
        cursor = conn.execute(
            "SELECT * FROM user_sessions WHERE session_id = ? AND expires_at > ?",
            (session_id, now),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def delete_session(conn: sqlite3.Connection, session_id: str) -> bool:
        """Delete an individual session (e.g. user logout)."""
        cursor = conn.execute("DELETE FROM user_sessions WHERE session_id = ?", (session_id,))
        return cursor.rowcount > 0

    @staticmethod
    def delete_all_for_user(conn: sqlite3.Connection, user_id: str) -> int:
        """
        Delete all active sessions for a user (e.g. on password reset or account deletion).
        Returns the number of invalidated sessions.
        """
        cursor = conn.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
        return cursor.rowcount

    @staticmethod
    def delete_expired_sessions(conn: sqlite3.Connection, now_iso: Optional[str] = None) -> int:
        """
        Clean up expired session records.
        Returns the count of purged sessions.
        """
        now = now_iso or utc_now_iso()
        cursor = conn.execute("DELETE FROM user_sessions WHERE expires_at <= ?", (now,))
        return cursor.rowcount
