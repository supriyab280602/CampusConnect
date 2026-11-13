import sqlite3
from typing import Any, Dict, List, Optional
from app.utils.helpers import canonical_user_pair, generate_id, utc_now_iso


class ConnectionRepository:
    """Data access repository for connections table (CC-DAT-004 v1.2 Section 4.3)."""

    @staticmethod
    def create_connection(
        conn: sqlite3.Connection,
        user_a: str,
        user_b: str,
        connection_id: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Insert a canonical undirected connection edge.
        Enforces user_id_low < user_id_high.
        Raises ValueError on self-connection.
        Raises sqlite3.IntegrityError if connection pair already exists.
        """
        low, high = canonical_user_pair(user_a, user_b)
        conn_id = connection_id or generate_id("conn")
        now = created_at or utc_now_iso()

        conn.execute(
            """
            INSERT INTO connections (connection_id, user_id_low, user_id_high, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (conn_id, low, high, now),
        )

        return {
            "connection_id": conn_id,
            "user_id_low": low,
            "user_id_high": high,
            "created_at": now,
        }

    @staticmethod
    def are_connected(conn: sqlite3.Connection, user_a: str, user_b: str) -> bool:
        """Check if an accepted connection exists between two users."""
        if user_a == user_b:
            return False
        low, high = canonical_user_pair(user_a, user_b)
        cursor = conn.execute(
            "SELECT 1 FROM connections WHERE user_id_low = ? AND user_id_high = ?",
            (low, high),
        )
        return cursor.fetchone() is not None

    @staticmethod
    def get_connection(
        conn: sqlite3.Connection, user_a: str, user_b: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve connection record between two users."""
        if user_a == user_b:
            return None
        low, high = canonical_user_pair(user_a, user_b)
        cursor = conn.execute(
            "SELECT * FROM connections WHERE user_id_low = ? AND user_id_high = ?",
            (low, high),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_connections_for_user(
        conn: sqlite3.Connection, user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all accepted connections where user_id is either user_id_low or user_id_high.
        Returns list of connection records.
        """
        cursor = conn.execute(
            """
            SELECT * FROM connections
            WHERE user_id_low = ? OR user_id_high = ?
            ORDER BY created_at DESC
            """,
            (user_id, user_id),
        )
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def remove_connection(conn: sqlite3.Connection, user_a: str, user_b: str) -> bool:
        """
        Delete the canonical connection row between user_a and user_b.
        Returns True if row was deleted, False otherwise.
        """
        if user_a == user_b:
            return False
        low, high = canonical_user_pair(user_a, user_b)
        cursor = conn.execute(
            "DELETE FROM connections WHERE user_id_low = ? AND user_id_high = ?",
            (low, high),
        )
        return cursor.rowcount > 0

    @staticmethod
    def get_all_connections(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        """
        Retrieve all connection edges from the database.
        Used at startup to rebuild the in-memory graph.
        """
        cursor = conn.execute("SELECT * FROM connections ORDER BY created_at ASC")
        return [dict(row) for row in cursor.fetchall()]
