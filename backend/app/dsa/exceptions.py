"""
DSA Layer Domain Exceptions.
"""


class DSABaseException(Exception):
    """Base exception for all in-memory DSA operations."""
    pass


class IndexUnavailableError(DSABaseException):
    """
    Raised when a graph or Trie read/mutation query arrives
    while in-memory indices are unavailable or recovering.
    Maps to HTTP 503 Service Unavailable.
    """
    pass


class IndexDegradedCommittedError(DSABaseException):
    """
    Raised when a database transaction has successfully committed to SQLite,
    but the corresponding in-memory index update and subsequent recovery rebuild
    both failed.
    Explicitly informs the caller that persistent data was committed and should
    NOT be blindly retried.
    """
    pass
