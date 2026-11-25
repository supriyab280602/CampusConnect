"""
DSA Manager and In-Memory Synchronization Coordinator.
Governing Baseline: CC-PLN-DSA-002 v2.4, architecture.md v1.1, database.md v1.2.
"""

import enum
import logging
import sqlite3
import threading
from typing import Any, Optional, List, Tuple, Callable

from app.db.connection import transaction
from app.dsa.bfs import bfs_shortest_path
from app.dsa.exceptions import IndexUnavailableError, IndexDegradedCommittedError
from app.dsa.graph import UndirectedGraph
from app.dsa.trie import PrefixTrie, extract_search_keys

logger = logging.getLogger(__name__)


class CoordinatorState(enum.Enum):
    """Lifecycle states for MutationCoordinator."""
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


class MutationCoordinator:
    """
    Context manager returned by dsa_manager.synchronized_mutation(conn).
    Exclusively coordinates mutations that affect in-memory graph or Trie state.
    Enforces unified locking, pre-mutation readiness checks, mandatory hook
    validation, atomic commit, and safe post-commit index synchronization.
    """

    def __init__(self, manager: "DSAManager", conn: sqlite3.Connection):
        self.manager = manager
        self.conn = conn
        self.post_commit_hook: Optional[Callable[[], None]] = None
        self.tx = None
        self._state = CoordinatorState.CREATED

    def _validate_str(self, val: Any, name: str) -> str:
        """Validate that input parameter is a non-empty string."""
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"Parameter '{name}' must be a non-empty string.")
        return val.strip()

    def on_commit(self, hook_fn: Callable[[], None]) -> None:
        """Register the mandatory post-commit in-memory synchronization hook."""
        if self._state != CoordinatorState.ACTIVE:
            raise RuntimeError("Hooks can only be registered while MutationCoordinator is active.")
        if not callable(hook_fn):
            raise TypeError("Post-commit hook must be a callable.")
        if self.post_commit_hook is not None:
            raise ValueError("Only one post-commit hook may be registered per synchronized mutation.")
        self.post_commit_hook = hook_fn

    def record_connection_accepted(self, user_a: str, user_b: str) -> None:
        """Register controlled post-commit graph edge insertion for accepted connection."""
        if self._state != CoordinatorState.ACTIVE:
            raise RuntimeError("Hooks can only be registered while MutationCoordinator is active.")
        u_a = self._validate_str(user_a, "user_a")
        u_b = self._validate_str(user_b, "user_b")
        if u_a == u_b:
            raise ValueError("Self-connections are prohibited; user_a and user_b must be distinct.")
        self.on_commit(lambda: self.manager._apply_connection_accepted(u_a, u_b))

    def record_connection_removed(self, user_a: str, user_b: str) -> None:
        """Register controlled post-commit graph edge removal for disconnected pair."""
        if self._state != CoordinatorState.ACTIVE:
            raise RuntimeError("Hooks can only be registered while MutationCoordinator is active.")
        u_a = self._validate_str(user_a, "user_a")
        u_b = self._validate_str(user_b, "user_b")
        if u_a == u_b:
            raise ValueError("Vertices must be distinct; user_a and user_b cannot be identical.")
        self.on_commit(lambda: self.manager._apply_connection_removed(u_a, u_b))

    def record_user_registered(self, user_id: str, username: str, full_name: str) -> None:
        """Register controlled post-commit vertex creation and Trie indexing for registered user."""
        if self._state != CoordinatorState.ACTIVE:
            raise RuntimeError("Hooks can only be registered while MutationCoordinator is active.")
        uid = self._validate_str(user_id, "user_id")
        uname = self._validate_str(username, "username")
        fname = self._validate_str(full_name, "full_name")
        self.on_commit(lambda: self.manager._apply_user_registered(uid, uname, fname))

    def record_user_updated(
        self,
        user_id: str,
        old_username: str,
        old_full_name: str,
        new_username: str,
        new_full_name: str
    ) -> None:
        """Register controlled post-commit Trie key replacement for updated user profile."""
        if self._state != CoordinatorState.ACTIVE:
            raise RuntimeError("Hooks can only be registered while MutationCoordinator is active.")
        uid = self._validate_str(user_id, "user_id")
        o_uname = self._validate_str(old_username, "old_username")
        o_fname = self._validate_str(old_full_name, "old_full_name")
        n_uname = self._validate_str(new_username, "new_username")
        n_fname = self._validate_str(new_full_name, "new_full_name")
        self.on_commit(lambda: self.manager._apply_user_updated(
            uid, o_uname, o_fname, n_uname, n_fname
        ))

    def record_user_deleted(self, user_id: str, username: str, full_name: str) -> None:
        """Register controlled post-commit vertex removal and Trie key cleanup for deleted user."""
        if self._state != CoordinatorState.ACTIVE:
            raise RuntimeError("Hooks can only be registered while MutationCoordinator is active.")
        uid = self._validate_str(user_id, "user_id")
        uname = self._validate_str(username, "username")
        fname = self._validate_str(full_name, "full_name")
        self.on_commit(lambda: self.manager._apply_user_deleted(uid, uname, fname))

    def __enter__(self) -> "MutationCoordinator":
        # 1. Lifecycle check: cannot reuse or re-enter
        # If already active or completed, reject without altering existing state.
        if self._state != CoordinatorState.CREATED:
            raise RuntimeError("MutationCoordinator cannot be reused or re-entered.")

        # From this point on, this is the initial entry attempt.
        # Any failure (including interruption during lock acquisition) must permanently
        # transition the coordinator to COMPLETED.
        lock_acquired = False
        success = False

        try:
            # 2. Acquire process-wide mutation lock
            self.manager._lock.acquire()
            lock_acquired = True

            # 3. Reject an already-active SQLite transaction before attempting readiness recovery or opening a transaction.
            # Do not commit or roll back the caller's outer transaction.
            if self.conn.in_transaction:
                raise RuntimeError(
                    "Cannot start a synchronized mutation within an existing active SQLite transaction. "
                    "Synchronized mutations must own the top-level database transaction."
                )

            # 4. PRE-MUTATION READINESS GUARD
            # Before opening the SQLite transaction, inspect index health.
            # Never apply incremental updates to an index marked unavailable.
            if not self.manager._is_ready:
                logger.warning("DSA index unavailable prior to mutation. Attempting recovery rebuild under lock.")
                try:
                    self.manager.rebuild(self.conn)
                except Exception as rebuild_exc:
                    raise IndexUnavailableError(
                        "DSA indices are unavailable and recovery rebuild failed. "
                        "Mutation rejected prior to opening database transaction."
                    ) from rebuild_exc

            # 5. Open immediate SQLite write transaction (BEGIN IMMEDIATE)
            self.tx = transaction(self.conn, immediate=True)
            self.tx.__enter__()
            self._state = CoordinatorState.ACTIVE
            success = True
            return self

        finally:
            if not success:
                # Any failure during the initial entry permanently marks coordinator COMPLETED
                self._state = CoordinatorState.COMPLETED
                # Release lock only if it was actually acquired
                if lock_acquired:
                    self.manager._lock.release()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 1. Exiting an inactive coordinator must be rejected
        if self._state != CoordinatorState.ACTIVE:
            raise RuntimeError("Cannot exit an inactive or already completed MutationCoordinator.")
        self._state = CoordinatorState.COMPLETED

        try:
            if exc_type is not None:
                # 2. Rollback SQLite transaction on application exception
                if self.tx:
                    self.tx.__exit__(exc_type, exc_val, exc_tb)
                return False  # Propagate exception

            # 3. MANDATORY HOOK VALIDATION BEFORE COMMIT
            # If caller executed an index-affecting mutation but failed to register
            # a callable synchronization hook, immediately roll back SQLite and abort!
            if self.post_commit_hook is None or not callable(self.post_commit_hook):
                rollback_exc = RuntimeError(
                    "Synchronized mutation aborted: Missing mandatory post-commit synchronization hook. "
                    "Database transaction was rolled back to prevent memory desynchronization."
                )
                if self.tx:
                    self.tx.__exit__(RuntimeError, rollback_exc, None)
                raise rollback_exc

            # 4. Commit database transaction
            if self.tx:
                self.tx.__exit__(None, None, None)

            # 5. Execute registered in-memory post-commit hook
            try:
                self.post_commit_hook()
            except Exception as sync_exc:
                logger.warning("In-memory update failed post-commit. Triggering recovery rebuild: %s", sync_exc)
                try:
                    self.manager.rebuild(self.conn)
                    # Rebuild succeeded! Memory is consistent with committed DB.
                    return True  # Operation succeeded; do not report false failure to caller
                except Exception as rebuild_exc:
                    self.manager.mark_unavailable()
                    raise IndexDegradedCommittedError(
                        "Database mutation committed successfully, but in-memory index "
                        "is unavailable. Do not retry the operation."
                    ) from rebuild_exc
            return True
        finally:
            # 6. Always release process-wide mutation lock exactly once
            self.manager._lock.release()


