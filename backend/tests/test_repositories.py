import sqlite3
import pytest
from app.repositories import (
    UserRepository,
    ConnectionRequestRepository,
    ConnectionRepository,
    PostRepository,
    SessionRepository,
)
from app.repositories.connection_request_repository import (
    SelfRequestError,
    ReverseRequestConflictError,
    DuplicatePendingRequestError,
    AlreadyConnectedError,
    InvalidRequestStatusError,
)
from app.utils.helpers import hash_session_token, utc_now_iso


# --- User Repository Tests ---

def test_user_creation_and_retrieval(db_conn):
    """Verify user creation and retrieval by id, username_key, and email_key."""
    user = UserRepository.create_user(
        conn=db_conn,
        username="JohnDoe",
        email="John.Doe@University.edu",
        password_hash="scrypt:hash123",
        full_name="John Doe",
        programme="Computer Science",
        academic_year=3,
        skills=["Python", "React", "SQL"],
        bio="Hello world",
    )
    assert user["user_id"] is not None
    assert user["username_key"] == "johndoe"
    assert user["email_key"] == "john.doe@university.edu"

    # Retrieve by ID
    by_id = UserRepository.get_by_id(db_conn, user["user_id"])
    assert by_id is not None
    assert by_id["username"] == "JohnDoe"

    # Retrieve by username_key
    by_uname = UserRepository.get_by_username_key(db_conn, "johndoe")
    assert by_uname is not None
    assert by_uname["user_id"] == user["user_id"]

    # Retrieve by email_key
    by_email = UserRepository.get_by_email_key(db_conn, "john.doe@university.edu")
    assert by_email is not None
    assert by_email["user_id"] == user["user_id"]


def test_user_case_insensitive_username_uniqueness(db_conn):
    """Verify that case-variant usernames collide on username_key."""
    UserRepository.create_user(
        conn=db_conn,
        username="AliceSmith",
        email="alice@u.edu",
        password_hash="h1",
        full_name="Alice Smith",
        programme="CS",
        academic_year=2,
        skills=[],
    )

    # Attempt second user with different casing for username
    with pytest.raises(sqlite3.IntegrityError):
        UserRepository.create_user(
            conn=db_conn,
            username="ALICESMITH",
            email="alice2@u.edu",
            password_hash="h2",
            full_name="Alice Smith 2",
            programme="CS",
            academic_year=2,
            skills=[],
        )


def test_user_case_insensitive_email_uniqueness(db_conn):
    """Verify that case-variant emails collide on email_key."""
    UserRepository.create_user(
        conn=db_conn,
        username="user1",
        email="Student@College.EDU",
        password_hash="h1",
        full_name="User One",
        programme="CS",
        academic_year=1,
        skills=[],
    )

    with pytest.raises(sqlite3.IntegrityError):
        UserRepository.create_user(
            conn=db_conn,
            username="user2",
            email="student@college.edu",
            password_hash="h2",
            full_name="User Two",
            programme="CS",
            academic_year=1,
            skills=[],
        )


def test_user_profile_update(db_conn):
    """Verify profile fields update correctly."""
    user = UserRepository.create_user(
        conn=db_conn,
        username="bob",
        email="bob@u.edu",
        password_hash="h",
        full_name="Bob Builder",
        programme="EE",
        academic_year=1,
        skills=["C"],
    )

    updated = UserRepository.update_profile(
        conn=db_conn,
        user_id=user["user_id"],
        full_name="Robert Builder",
        academic_year=2,
        skills=["C", "Python"],
        bio="Updated bio",
    )
    assert updated["full_name"] == "Robert Builder"
    assert updated["academic_year"] == 2
    assert "Python" in updated["skills"]
    assert updated["bio"] == "Updated bio"


# --- Connection Request Repository Tests ---

