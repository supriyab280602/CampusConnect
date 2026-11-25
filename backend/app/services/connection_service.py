import sqlite3
from typing import Any, Dict, List, Optional
from app.db.connection import get_db
from app.dsa import get_dsa_manager
from app.repositories.connection_repository import ConnectionRepository
from app.repositories.connection_request_repository import (
    ConnectionRequestRepository,
    SelfRequestError,
    AlreadyConnectedError,
    ReverseRequestConflictError,
    DuplicatePendingRequestError,
    InvalidRequestStatusError,
)
from app.repositories.user_repository import UserRepository


class ConnectionService:
    """Service governing connection requests and accepted graph relationships."""

    @staticmethod
    def send_request(
        sender_id: str,
        receiver_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Dict[str, Any]:
        """Send a connection request after verifying constraints."""
        conn = conn or get_db()
        receiver = UserRepository.get_by_id(conn, receiver_id)
        if not receiver:
            raise ValueError("Target user does not exist.")

        return ConnectionRequestRepository.create_request(conn, sender_id, receiver_id)

    @staticmethod
    def get_received_requests(
        user_id: str, conn: Optional[sqlite3.Connection] = None
    ) -> List[Dict[str, Any]]:
        """List pending connection requests received by user."""
        conn = conn or get_db()
        requests = ConnectionRequestRepository.get_incoming_requests(conn, user_id, "pending")
        enriched = []
        for req in requests:
            sender = UserRepository.get_by_id(conn, req["sender_id"])
            enriched.append({
                "request_id": req["request_id"],
                "sender_id": req["sender_id"],
                "receiver_id": req["receiver_id"],
                "created_at": req["created_at"],
                "sender": {
                    "user_id": sender["user_id"],
                    "username": sender["username"],
                    "full_name": sender["full_name"],
                    "programme": sender["programme"],
                    "academic_year": sender["academic_year"],
                } if sender else None,
            })
        return enriched

    @staticmethod
    def get_sent_requests(
        user_id: str, conn: Optional[sqlite3.Connection] = None
    ) -> List[Dict[str, Any]]:
        """List pending connection requests sent by user."""
        conn = conn or get_db()
        requests = ConnectionRequestRepository.get_outgoing_requests(conn, user_id, "pending")
        enriched = []
        for req in requests:
            receiver = UserRepository.get_by_id(conn, req["receiver_id"])
            enriched.append({
                "request_id": req["request_id"],
                "sender_id": req["sender_id"],
                "receiver_id": req["receiver_id"],
                "created_at": req["created_at"],
                "receiver": {
                    "user_id": receiver["user_id"],
                    "username": receiver["username"],
                    "full_name": receiver["full_name"],
                    "programme": receiver["programme"],
                    "academic_year": receiver["academic_year"],
                } if receiver else None,
            })
        return enriched

    @staticmethod
    def accept_request(
        request_id: str,
        receiver_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Dict[str, Any]:
        """
        Accept a pending connection request atomically.
        Commits canonical edge in SQLite and adds undirected edge in DSAManager.
        """
        conn = conn or get_db()
        dsa_manager = get_dsa_manager()

        req = ConnectionRequestRepository.get_by_id(conn, request_id)
        if not req:
            raise LookupError("Connection request not found.")
        if req["receiver_id"] != receiver_id:
            raise PermissionError("Only the designated recipient may accept this request.")
        if req["status"] != "pending":
            raise InvalidRequestStatusError(f"Cannot accept request with status '{req['status']}'; status must be 'pending'.")

        sender_id = req["sender_id"]

        with dsa_manager.synchronized_mutation(conn) as sync:
            result = ConnectionRequestRepository.accept_request(conn, request_id, receiver_id)
            sync.record_connection_accepted(sender_id, receiver_id)

        return result

    @staticmethod
    def reject_request(
        request_id: str,
        receiver_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Dict[str, Any]:
        """Reject a pending connection request."""
        conn = conn or get_db()
        req = ConnectionRequestRepository.get_by_id(conn, request_id)
        if not req:
            raise LookupError("Connection request not found.")
        if req["receiver_id"] != receiver_id:
            raise PermissionError("Only the designated recipient may reject this request.")
        if req["status"] != "pending":
            raise InvalidRequestStatusError(f"Cannot reject request with status '{req['status']}'; status must be 'pending'.")
        return ConnectionRequestRepository.reject_request(conn, request_id, receiver_id)

    @staticmethod
    def cancel_request(
        request_id: str,
        sender_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Dict[str, Any]:
        """Cancel a pending outgoing connection request."""
        conn = conn or get_db()
        req = ConnectionRequestRepository.get_by_id(conn, request_id)
        if not req:
            raise LookupError("Connection request not found.")
        if req["sender_id"] != sender_id:
            raise PermissionError("Only the original sender can cancel this request.")
        if req["status"] != "pending":
            raise InvalidRequestStatusError(f"Cannot cancel request with status '{req['status']}'; status must be 'pending'.")
        return ConnectionRequestRepository.cancel_request(conn, request_id, sender_id)

    @staticmethod
    def list_connections(
        user_id: str, conn: Optional[sqlite3.Connection] = None
    ) -> List[Dict[str, Any]]:
        """List accepted connections of user with public profile details."""
        conn = conn or get_db()
        connections = ConnectionRepository.get_connections_for_user(conn, user_id)
        result = []
        for c in connections:
            partner_id = c["user_id_high"] if user_id == c["user_id_low"] else c["user_id_low"]
            partner = UserRepository.get_by_id(conn, partner_id)
            if partner:
                result.append({
                    "connection_id": c["connection_id"],
                    "connected_at": c["created_at"],
                    "user": {
                        "user_id": partner["user_id"],
                        "username": partner["username"],
                        "full_name": partner["full_name"],
                        "programme": partner["programme"],
                        "academic_year": partner["academic_year"],
                        "bio": partner["bio"],
                    }
                })
        return result

    @staticmethod
    def remove_connection(
        user_a: str, user_b: str, conn: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Remove connection in SQLite and synchronize graph edge removal in DSAManager."""
        conn = conn or get_db()
        dsa_manager = get_dsa_manager()

        if not ConnectionRepository.are_connected(conn, user_a, user_b):
            raise LookupError("Users are not connected.")

        with dsa_manager.synchronized_mutation(conn) as sync:
            removed = ConnectionRepository.remove_connection(conn, user_a, user_b)
            if not removed:
                return False
            sync.record_connection_removed(user_a, user_b)

        return True
