"""
Unit tests for PrefixTrie, normalization, multi-tenant terminals, and pruning.
"""

from app.dsa.trie import PrefixTrie, extract_search_keys


def test_trie_insert_and_search():
    trie = PrefixTrie()
    trie.insert("sanjanas", "u1")
    trie.insert("sanjana sharma", "u1")
    trie.insert("sanjay", "u2")
    trie.insert("bob", "u3")

    results = trie.search_prefix("san")
    assert "u1" in results
    assert "u2" in results
    assert "u3" not in results


def test_trie_case_and_unicode_normalization():
    trie = PrefixTrie()
    keys = extract_search_keys("alice_u", "Alice Smith")
    for k in keys:
        trie.insert(k, "u1")

    # Search with different casings and tokens
    assert trie.search_prefix("alice") == ["u1"]
    assert trie.search_prefix("ALICE") == ["u1"]
    assert trie.search_prefix("aLiCe") == ["u1"]
    assert trie.search_prefix("smi") == ["u1"]


def test_trie_multi_tenant_terminals():
    """Verify multiple users with identical display names are indexed on the same node."""
    trie = PrefixTrie()
    trie.insert("alex smith", "u1")
    trie.insert("alex smith", "u2")

    results = trie.search_prefix("alex")
    assert sorted(results) == ["u1", "u2"]


def test_trie_duplicate_token_deduplication():
    """Verify users with repeated name tokens (e.g., 'John John') are not duplicated in results."""
    trie = PrefixTrie()
    keys = extract_search_keys("johnny", "John John")
    for k in keys:
        trie.insert(k, "u_john")

    results = trie.search_prefix("jo")
    assert results == ["u_john"]


def test_trie_search_limit_and_deterministic_order():
    trie = PrefixTrie()
    # Insert users a1 through a5 under prefix "test"
    trie.insert("test_alpha", "u1")
    trie.insert("test_bravo", "u2")
    trie.insert("test_charlie", "u3")
    trie.insert("test_delta", "u4")
    trie.insert("test_echo", "u5")

    results_limit_3 = trie.search_prefix("test", limit=3)
    assert len(results_limit_3) == 3
    # Lexicographical deterministic traversal
    assert results_limit_3 == ["u1", "u2", "u3"]


def test_trie_profile_update_removes_old_keys():
    trie = PrefixTrie()
    old_keys = extract_search_keys("old_alice", "Alice Old")
    for k in old_keys:
        trie.insert(k, "u1")

    assert trie.search_prefix("old_al") == ["u1"]
    assert trie.search_prefix("new_al") == []

    # Update profile to new_alice
    new_keys = extract_search_keys("new_alice", "Alice New")
    for k in (old_keys - new_keys):
        trie.remove(k, "u1")
    for k in (new_keys - old_keys):
        trie.insert(k, "u1")

    # Old keys purged, new keys active
    assert trie.search_prefix("old_al") == []
    assert trie.search_prefix("new_al") == ["u1"]
    assert trie.search_prefix("ali") == ["u1"]  # "Alice" token remains


def test_trie_deletion_and_branch_pruning():
    trie = PrefixTrie()
    trie.insert("unique_word", "u1")
    assert trie.search_prefix("unique") == ["u1"]

    # Delete u1
    assert trie.remove("unique_word", "u1") is True
    assert trie.search_prefix("unique") == []

    # Internal tree must be pruned back to root
    assert len(trie._root.children) == 0


def test_trie_empty_and_missing_prefix():
    trie = PrefixTrie()
    trie.insert("campus", "u1")

    assert trie.search_prefix("") == []
    assert trie.search_prefix("   ") == []
    assert trie.search_prefix("missing") == []