def test_connection_request_lifecycle(db_conn):
    """Verify send request, pending query, and accept request creating connection."""
    u1 = UserRepository.create_user(
        db_conn, "alice", "alice@u.edu", "h", "Alice", "CS", 1, []
    )
    u2 = UserRepository.create_user(
        db_conn, "bob", "bob@u.edu", "h", "Bob", "CS", 1, []
    )

    # u1 sends request to u2
    req = ConnectionRequestRepository.create_request(db_conn, u1["user_id"], u2["user_id"])
    assert req["status"] == "pending"

    # Query incoming for u2
    incoming = ConnectionRequestRepository.get_incoming_requests(db_conn, u2["user_id"])
    assert len(incoming) == 1
    assert incoming[0]["request_id"] == req["request_id"]

    # Query outgoing for u1
    outgoing = ConnectionRequestRepository.get_outgoing_requests(db_conn, u1["user_id"])
    assert len(outgoing) == 1
    assert outgoing[0]["request_id"] == req["request_id"]

    # u2 accepts request
    result = ConnectionRequestRepository.accept_request(db_conn, req["request_id"], u2["user_id"])
    assert result["request"]["status"] == "accepted"
    assert result["connection"] is not None

    # Verify they are now connected
    assert ConnectionRepository.are_connected(db_conn, u1["user_id"], u2["user_id"]) is True


def test_connection_request_self_request_rejected(db_conn):
    """Verify self-request raises SelfRequestError."""
    u1 = UserRepository.create_user(
        db_conn, "alice", "alice@u.edu", "h", "Alice", "CS", 1, []
    )
    with pytest.raises(SelfRequestError):
        ConnectionRequestRepository.create_request(db_conn, u1["user_id"], u1["user_id"])


def test_connection_request_reverse_pending_prevention(db_conn):
    """Verify reverse-direction pending request raises ReverseRequestConflictError."""
    u1 = UserRepository.create_user(
        db_conn, "alice", "alice@u.edu", "h", "Alice", "CS", 1, []
    )
    u2 = UserRepository.create_user(
        db_conn, "bob", "bob@u.edu", "h", "Bob", "CS", 1, []
    )

    # u1 sends to u2
    ConnectionRequestRepository.create_request(db_conn, u1["user_id"], u2["user_id"])

    # u2 attempts to send to u1 while request is pending
    with pytest.raises(ReverseRequestConflictError):
        ConnectionRequestRepository.create_request(db_conn, u2["user_id"], u1["user_id"])


def test_connection_request_duplicate_pending_prevention(db_conn):
    """Verify duplicate request in same direction raises DuplicatePendingRequestError."""
    u1 = UserRepository.create_user(
        db_conn, "alice", "alice@u.edu", "h", "Alice", "CS", 1, []
    )
    u2 = UserRepository.create_user(
        db_conn, "bob", "bob@u.edu", "h", "Bob", "CS", 1, []
    )

    ConnectionRequestRepository.create_request(db_conn, u1["user_id"], u2["user_id"])

    with pytest.raises(DuplicatePendingRequestError):
        ConnectionRequestRepository.create_request(db_conn, u1["user_id"], u2["user_id"])


def test_connection_request_already_connected_prevention(db_conn):
    """Verify request cannot be created between already-connected users."""
    u1 = UserRepository.create_user(
        db_conn, "alice", "alice@u.edu", "h", "Alice", "CS", 1, []
    )
    u2 = UserRepository.create_user(
        db_conn, "bob", "bob@u.edu", "h", "Bob", "CS", 1, []
    )
    ConnectionRepository.create_connection(db_conn, u1["user_id"], u2["user_id"])

    with pytest.raises(AlreadyConnectedError):
        ConnectionRequestRepository.create_request(db_conn, u1["user_id"], u2["user_id"])


def test_connection_request_rejection_and_cancellation(db_conn):
    """Verify rejecting and cancelling requests update status without creating connection."""
    u1 = UserRepository.create_user(db_conn, "u1", "u1@u.edu", "h", "U1", "CS", 1, [])
    u2 = UserRepository.create_user(db_conn, "u2", "u2@u.edu", "h", "U2", "CS", 1, [])
    u3 = UserRepository.create_user(db_conn, "u3", "u3@u.edu", "h", "U3", "CS", 1, [])

    # u1 -> u2 rejected by u2
    req1 = ConnectionRequestRepository.create_request(db_conn, u1["user_id"], u2["user_id"])
    rejected = ConnectionRequestRepository.reject_request(db_conn, req1["request_id"], u2["user_id"])
    assert rejected["status"] == "rejected"
    assert ConnectionRepository.are_connected(db_conn, u1["user_id"], u2["user_id"]) is False

    # u1 -> u3 cancelled by u1
    req2 = ConnectionRequestRepository.create_request(db_conn, u1["user_id"], u3["user_id"])
    cancelled = ConnectionRequestRepository.cancel_request(db_conn, req2["request_id"], u1["user_id"])
    assert cancelled["status"] == "cancelled"
    assert ConnectionRepository.are_connected(db_conn, u1["user_id"], u3["user_id"]) is False


