import json
import sqlite3
from typing import Any, Dict, Optional
from app.db.connection import get_db
from app.dsa import get_dsa_manager
from app.repositories.user_repository import UserRepository


class UserService:
    """Service handling student profile queries and updates."""

    @staticmethod
    def get_public_profile(user_id: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        """Retrieve sanitized public student profile."""
        conn = conn or get_db()
        user = UserRepository.get_by_id(conn, user_id)
        if not user:
            return None

        skills = []
        if user.get("skills"):
            try:
                skills = json.loads(user["skills"]) if isinstance(user["skills"], str) else user["skills"]
            except Exception:
                skills = []

        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "programme": user["programme"],
            "academic_year": user["academic_year"],
            "bio": user["bio"],
            "skills": skills,
            "created_at": user["created_at"],
        }

    @staticmethod
    def update_profile(
        user_id: str,
        full_name: Optional[str] = None,
        programme: Optional[str] = None,
        academic_year: Optional[int] = None,
        bio: Optional[str] = None,
        skills: Optional[Any] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Dict[str, Any]:
        """
        Update user profile and synchronize in-memory Trie index under process-wide lock.
        """
        if full_name is not None and not full_name.strip():
            raise ValueError("Full name cannot be empty.")
        if academic_year is not None:
            try:
                ay = int(academic_year)
                if ay < 1 or ay > 10:
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValueError("Academic year must be an integer between 1 and 10.")

        conn = conn or get_db()
        dsa_manager = get_dsa_manager()

        with dsa_manager.synchronized_mutation(conn) as sync:
            old_user = UserRepository.get_by_id(conn, user_id)
            if not old_user:
                raise ValueError("User not found.")

            updated_user = UserRepository.update_profile(
                conn=conn,
                user_id=user_id,
                full_name=full_name,
                programme=programme,
                academic_year=academic_year,
                bio=bio,
                skills=skills,
            )

            # Synchronize Trie search keys if full_name changed
            sync.record_user_updated(
                user_id=user_id,
                old_username=old_user["username"],
                old_full_name=old_user["full_name"],
                new_username=updated_user["username"],
                new_full_name=updated_user["full_name"],
            )

        return UserService.get_public_profile(user_id, conn=conn)
