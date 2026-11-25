import datetime
import json
import sqlite3
import uuid
from typing import Any, Dict, Optional, Tuple
from app.db.connection import get_db
from app.dsa import get_dsa_manager
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.utils.helpers import (
    generate_id,
    hash_password,
    hash_session_token,
    normalize_key,
    utc_now_iso,
    verify_password,
)


class AuthService:
    """Service handling registration, authentication, and session lifecycles."""

    @staticmethod
    def register_user(
        username: str,
        email: str,
        password: str,
        full_name: str,
        programme: str = "General",
        academic_year: int = 1,
        skills: Any = None,
        bio: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Dict[str, Any]:
        """
        Validate inputs, hash password, create persistent user record,
        and atomically synchronize in-memory vertex and Trie search keys.
        """
        if not username or not username.strip():
            raise ValueError("Username is required.")
        if not email or not email.strip():
            raise ValueError("Email is required.")
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters.")
        if not full_name or not full_name.strip():
            raise ValueError("Full name is required.")

        conn = conn or get_db()
        norm_username = normalize_key(username)
        norm_email = normalize_key(email)

        # Check uniqueness
        if UserRepository.get_by_username_key(conn, norm_username):
            raise ValueError("Username is already taken.")
        if UserRepository.get_by_email_key(conn, norm_email):
            raise ValueError("Email is already registered.")

        pwd_hash = hash_password(password)
        user_id = generate_id("usr")
        if skills is None:
            skills = []

        dsa_manager = get_dsa_manager()

        with dsa_manager.synchronized_mutation(conn) as sync:
            user_record = UserRepository.create_user(
                conn=conn,
                username=username.strip(),
                email=email.strip(),
                password_hash=pwd_hash,
                full_name=full_name.strip(),
                programme=programme.strip(),
                academic_year=int(academic_year),
                skills=skills,
                user_id=user_id,
                bio=bio.strip() if bio else None,
            )
            sync.record_user_registered(user_id, username.strip(), full_name.strip())

        return {
            "user_id": user_record["user_id"],
            "username": user_record["username"],
            "full_name": user_record["full_name"],
            "email": user_record["email"],
        }

    @staticmethod
    def login(
        username_or_email: str,
        password: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Authenticate user credentials and create a server-managed session.
        Returns (raw_session_token, public_user_data).
        """
        if not username_or_email or not password:
            raise ValueError("Username/email and password are required.")

        conn = conn or get_db()
        norm_key = normalize_key(username_or_email)

        user = UserRepository.get_by_username_key(conn, norm_key)
        if not user:
            user = UserRepository.get_by_email_key(conn, norm_key)

        if not user or not verify_password(user["password_hash"], password):
            raise ValueError("Invalid credentials.")

        raw_token = uuid.uuid4().hex + uuid.uuid4().hex
        hashed_token = hash_session_token(raw_token)

        # Expiry 7 days from now
        expires_at = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        SessionRepository.create_session(
            conn=conn,
            user_id=user["user_id"],
            session_id=hashed_token,
            expires_at=expires_at,
        )

        user_data = {
            "user_id": user["user_id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "programme": user["programme"],
            "academic_year": user["academic_year"],
        }
        return raw_token, user_data

    @staticmethod
    def logout(raw_token: str, conn: Optional[sqlite3.Connection] = None) -> bool:
        """Invalidate the session corresponding to the raw token."""
        if not raw_token:
            return False
        conn = conn or get_db()
        hashed_token = hash_session_token(raw_token)
        return SessionRepository.delete_session(conn, hashed_token)
