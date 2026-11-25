import sqlite3
from typing import Any, Dict, List, Optional
from app.db.connection import get_db
from app.dsa import get_dsa_manager
from app.repositories.user_repository import UserRepository


class SearchService:
    """Service handling prefix-based student lookup using Trie."""

    @staticmethod
    def search_users(
        query: str,
        limit: int = 10,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lookup students by prefix using the custom in-memory Trie index,
        then resolve full student public profiles from SQLite.
        """
        if not query or not query.strip():
            return []

        limit = max(1, min(limit, 50))
        dsa_manager = get_dsa_manager()
        matching_user_ids = dsa_manager.search_prefix(query.strip(), limit=limit)

        if not matching_user_ids:
            return []

        conn = conn or get_db()
        results = []
        for uid in matching_user_ids:
            user = UserRepository.get_by_id(conn, uid)
            if user:
                results.append({
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "programme": user["programme"],
                    "academic_year": user["academic_year"],
                    "bio": user["bio"],
                })

        return results

