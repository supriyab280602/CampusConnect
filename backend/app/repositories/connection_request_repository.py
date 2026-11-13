import sqlite3
from typing import Any, Dict, List, Optional
from app.repositories.connection_repository import ConnectionRepository
from app.utils.helpers import canonical_user_pair, generate_id, utc_now_iso


class SelfRequestError(ValueError):
    """Raised when a user attempts to send a connection request to themselves."""
    pass


class ReverseRequestConflictError(Exception):
    """Raised when a pending reverse request already exists."""
    pass


class AlreadyConnectedError(Exception):
    """Raised when the two users are already accepted connections."""
    pass


class DuplicatePendingRequestError(Exception):
    """Raised when a pending request in the same direction already exists."""
    pass


class InvalidRequestStatusError(ValueError):
    """Raised when an invalid status transition is attempted."""
    pass


class ConnectionRequestRepository:
    """Data access repository for connection_requests (CC-DAT-004 v1.2 Section 4.2)."""

    VALID_STATUSES = {"pending", "accepted", "rejected", "cancelled"}

    @staticmethod
    def create_request(
        conn: sqlite3.Connection,
        sender_id: str,
        receiver_id: str,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a directed connection request in a write-locked transaction (BEGIN IMMEDIATE).
        Enforces:
        1. sender_id != receiver_id
        2. Users must not already be connected
        3. No reverse pending request exists
        4. No duplicate pending request in the same direction exists
        """
        if sender_id == receiver_id:
            raise SelfRequestError("Sender and receiver cannot be the same user.")

        # Ensure write lock if not already inside a transaction
        # If in autocommit mode, start BEGIN IMMEDIATE
        try:
            conn.execute("BEGIN IMMEDIATE;")
            in_local_tx = True
        except sqlite3.OperationalError:
            # Already inside an active transaction
            in_local_tx = False

        try:
            # 1. Verify not already connected
            if ConnectionRepository.are_connected(conn, sender_id, receiver_id):
                raise AlreadyConnectedError("Users are already connected.")

            # 2. Check for reverse pending request
            reverse_cursor = conn.execute(
                "SELECT request_id FROM connection_requests WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'",
                (receiver_id, sender_id),
            )
            if reverse_cursor.fetchone():
                raise ReverseRequestConflictError(
                    "A pending connection request from the recipient already exists. Accept or resolve that request."
                )

            # 3. Check for existing pending request in same direction
            same_cursor = conn.execute(
                "SELECT request_id FROM connection_requests WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'",
                (sender_id, receiver_id),
            )
            if same_cursor.fetchone():
                raise DuplicatePendingRequestError("A pending request to this user already exists.")

            # 4. Insert request
            req_id = request_id or generate_id("req")
            now = utc_now_iso()

            conn.execute(
                """
                INSERT INTO connection_requests (
                    request_id, sender_id, receiver_id, status, created_at, updated_at
                ) VALUES (?, ?, ?, 'pending', ?, ?)
                """,
                (req_id, sender_id, receiver_id, now, now),
            )

            if in_local_tx:
                conn.execute("COMMIT;")

            return {
                "request_id": req_id,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "status": "pending",
                "created_at": now,
                "updated_at": now,
            }
        except Exception:
            if in_local_tx:
                conn.execute("ROLLBACK;")
            raise

    @staticmethod
    def get_by_id(conn: sqlite3.Connection, request_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve request by request_id."""
        cursor = conn.execute("SELECT * FROM connection_requests WHERE request_id = ?", (request_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_incoming_requests(
        conn: sqlite3.Connection, receiver_id: str, status: str = "pending"
    ) -> List[Dict[str, Any]]:
        """Retrieve incoming requests for a user ordered by created_at DESC."""
        cursor = conn.execute(
            """
            SELECT * FROM connection_requests
            WHERE receiver_id = ? AND status = ?
            ORDER BY created_at DESC
            """,
            (receiver_id, status),
        )
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_outgoing_requests(
        conn: sqlite3.Connection, sender_id: str, status: str = "pending"
    ) -> List[Dict[str, Any]]:
        """Retrieve outgoing requests for a user ordered by created_at DESC."""
        cursor = conn.execute(
            """
            SELECT * FROM connection_requests
            WHERE sender_id = ? AND status = ?
            ORDER BY created_at DESC
            """,
            (sender_id, status),
        )
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def accept_request(
        conn: sqlite3.Connection, request_id: str, receiver_id: str
    ) -> Dict[str, Any]:
        """
        Accept a pending connection request atomically.
        Creates exactly one canonical row in `connections` and updates request status to 'accepted'.
        """
        try:
            conn.execute("BEGIN IMMEDIATE;")
            in_local_tx = True
        except sqlite3.OperationalError:
            in_local_tx = False

        try:
            req = ConnectionRequestRepository.get_by_id(conn, request_id)
            if not req:
                raise ValueError("Connection request not found.")
            if req["receiver_id"] != receiver_id:
                raise ValueError("Only the designated receiver can accept this request.")
            if req["status"] != "pending":
                raise InvalidRequestStatusError(
                    f"Cannot accept request with status '{req['status']}'; status must be 'pending'."
                )

            # Insert canonical connection row
            connection_record = ConnectionRepository.create_connection(
                conn, req["sender_id"], req["receiver_id"]
            )

            # Update request status
            now = utc_now_iso()
            conn.execute(
                "UPDATE connection_requests SET status = 'accepted', updated_at = ? WHERE request_id = ?",
                (now, request_id),
            )

            if in_local_tx:
                conn.execute("COMMIT;")

            req["status"] = "accepted"
            req["updated_at"] = now
            return {
                "request": req,
                "connection": connection_record,
            }
        except Exception:
            if in_local_tx:
                conn.execute("ROLLBACK;")
            raise

    @staticmethod
    def reject_request(
        conn: sqlite3.Connection, request_id: str, receiver_id: str
    ) -> Dict[str, Any]:
        """Reject a pending connection request."""
        req = ConnectionRequestRepository.get_by_id(conn, request_id)
        if not req:
            raise ValueError("Connection request not found.")
        if req["receiver_id"] != receiver_id:
            raise ValueError("Only the designated receiver can reject this request.")
        if req["status"] != "pending":
            raise InvalidRequestStatusError(
                f"Cannot reject request with status '{req['status']}'; status must be 'pending'."
            )

        now = utc_now_iso()
        conn.execute(
            "UPDATE connection_requests SET status = 'rejected', updated_at = ? WHERE request_id = ?",
            (now, request_id),
        )
        req["status"] = "rejected"
        req["updated_at"] = now
        return req

    @staticmethod
    def cancel_request(
        conn: sqlite3.Connection, request_id: str, sender_id: str
    ) -> Dict[str, Any]:
        """Cancel a pending outgoing connection request."""
        req = ConnectionRequestRepository.get_by_id(conn, request_id)
        if not req:
            raise ValueError("Connection request not found.")
        if req["sender_id"] != sender_id:
            raise ValueError("Only the original sender can cancel this request.")
        if req["status"] != "pending":
            raise InvalidRequestStatusError(
                f"Cannot cancel request with status '{req['status']}'; status must be 'pending'."
            )

        now = utc_now_iso()
        conn.execute(
            "UPDATE connection_requests SET status = 'cancelled', updated_at = ? WHERE request_id = ?",
            (now, request_id),
        )
        req["status"] = "cancelled"
        req["updated_at"] = now
        return req
