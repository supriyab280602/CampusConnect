import json
import sqlite3
from typing import Any, Dict, List, Optional
from app.utils.helpers import generate_id, normalize_key, utc_now_iso


class UserRepository:
    """Data access repository for users table (CC-DAT-004 v1.2 Section 4.1)."""

    @staticmethod
    def create_user(
        conn: sqlite3.Connection,
        username: str,
        email: str,
        password_hash: str,
        full_name: str,
        programme: str,
        academic_year: int,
        skills: Any,
        user_id: Optional[str] = None,
        bio: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Insert a new user record with normalized username and email keys.
        Raises sqlite3.IntegrityError on duplicate username_key or email_key.
        """
        if not user_id:
            user_id = generate_id("usr")

        username_key = normalize_key(username)
        email_key = normalize_key(email)

        if not username_key or not email_key:
            raise ValueError("Username and email cannot be empty or purely whitespace.")

        # Ensure skills is JSON-serialized
        if isinstance(skills, (list, tuple)):
            skills_json = json.dumps(list(skills))
        elif isinstance(skills, str):
            # Validate valid JSON string
            json.loads(skills)
            skills_json = skills
        else:
            raise ValueError("Skills must be a list of strings or a valid JSON array string.")

        now = utc_now_iso()
        c_at = created_at or now
        u_at = updated_at or now

        query = """
            INSERT INTO users (
                user_id, username, username_key, email, email_key,
                password_hash, full_name, programme, academic_year,
                bio, skills, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        conn.execute(
            query,
            (
                user_id,
                username.strip(),
                username_key,
                email.strip(),
                email_key,
                password_hash,
                full_name.strip(),
                programme.strip(),
                int(academic_year),
                bio.strip() if bio else None,
                skills_json,
                c_at,
                u_at,
            ),
        )

        return {
            "user_id": user_id,
            "username": username.strip(),
            "username_key": username_key,
            "email": email.strip(),
            "email_key": email_key,
            "full_name": full_name.strip(),
            "programme": programme.strip(),
            "academic_year": int(academic_year),
            "bio": bio.strip() if bio else None,
            "skills": skills_json,
            "created_at": c_at,
            "updated_at": u_at,
        }

    @staticmethod
    def get_by_id(conn: sqlite3.Connection, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user record by user_id."""
        query = "SELECT * FROM users WHERE user_id = ?"
        cursor = conn.execute(query, (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_username_key(conn: sqlite3.Connection, username_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve user record by normalized username key."""
        query = "SELECT * FROM users WHERE username_key = ?"
        cursor = conn.execute(query, (username_key,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_email_key(conn: sqlite3.Connection, email_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve user record by normalized email key."""
        query = "SELECT * FROM users WHERE email_key = ?"
        cursor = conn.execute(query, (email_key,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def update_profile(
        conn: sqlite3.Connection,
        user_id: str,
        full_name: Optional[str] = None,
        programme: Optional[str] = None,
        academic_year: Optional[int] = None,
        bio: Optional[str] = None,
        skills: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update student profile fields and updated_at timestamp."""
        existing = UserRepository.get_by_id(conn, user_id)
        if not existing:
            return None

        updates = []
        params = []

        if full_name is not None:
            updates.append("full_name = ?")
            params.append(full_name.strip())
        if programme is not None:
            updates.append("programme = ?")
            params.append(programme.strip())
        if academic_year is not None:
            updates.append("academic_year = ?")
            params.append(int(academic_year))
        if bio is not None:
            updates.append("bio = ?")
            params.append(bio.strip() if bio else None)
        if skills is not None:
            if isinstance(skills, (list, tuple)):
                skills_json = json.dumps(list(skills))
            elif isinstance(skills, str):
                json.loads(skills)
                skills_json = skills
            else:
                raise ValueError("Skills must be a list of strings or valid JSON string.")
            updates.append("skills = ?")
            params.append(skills_json)

        if not updates:
            return existing

        now = utc_now_iso()
        updates.append("updated_at = ?")
        params.append(now)
        params.append(user_id)

        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
        conn.execute(query, tuple(params))
        return UserRepository.get_by_id(conn, user_id)

    @staticmethod
    def delete_user(conn: sqlite3.Connection, user_id: str) -> bool:
        """
        Delete a user record by user_id.
        Foreign key ON DELETE CASCADE cascades to requests, connections, posts, and sessions.
        """
        cursor = conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        return cursor.rowcount > 0

    @staticmethod
    def list_users(conn: sqlite3.Connection, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List users ordered by created_at."""
        query = "SELECT * FROM users ORDER BY created_at ASC LIMIT ? OFFSET ?"
        cursor = conn.execute(query, (limit, offset))
        return [dict(row) for row in cursor.fetchall()]
