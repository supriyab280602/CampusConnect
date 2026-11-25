import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from app.db.connection import get_db
from app.dsa import get_dsa_manager
from app.repositories.user_repository import UserRepository
from app.utils.helpers import normalize_key


class NetworkService:
    """Service governing graph analysis: degree, mutual connections, BFS paths, recommendations."""

    @staticmethod
    def _resolve_canonical_user_id(identifier: str, conn: sqlite3.Connection) -> Optional[str]:
        """
        Resolve an identifier (user_id, username, @username, or full name)
        to a canonical user_id from the database.
        """
        raw = (identifier or "").strip()
        if not raw:
            return None

        # 1. Direct user_id lookup
        user = UserRepository.get_by_id(conn, raw)
        if user:
            return user["user_id"]

        clean = raw.lstrip("@").strip()
        if clean != raw:
            user = UserRepository.get_by_id(conn, clean)
            if user:
                return user["user_id"]

        # 2. Case-insensitive normalized username key lookup
        username_key = normalize_key(clean)
        if username_key:
            user = UserRepository.get_by_username_key(conn, username_key)
            if user:
                return user["user_id"]

        # 3. Exact full_name match (case-insensitive)
        cursor = conn.execute(
            "SELECT user_id FROM users WHERE LOWER(TRIM(full_name)) = LOWER(?) LIMIT 1",
            (clean,),
        )
        row = cursor.fetchone()
        if row:
            return row["user_id"]

        return None

    resolve_canonical_user_id = _resolve_canonical_user_id

    @staticmethod
    def get_degree(user_id: str, conn: Optional[sqlite3.Connection] = None) -> int:
        """Return immediate accepted-connection count in O(1) time."""
        conn = conn or get_db()
        canonical_id = NetworkService._resolve_canonical_user_id(user_id, conn) or user_id
        dsa_manager = get_dsa_manager()
        return dsa_manager.get_degree(canonical_id)

    @staticmethod
    def get_mutual_connections(
        user_a: str,
        user_b: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calculate common connections between user_a and user_b via graph set intersection,
        returning their public student profiles.
        """
        conn = conn or get_db()
        canonical_a = NetworkService._resolve_canonical_user_id(user_a, conn) or user_a
        canonical_b = NetworkService._resolve_canonical_user_id(user_b, conn) or user_b

        dsa_manager = get_dsa_manager()
        mutual_ids = dsa_manager.get_mutual_connections(canonical_a, canonical_b)
        if not mutual_ids:
            return []

        mutual_users = []
        for uid in mutual_ids:
            u = UserRepository.get_by_id(conn, uid)
            if u:
                mutual_users.append({
                    "user_id": u["user_id"],
                    "username": u["username"],
                    "full_name": u["full_name"],
                    "programme": u["programme"],
                    "academic_year": u["academic_year"],
                })
        return mutual_users

    @staticmethod
    def get_shortest_path(
        source_id: str,
        target_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Tuple[Optional[List[str]], int]:
        """
        Calculate unweighted shortest path and hop distance between source and target via BFS.
        Resolves target and source identifiers (user_id, username, @username) to canonical user_id.
        Returns (path, distance). If disconnected or missing, returns (None, -1).
        """
        conn = conn or get_db()
        dsa_manager = get_dsa_manager()

        canonical_source = NetworkService._resolve_canonical_user_id(source_id, conn)
        if not canonical_source:
            canonical_source = source_id

        canonical_target = NetworkService._resolve_canonical_user_id(target_id, conn)
        if not canonical_target:
            return None, -1

        return dsa_manager.get_shortest_path(canonical_source, canonical_target)

    @staticmethod
    def enrich_path(
        path: Optional[List[str]],
        conn: Optional[sqlite3.Connection] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Enrich a list of vertex IDs along a BFS shortest path with display attributes.
        """
        if path is None:
            return None

        conn = conn or get_db()
        formatted = []
        for uid in path:
            u = UserRepository.get_by_id(conn, uid)
            formatted.append({
                "id": uid,
                "user_id": uid,
                "username": u["username"] if u else None,
                "full_name": u["full_name"] if u else None,
            })
        return formatted

    @staticmethod
    def get_recommendations(
        user_id: str,
        limit: int = 10,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate student connection recommendations.
        Identifies 2-hop graph neighbors (friends-of-friends) who are not already connected,
        ranks them by mutual connection count descending, and returns public student profiles.
        """
        limit = max(1, min(limit, 50))
        dsa_manager = get_dsa_manager()

        try:
            immediate_neighbors = set(dsa_manager.get_neighbors(user_id))
        except Exception:
            return []

        # Find 2-hop candidates
        candidates: dict[str, int] = {}
        for neighbor in immediate_neighbors:
            for second_hop in dsa_manager.get_neighbors(neighbor):
                if second_hop != user_id and second_hop not in immediate_neighbors:
                    candidates[second_hop] = candidates.get(second_hop, 0) + 1

        # If sparse network, also consider other vertices in the graph
        if len(candidates) < limit:
            all_verts = dsa_manager.get_all_vertices()
            for v in all_verts:
                if v != user_id and v not in immediate_neighbors and v not in candidates:
                    candidates[v] = 0

        # Deterministic ranking: mutual count DESC, user_id ASC
        sorted_candidates = sorted(candidates.items(), key=lambda item: (-item[1], item[0]))[:limit]

        conn = conn or get_db()
        recommendations = []
        for cand_id, mutual_count in sorted_candidates:
            u = UserRepository.get_by_id(conn, cand_id)
            if u:
                recommendations.append({
                    "user_id": u["user_id"],
                    "username": u["username"],
                    "full_name": u["full_name"],
                    "programme": u["programme"],
                    "academic_year": u["academic_year"],
                    "bio": u["bio"],
                    "mutual_connections_count": mutual_count,
                })

        return recommendations