# --- Connection Repository Tests ---

def test_connection_canonical_pair_storage(db_conn):
    """Verify connection stores lower user ID in user_id_low regardless of argument order."""
    u_alpha = UserRepository.create_user(db_conn, "alpha", "alpha@u.edu", "h", "Alpha", "CS", 1, [])
    u_zeta = UserRepository.create_user(db_conn, "zeta", "zeta@u.edu", "h", "Zeta", "CS", 1, [])

    # Order 1: (zeta, alpha) passed
    conn1 = ConnectionRepository.create_connection(db_conn, u_zeta["user_id"], u_alpha["user_id"])
    expected_low = min(u_zeta["user_id"], u_alpha["user_id"])
    expected_high = max(u_zeta["user_id"], u_alpha["user_id"])
    assert conn1["user_id_low"] == expected_low
    assert conn1["user_id_high"] == expected_high

    # are_connected works symmetrically
    assert ConnectionRepository.are_connected(db_conn, u_zeta["user_id"], u_alpha["user_id"]) is True
    assert ConnectionRepository.are_connected(db_conn, u_alpha["user_id"], u_zeta["user_id"]) is True

    # remove_connection deletes canonical row
    assert ConnectionRepository.remove_connection(db_conn, u_alpha["user_id"], u_zeta["user_id"]) is True
    assert ConnectionRepository.are_connected(db_conn, u_alpha["user_id"], u_zeta["user_id"]) is False


# --- Post Repository Tests ---

def test_post_creation_and_validation(db_conn):
    """Verify valid post creation, empty rejection, and retrieval."""
    u1 = UserRepository.create_user(db_conn, "writer", "w@u.edu", "h", "Writer", "CS", 1, [])

    # Valid post
    post = PostRepository.create_post(db_conn, u1["user_id"], "First technical post about graphs.")
    assert post["post_id"] is not None
    assert post["content"] == "First technical post about graphs."

    # Empty content rejected
    with pytest.raises(ValueError):
        PostRepository.create_post(db_conn, u1["user_id"], "   ")

    # Author delete works
    assert PostRepository.delete_post(db_conn, post["post_id"], user_id=u1["user_id"]) is True
    assert PostRepository.get_by_id(db_conn, post["post_id"]) is None


# --- Session Repository Tests ---

def test_session_hashed_token_storage_and_expiry(db_conn):
    """Verify sessions store only hashed tokens and reject expired sessions."""
    u1 = UserRepository.create_user(db_conn, "student", "s@u.edu", "h", "Student", "CS", 1, [])

    raw_token = "secret-client-token-xyz"
    token_hash = hash_session_token(raw_token)
    assert token_hash != raw_token

    # Active session expiring in 2099
    future_iso = "2099-01-01T00:00:00.000000Z"
    SessionRepository.create_session(
        db_conn,
        user_id=u1["user_id"],
        session_id=token_hash,
        expires_at=future_iso,
    )

    # Active session found
    active = SessionRepository.get_active_session(db_conn, token_hash)
    assert active is not None
    assert active["user_id"] == u1["user_id"]

    # Expired session test
    past_iso = "2020-01-01T00:00:00.000000Z"
    expired_token_hash = hash_session_token("expired-token")
    SessionRepository.create_session(
        db_conn,
        user_id=u1["user_id"],
        session_id=expired_token_hash,
        expires_at=past_iso,
    )

    # get_active_session rejects expired session
    assert SessionRepository.get_active_session(db_conn, expired_token_hash) is None

    # delete_expired_sessions purges it
    purged = SessionRepository.delete_expired_sessions(db_conn)
    assert purged >= 1
    assert SessionRepository.get_by_id(db_conn, expired_token_hash) is None