class DSAManager:
    """
    Central thread-safe coordinator for in-memory graph and Trie indices.
    Manages process-wide locking, database-to-memory synchronization,
    rebuild snapshots, and defensive query copying.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._graph = UndirectedGraph()
        self._trie = PrefixTrie()
        self._is_ready = False

    def is_ready(self) -> bool:
        """Check if indices are initialized and ready to serve queries."""
        with self._lock:
            return self._is_ready

    def mark_unavailable(self) -> None:
        """Mark indices as unavailable."""
        with self._lock:
            self._is_ready = False

    def initialize(self, conn: sqlite3.Connection) -> None:
        """Initialize in-memory indices from persistent SQLite state."""
        self.rebuild(conn)

    def rebuild(self, conn: sqlite3.Connection) -> None:
        """
        Reconstruct in-memory graph and Trie indices directly from SQLite.
        Enforces strict commit ordering and active transaction rejection:
        1. Acquires process-wide mutation lock.
        2. Rejects an already-active SQLite transaction BEFORE changing _is_ready or reading records.
        3. Sets _is_ready = False.
        4. Populates candidate instances inside an immediate transaction snapshot.
        5. Commits the SQLite transaction.
        6. Atomically swaps internal references.
        7. Sets _is_ready = True only after successful commit and swap.
        """
        with self._lock:
            # Reject an already-active SQLite transaction BEFORE changing _is_ready or reading any records
            if conn.in_transaction:
                raise RuntimeError(
                    "Cannot rebuild DSA indices using a connection with an active transaction. "
                    "Rebuild requires a clean snapshot transaction to prevent reading or committing uncommitted data."
                )

            self._is_ready = False

            # Snapshot transaction: BEGIN IMMEDIATE prevents concurrent writes
            with transaction(conn, immediate=True):
                new_graph = UndirectedGraph()
                new_trie = PrefixTrie()

                # Step A: Load active users
                users = conn.execute("SELECT user_id, username, full_name FROM users;").fetchall()
                for u in users:
                    uid = u["user_id"]
                    new_graph.add_vertex(uid)
                    for key in extract_search_keys(u["username"], u["full_name"]):
                        new_trie.insert(key, uid)

                # Step B: Load accepted connections
                conns = conn.execute("SELECT user_id_low, user_id_high FROM connections;").fetchall()
                for c in conns:
                    new_graph.add_edge(c["user_id_low"], c["user_id_high"])

                # Context exit executes COMMIT on conn.
                # If COMMIT fails, transaction rolls back and swap is never reached.

            # Step C: Atomic pointer swap only after successful commit
            self._graph = new_graph
            self._trie = new_trie
            self._is_ready = True

    def synchronized_mutation(self, conn: sqlite3.Connection) -> MutationCoordinator:
        """
        Return a MutationCoordinator context manager governing an atomic
        database write transaction and post-commit in-memory hook.
        """
        return MutationCoordinator(self, conn)

    # -------------------------------------------------------------------------
    # Internal Controlled Mutation Application Methods (Called only via coordinator)
    # -------------------------------------------------------------------------

    def _apply_connection_accepted(self, user_a: str, user_b: str) -> None:
        self._graph.add_edge(user_a, user_b)

    def _apply_connection_removed(self, user_a: str, user_b: str) -> None:
        self._graph.remove_edge(user_a, user_b)

    def _apply_user_registered(self, user_id: str, username: str, full_name: str) -> None:
        self._graph.add_vertex(user_id)
        for key in extract_search_keys(username, full_name):
            self._trie.insert(key, user_id)

    def _apply_user_updated(
        self,
        user_id: str,
        old_username: str,
        old_full_name: str,
        new_username: str,
        new_full_name: str
    ) -> None:
        old_keys = extract_search_keys(old_username, old_full_name)
        new_keys = extract_search_keys(new_username, new_full_name)
        for k in (old_keys - new_keys):
            self._trie.remove(k, user_id)
        for k in (new_keys - old_keys):
            self._trie.insert(k, user_id)

    def _apply_user_deleted(self, user_id: str, username: str, full_name: str) -> None:
        self._graph.remove_vertex(user_id)
        for k in extract_search_keys(username, full_name):
            self._trie.remove(k, user_id)

    # -------------------------------------------------------------------------
    # Thread-Safe Query Methods (Protected by _lock, defensive copies)
    # -------------------------------------------------------------------------

    def get_shortest_path(self, source: str, target: str) -> Tuple[Optional[List[str]], int]:
        """
        Return the unweighted shortest path and distance between source and target.
        Acquires _lock and returns a defensive copy.
        """
        with self._lock:
            if not self._is_ready:
                raise IndexUnavailableError("DSA indices are currently unavailable.")
            path, distance = bfs_shortest_path(self._graph, source, target)
            return (list(path) if path is not None else None, distance)

    def get_degree(self, user_id: str) -> int:
        """
        Return immediate degree (connection count) of user_id in O(1) time.
        Acquires _lock.
        """
        with self._lock:
            if not self._is_ready:
                raise IndexUnavailableError("DSA indices are currently unavailable.")
            return self._graph.degree(user_id)

    def get_mutual_connections(self, u: str, v: str) -> List[str]:
        """
        Return deterministically sorted list of common connections between u and v.
        Acquires _lock and returns a defensive copy.
        """
        with self._lock:
            if not self._is_ready:
                raise IndexUnavailableError("DSA indices are currently unavailable.")
            return list(self._graph.mutual_connections(u, v))

    def search_prefix(self, prefix: str, limit: int = 10) -> List[str]:
        """
        Search for user_ids matching the given prefix up to limit.
        Acquires _lock and returns a defensive copy.
        """
        with self._lock:
            if not self._is_ready:
                raise IndexUnavailableError("DSA indices are currently unavailable.")
            return list(self._trie.search_prefix(prefix, limit))

    def get_neighbors(self, user_id: str) -> List[str]:
        """
        Return a deterministically sorted defensive copy of immediate neighbor user_ids.
        Acquires _lock.
        """
        with self._lock:
            if not self._is_ready:
                raise IndexUnavailableError("DSA indices are currently unavailable.")
            return sorted(self._graph.get_neighbors(user_id))

    def get_all_vertices(self) -> List[str]:
        """
        Return a deterministically sorted defensive copy of all vertices currently in the graph.
        Acquires _lock.
        """
        with self._lock:
            if not self._is_ready:
                raise IndexUnavailableError("DSA indices are currently unavailable.")
            return sorted(self._graph.all_vertices())


# Global process-level singleton instance
_dsa_manager_instance: Optional[DSAManager] = None
_dsa_manager_init_lock = threading.Lock()


def get_dsa_manager() -> DSAManager:
    """Retrieve or create the process-level singleton DSAManager instance."""
    global _dsa_manager_instance
    if _dsa_manager_instance is None:
        with _dsa_manager_init_lock:
            if _dsa_manager_instance is None:
                _dsa_manager_instance = DSAManager()
    return _dsa_manager_instance
