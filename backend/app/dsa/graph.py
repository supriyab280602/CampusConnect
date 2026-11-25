"""
Undirected Adjacency-List Graph for CampusConnect.
Governing Baseline: CC-PLN-DSA-002 v2.4, architecture.md v1.1.
"""

from typing import Optional, Set, List


class UndirectedGraph:
    """
    Custom in-memory undirected adjacency-list graph representing accepted student connections.
    Encapsulates internal adjacency sets and returns defensive copies to protect invariants.
    """

    def __init__(self) -> None:
        self._adj: dict[str, set[str]] = {}

    def add_vertex(self, user_id: str) -> bool:
        """Add a vertex to the graph. Returns True if added, False if already present."""
        if not user_id:
            raise ValueError("user_id cannot be empty.")
        if user_id not in self._adj:
            self._adj[user_id] = set()
            return True
        return False

    def remove_vertex(self, user_id: str) -> bool:
        """
        Remove a vertex and all its incident edges from the graph.
        Returns True if removed, False if vertex did not exist.
        """
        if user_id not in self._adj:
            return False
        # Remove user_id from all neighbors' adjacency sets
        for neighbor in list(self._adj[user_id]):
            if neighbor in self._adj:
                self._adj[neighbor].discard(user_id)
        del self._adj[user_id]
        return True

    def add_edge(self, u: str, v: str) -> bool:
        """
        Add an undirected edge between u and v.
        Enforces symmetry (u <-> v) and prohibits self-connections (u != v).
        Returns True if edge was added, False if it was already present.
        """
        if not u or not v:
            raise ValueError("Both vertex identifiers must be non-empty.")
        if u == v:
            raise ValueError("Self-connections are prohibited; vertices must be distinct.")

        # Ensure both vertices exist in adjacency map
        if u not in self._adj:
            self._adj[u] = set()
        if v not in self._adj:
            self._adj[v] = set()

        if v in self._adj[u]:
            return False  # Already connected

        self._adj[u].add(v)
        self._adj[v].add(u)
        return True

    def remove_edge(self, u: str, v: str) -> bool:
        """
        Remove the undirected edge between u and v.
        Returns True if edge was removed, False if vertices or edge did not exist.
        """
        if u not in self._adj or v not in self._adj:
            return False
        if v not in self._adj[u]:
            return False

        self._adj[u].discard(v)
        self._adj[v].discard(u)
        return True

    def has_vertex(self, user_id: str) -> bool:
        """Check if a vertex exists in the graph."""
        return user_id in self._adj

    def has_edge(self, u: str, v: str) -> bool:
        """Check if an undirected edge exists between u and v."""
        return u in self._adj and v in self._adj[u]

    def get_neighbors(self, user_id: str) -> Set[str]:
        """
        Return a defensive copy of a user's neighbor set.
        Callers cannot mutate internal graph state through the returned set.
        """
        if user_id not in self._adj:
            return set()
        return set(self._adj[user_id])

    def all_vertices(self) -> Set[str]:
        """Return a defensive copy of all vertices currently in the graph."""
        return set(self._adj.keys())

    def degree(self, user_id: str) -> int:
        """
        Return the immediate degree (neighbor count) of a user in O(1) time.
        Calculates directly from internal set length without intermediate object copying.
        """
        neighbors = self._adj.get(user_id)
        if neighbors is None:
            raise KeyError(f"User '{user_id}' does not exist in graph.")
        return len(neighbors)

    def mutual_connections(self, u: str, v: str) -> List[str]:
        """
        Return a deterministically sorted list of common neighbors between u and v.
        Calculated via set intersection in O(min(|Adj(u)|, |Adj(v)|)) time.
        """
        if u not in self._adj or v not in self._adj:
            return []
        if u == v:
            return []
        common = self._adj[u] & self._adj[v]
        return sorted(common)

    def vertex_count(self) -> int:
        """Return total number of vertices."""
        return len(self._adj)

    def edge_count(self) -> int:
        """Return total number of undirected edges."""
        total = sum(len(neighbors) for neighbors in self._adj.values())
        return total // 2

    def clear(self) -> None:
        """Reset the graph to empty state."""
        self._adj.clear()
