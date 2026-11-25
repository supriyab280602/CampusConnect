"""
Breadth-First Search (BFS) Traversal and Shortest Path.
Governing Baseline: CC-PLN-DSA-002 v2.4, architecture.md v1.1.
"""

from collections import deque
from typing import Optional, List, Tuple
from app.dsa.graph import UndirectedGraph


def bfs_shortest_path(
    graph: UndirectedGraph,
    source: str,
    target: str
) -> Tuple[Optional[List[str]], int]:
    """
    Compute the unweighted shortest path and distance (in edge count) between
    source and target using Breadth-First Search.

    Returns:
    - (path, distance): where path is a list of user_ids from source to target,
      and distance is the integer number of edges (len(path) - 1).
    - (None, -1): if no path exists, or if either vertex is not present in the graph.

    Complexity:
    - Time: O(V + E)
    - Space: O(V)
    """
    if not source or not target:
        return (None, -1)

    # Both vertices must exist in the graph
    if not graph.has_vertex(source) or not graph.has_vertex(target):
        return (None, -1)

    # Edge case: Source is Target
    if source == target:
        return ([source], 0)

    # Queue stores vertices to visit in FIFO order
    queue = deque([source])
    # Parent map records discovery and predecessor for path reconstruction
    parent: dict[str, Optional[str]] = {source: None}

    while queue:
        current = queue.popleft()

        if current == target:
            break

        # Deterministic traversal over sorted neighbor IDs
        neighbors = sorted(graph._adj.get(current, set()))
        for neighbor in neighbors:
            if neighbor not in parent:
                parent[neighbor] = current
                queue.append(neighbor)

    # Target was not reached (disconnected components)
    if target not in parent:
        return (None, -1)

    # Reconstruct path backwards from target to source
    path = []
    curr: Optional[str] = target
    while curr is not None:
        path.append(curr)
        curr = parent[curr]

    path.reverse()
    distance = len(path) - 1
    return (path, distance)
