import sqlite3
from typing import Any, Dict, Optional
from app.db.connection import get_db
from app.repositories.post_repository import PostRepository
from app.repositories.user_repository import UserRepository


class PostService:
    """Service governing student technical posts."""

    @staticmethod
    def create_post(
        user_id: str,
        content: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Dict[str, Any]:
        """Create a new post authored by user_id."""
        if not content or not content.strip():
            raise ValueError("Post content cannot be empty.")

        conn = conn or get_db()
        return PostRepository.create_post(conn, user_id=user_id, content=content.strip())

    @staticmethod
    def get_post(
        post_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve post and author profile."""
        conn = conn or get_db()
        post = PostRepository.get_by_id(conn, post_id)
        if not post:
            return None

        author = UserRepository.get_by_id(conn, post["user_id"])
        return {
            "post_id": post["post_id"],
            "user_id": post["user_id"],
            "content": post["content"],
            "created_at": post["created_at"],
            "updated_at": post["updated_at"],
            "author": {
                "user_id": author["user_id"],
                "username": author["username"],
                "full_name": author["full_name"],
                "programme": author.get("programme"),
                "academic_year": author.get("academic_year"),
            } if author else None,
        }

    @staticmethod
    def delete_post(
        post_id: str,
        user_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        """Delete post verifying caller is the author."""
        conn = conn or get_db()
        post = PostRepository.get_by_id(conn, post_id)
        if not post:
            raise ValueError("Post not found.")
        if post["user_id"] != user_id:
            raise PermissionError("Only the author may delete their post.")

        return PostRepository.delete_post(conn, post_id=post_id, user_id=user_id)
