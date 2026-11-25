"""
Custom Multi-Tenant Prefix Search Trie for Student Lookup.
Governing Baseline: CC-PLN-DSA-002 v2.4, architecture.md v1.1.
"""

from typing import List, Optional, Set
from app.utils.helpers import normalize_key


class TrieNode:
    """A single node within the PrefixTrie."""

    __slots__ = ("children", "user_ids", "is_terminal")

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.user_ids: set[str] = set()
        self.is_terminal: bool = False


def extract_search_keys(username: str, full_name: str) -> Set[str]:
    """
    Extract all normalized searchable keys for a student:
    1. Normalized username.
    2. Normalized full display name.
    3. Individual normalized token words from full display name.
    """
    keys: set[str] = set()

    if username:
        norm_user = normalize_key(username)
        if norm_user:
            keys.add(norm_user)

    if full_name:
        norm_full = normalize_key(full_name)
        if norm_full:
            keys.add(norm_full)
        for token in full_name.split():
            norm_token = normalize_key(token)
            if norm_token:
                keys.add(norm_token)

    return keys


class PrefixTrie:
    """
    Custom in-memory Trie supporting case-insensitive, Unicode-normalized prefix search.
    Supports multi-tenant terminal nodes where multiple students share the same display name.
    """

    def __init__(self) -> None:
        self._root = TrieNode()

    def insert(self, key: str, user_id: str) -> None:
        """
        Insert a searchable key associated with a user_id.
        Automatically normalizes the key prior to insertion.
        """
        if not key or not user_id:
            return

        norm_key = normalize_key(key)
        if not norm_key:
            return

        curr = self._root
        for char in norm_key:
            if char not in curr.children:
                curr.children[char] = TrieNode()
            curr = curr.children[char]

        curr.is_terminal = True
        curr.user_ids.add(user_id)

    def remove(self, key: str, user_id: str) -> bool:
        """
        Remove user_id from a key's terminal node and prune empty branches.
        Returns True if user_id was found and removed, False otherwise.
        """
        if not key or not user_id:
            return False

        norm_key = normalize_key(key)
        if not norm_key:
            return False

        # Traverse and record path for upward branch pruning
        curr = self._root
        path: list[tuple[str, TrieNode, TrieNode]] = []

        for char in norm_key:
            if char not in curr.children:
                return False
            parent = curr
            curr = curr.children[char]
            path.append((char, parent, curr))

        if user_id not in curr.user_ids:
            return False

        curr.user_ids.discard(user_id)
        if not curr.user_ids:
            curr.is_terminal = False

        # Upward branch pruning: remove childless non-terminal nodes
        for char, parent, child in reversed(path):
            if not child.is_terminal and not child.children:
                del parent.children[char]
            else:
                break

        return True

    def search_prefix(self, prefix: str, limit: int = 10) -> List[str]:
        """
        Find user_ids matching the given prefix up to limit.
        Traverses children in deterministic alphabetical order.
        Guarantees that each user_id appears at most once in the returned list.
        """
        if not prefix or limit <= 0:
            return []

        norm_prefix = normalize_key(prefix)
        if not norm_prefix:
            return []

        # Step 1: Navigate to prefix root node
        curr = self._root
        for char in norm_prefix:
            if char not in curr.children:
                return []
            curr = curr.children[char]

        # Step 2: Traverse subtree collecting user_ids deterministically
        results: list[str] = []
        seen: set[str] = set()

        def _collect(node: TrieNode) -> bool:
            # If node is terminal, yield its user_ids in deterministic sorted order
            if node.is_terminal:
                for uid in sorted(node.user_ids):
                    if uid not in seen:
                        seen.add(uid)
                        results.append(uid)
                        if len(results) >= limit:
                            return True  # Halt traversal immediately

            # Recurse through children in sorted alphabetical order
            for char in sorted(node.children.keys()):
                if _collect(node.children[char]):
                    return True
            return False

        _collect(curr)
        return results

    def clear(self) -> None:
        """Reset the Trie to empty state."""
        self._root = TrieNode()
