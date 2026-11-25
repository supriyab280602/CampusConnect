"""
CampusConnect DSA Layer.
Exports core in-memory data structures, traversal algorithms, and coordinator.
"""

from app.dsa.exceptions import (
    DSABaseException,
    IndexUnavailableError,
    IndexDegradedCommittedError,
)
from app.dsa.graph import UndirectedGraph
from app.dsa.bfs import bfs_shortest_path
from app.dsa.trie import PrefixTrie, TrieNode, extract_search_keys
from app.dsa.heap import PostHeapEntry, HeapStreamMerger
from app.dsa.manager import (
    CoordinatorState,
    DSAManager,
    MutationCoordinator,
    get_dsa_manager,
)

__all__ = [
    "DSABaseException",
    "IndexUnavailableError",
    "IndexDegradedCommittedError",
    "UndirectedGraph",
    "bfs_shortest_path",
    "PrefixTrie",
    "TrieNode",
    "extract_search_keys",
    "PostHeapEntry",
    "HeapStreamMerger",
    "CoordinatorState",
    "DSAManager",
    "MutationCoordinator",
    "get_dsa_manager",
]
