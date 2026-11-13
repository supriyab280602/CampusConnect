import sqlite3
from typing import Any, Dict, List, Optional
from app.utils.helpers import generate_id, utc_now_iso

MAX_POST_CONTENT_LENGTH = 1000


class PostRepository:
    """Data access repository for posts table (CC-DAT-004 v1.2 Section 4.4)."""

    @staticmethod
    def create_post(
        conn: sqlite3.Connection,
        user_id: str,
        content: str,
        post_id: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new post authored by user_id.
        Validates non-empty content and length limits.
        """
        if not content or not content.strip():
            raise ValueError("Post content cannot be empty or purely whitespace.")
        if len(content.strip()) > MAX_POST_CONTENT_LENGTH:
            raise ValueError(
                f"Post content exceeds maximum allowed length of {MAX_POST_CONTENT_LENGTH} characters."
            )

        p_id = post_id or generate_id("post")
        now = utc_now_iso()
        c_at = created_at or now
        u_at = updated_at or now

        conn.execute(
            """
            INSERT INTO posts (post_id, user_id, content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (p_id, user_id, content.strip(), c_at, u_at),
        )

        return {
            "post_id": p_id,
            "user_id": user_id,
            "content": content.strip(),
            "created_at": c_at,
            "updated_at": u_at,
        }

    @staticmethod
    def get_by_id(conn: sqlite3.Connection, post_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a post by post_id."""
        cursor = conn.execute("SELECT * FROM posts WHERE post_id = ?", (post_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_posts_by_user(
        conn: sqlite3.Connection,
        user_id: str,
        limit: int = 20,
        before_timestamp: Optional[str] = None,
        before_post_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve posts authored by a user in reverse-chronological order.
        Supports cursor pagination using (created_at, post_id).
        """
        if before_timestamp and before_post_id:
            query = """
                SELECT * FROM posts
                WHERE user_id = ?
                  AND (created_at < ? OR (created_at = ? AND post_id < ?))
                ORDER BY created_at DESC, post_id DESC
                LIMIT ?
            """
            cursor = conn.execute(
                query, (user_id, before_timestamp, before_timestamp, before_post_id, limit)
            )
        else:
            query = """
                SELECT * FROM posts
                WHERE user_id = ?
                ORDER BY created_at DESC, post_id DESC
                LIMIT ?
            """
            cursor = conn.execute(query, (user_id, limit))

        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def delete_post(
        conn: sqlite3.Connection, post_id: str, user_id: Optional[str] = None
    ) -> bool:
        """
        Delete a post by post_id.
        If user_id is provided, enforces that only the author can delete it.
        """
        if user_id:
            cursor = conn.execute(
                "DELETE FROM posts WHERE post_id = ? AND user_id = ?", (post_id, user_id)
            )
        else:
            cursor = conn.execute("DELETE FROM posts WHERE post_id = ?", (post_id,))
        return cursor.rowcount > 0
